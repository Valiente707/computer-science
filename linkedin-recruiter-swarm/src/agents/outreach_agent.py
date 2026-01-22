"""
Outreach Agent - Generates and sends personalized messages
"""

from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent


class OutreachAgent(BaseAgent):
    """
    Specialized agent for generating and managing candidate outreach.
    Handles message personalization, contact constraints, and tracking.
    """

    def __init__(self, agent_id: str, linkedin_interface, config: Dict = None):
        """
        Initialize Outreach Agent

        Args:
            agent_id: Unique agent identifier
            linkedin_interface: LinkedInHunterInterface instance
            config: Configuration dictionary
        """
        super().__init__(agent_id, config)
        self.linkedin = linkedin_interface
        self.outreach_strategies = {
            'personalized': self._personalized_outreach,
            'bulk': self._bulk_outreach,
            'inmail': self._inmail_outreach,
            'connection_request': self._connection_request
        }
        self.daily_limit = config.get('daily_outreach_limit', 50)
        self.messages_sent_today = 0

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process outreach task

        Args:
            task: Task with candidates and outreach parameters

        Returns:
            Dictionary with outreach results
        """
        task_type = task.get('type', 'outreach')
        candidates = task.get('candidates', [])
        requisition_id = task.get('requisition_id')
        strategy = task.get('strategy', 'personalized')

        if task_type == 'outreach':
            return self._execute_outreach(candidates, requisition_id, strategy)
        elif task_type == 'generate_message':
            return self._generate_messages_only(candidates, requisition_id)
        elif task_type == 'schedule_outreach':
            return self._schedule_outreach(candidates, requisition_id, task.get('schedule'))
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _execute_outreach(self, candidates: List[Dict], requisition_id: str, strategy: str) -> Dict[str, Any]:
        """
        Execute outreach to candidates

        Args:
            candidates: List of candidates to contact
            requisition_id: Requisition ID
            strategy: Outreach strategy to use

        Returns:
            Outreach results
        """
        self.logger.info(f"Executing {strategy} outreach to {len(candidates)} candidates")

        req_profile = self.linkedin.get_requisition_profile(requisition_id)
        outreach_func = self.outreach_strategies.get(strategy, self._personalized_outreach)

        results = {
            'requisition_id': requisition_id,
            'strategy': strategy,
            'total_candidates': len(candidates),
            'messages_generated': 0,
            'messages_sent': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }

        for candidate in candidates:
            # Check daily limit
            if self.messages_sent_today >= self.daily_limit:
                self.logger.warning("Daily outreach limit reached")
                results['skipped'] += 1
                results['details'].append({
                    'candidate_id': candidate.get('candidate_id'),
                    'status': 'skipped',
                    'reason': 'daily_limit_reached'
                })
                continue

            # Check contact constraints
            candidate_id = candidate.get('candidate_id')
            if candidate_id:
                contact_check = self.linkedin.respect_contact_constraints(candidate_id)
                if not contact_check['allowed']:
                    self.logger.info(f"Skipping candidate {candidate_id}: {contact_check['reason']}")
                    results['skipped'] += 1
                    results['details'].append({
                        'candidate_id': candidate_id,
                        'status': 'skipped',
                        'reason': contact_check['reason']
                    })
                    continue

            # Generate and send message
            try:
                outreach_result = outreach_func(candidate, req_profile)
                results['messages_generated'] += 1

                if outreach_result['sent']:
                    results['messages_sent'] += 1
                    self.messages_sent_today += 1

                results['details'].append(outreach_result)

            except Exception as e:
                self.logger.error(f"Outreach failed for candidate: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'candidate_id': candidate.get('candidate_id'),
                    'status': 'failed',
                    'error': str(e)
                })

        return results

    def _personalized_outreach(self, candidate: Dict, req_profile: Dict) -> Dict:
        """
        Generate and send highly personalized outreach

        Args:
            candidate: Candidate information
            req_profile: Requisition profile

        Returns:
            Outreach result
        """
        # Extract candidate details
        profile = candidate.get('profile', candidate)
        score_details = candidate.get('score_breakdown', {})

        # Build personalization context
        personalization_context = self._build_personalization_context(profile, score_details)

        # Generate message using LinkedIn interface
        message = self.linkedin.generate_outreach_message(profile, req_profile)

        # Enhance with personalization
        enhanced_message = self._enhance_message(
            message,
            personalization_context,
            personalization_level='high'
        )

        # Add tracking
        enhanced_message['tracking'] = {
            'candidate_id': profile.get('candidate_id'),
            'requisition_id': req_profile.get('requisition_id'),
            'strategy': 'personalized',
            'sent_at': datetime.now(),
            'agent_id': self.agent_id
        }

        # Send message (simulated)
        sent = self._send_message(enhanced_message, profile)

        return {
            'candidate_id': profile.get('candidate_id'),
            'status': 'sent' if sent else 'failed',
            'message': enhanced_message,
            'personalization_score': personalization_context.get('score', 0),
            'sent': sent
        }

    def _build_personalization_context(self, profile: Dict, score_details: Dict) -> Dict:
        """
        Build context for message personalization

        Args:
            profile: Candidate profile
            score_details: Scoring details

        Returns:
            Personalization context
        """
        context = {
            'score': 0.0,
            'hooks': []
        }

        # Find strong matches to highlight
        components = score_details.get('components', {})

        if components.get('skill_match', 0) > 0.7:
            top_skills = profile.get('skills', [])[:3]
            context['hooks'].append({
                'type': 'skill_match',
                'data': top_skills,
                'message': f"Your expertise in {', '.join(top_skills)} particularly caught our attention"
            })
            context['score'] += 0.3

        if components.get('experience_match', 0) > 0.8:
            current_title = profile.get('current_title', '')
            context['hooks'].append({
                'type': 'experience',
                'data': current_title,
                'message': f"Your experience as {current_title} aligns perfectly with what we're looking for"
            })
            context['score'] += 0.3

        # Check for mutual connections (placeholder)
        mutual_connections = profile.get('mutual_connections', [])
        if mutual_connections:
            context['hooks'].append({
                'type': 'mutual_connection',
                'data': mutual_connections[0],
                'message': f"I noticed we both know {mutual_connections[0]}"
            })
            context['score'] += 0.2

        # Check for shared experiences
        if self._has_shared_experience(profile):
            context['hooks'].append({
                'type': 'shared_experience',
                'message': "I see you've worked in similar environments"
            })
            context['score'] += 0.2

        return context

    def _has_shared_experience(self, profile: Dict) -> bool:
        """Check for shared experiences with company"""
        # Placeholder - would check company history, schools, etc.
        return False

    def _enhance_message(self, base_message: Dict, context: Dict, personalization_level: str) -> Dict:
        """
        Enhance message with personalization

        Args:
            base_message: Base message from template
            context: Personalization context
            personalization_level: Level of personalization (low, medium, high)

        Returns:
            Enhanced message
        """
        enhanced = base_message.copy()

        if personalization_level == 'high' and context['hooks']:
            # Insert personalization hooks
            hooks_text = "\n\n".join([hook['message'] for hook in context['hooks'][:2]])

            # Insert after greeting
            body = enhanced.get('body', '')
            enhanced['body'] = body.replace(
                '\n\n',
                f"\n\n{hooks_text}\n\n",
                1  # Only first occurrence
            )

            enhanced['personalization_level'] = 'high'
            enhanced['personalization_score'] = context['score']
        else:
            enhanced['personalization_level'] = 'standard'
            enhanced['personalization_score'] = 0.3

        return enhanced

    def _send_message(self, message: Dict, profile: Dict) -> bool:
        """
        Send message to candidate (simulated)

        Args:
            message: Message to send
            profile: Candidate profile

        Returns:
            True if sent successfully
        """
        # In production, this would actually send via LinkedIn API
        self.logger.info(f"Sending message to {profile.get('first_name', 'candidate')}")

        # Simulate success
        # In reality would handle API calls, rate limits, etc.
        return True

    def _bulk_outreach(self, candidate: Dict, req_profile: Dict) -> Dict:
        """Bulk outreach with less personalization"""
        profile = candidate.get('profile', candidate)

        # Use template with minimal personalization
        message = self.linkedin.generate_outreach_message(profile, req_profile)
        message['personalization_level'] = 'low'

        sent = self._send_message(message, profile)

        return {
            'candidate_id': profile.get('candidate_id'),
            'status': 'sent' if sent else 'failed',
            'message': message,
            'personalization_score': 0.2,
            'sent': sent
        }

    def _inmail_outreach(self, candidate: Dict, req_profile: Dict) -> Dict:
        """InMail outreach (premium LinkedIn feature)"""
        profile = candidate.get('profile', candidate)

        # Generate InMail-specific message (subject + body)
        message = self.linkedin.generate_outreach_message(profile, req_profile)
        message['type'] = 'inmail'
        message['credits_used'] = 1  # InMail credits

        sent = self._send_message(message, profile)

        return {
            'candidate_id': profile.get('candidate_id'),
            'status': 'sent' if sent else 'failed',
            'message': message,
            'personalization_score': 0.6,
            'sent': sent,
            'inmail_credits_used': 1
        }

    def _connection_request(self, candidate: Dict, req_profile: Dict) -> Dict:
        """Send connection request with note"""
        profile = candidate.get('profile', candidate)

        # Generate short connection note (300 char limit)
        note = self._generate_connection_note(profile, req_profile)

        message = {
            'type': 'connection_request',
            'note': note,
            'subject': 'Connection Request'
        }

        sent = self._send_message(message, profile)

        return {
            'candidate_id': profile.get('candidate_id'),
            'status': 'sent' if sent else 'failed',
            'message': message,
            'personalization_score': 0.4,
            'sent': sent
        }

    def _generate_connection_note(self, profile: Dict, req_profile: Dict) -> str:
        """Generate connection request note"""
        name = profile.get('first_name', 'there')
        job_title = req_profile.get('job_title', 'opportunity')

        note = f"Hi {name}, I'd love to connect and share an exciting {job_title} opportunity with you."

        # Keep under 300 characters
        return note[:300]

    def _generate_messages_only(self, candidates: List[Dict], requisition_id: str) -> Dict[str, Any]:
        """
        Generate messages without sending

        Args:
            candidates: List of candidates
            requisition_id: Requisition ID

        Returns:
            Generated messages
        """
        req_profile = self.linkedin.get_requisition_profile(requisition_id)

        messages = []
        for candidate in candidates:
            profile = candidate.get('profile', candidate)
            message = self.linkedin.generate_outreach_message(profile, req_profile)

            messages.append({
                'candidate_id': profile.get('candidate_id'),
                'message': message,
                'generated_at': datetime.now()
            })

        return {
            'requisition_id': requisition_id,
            'messages_generated': len(messages),
            'messages': messages
        }

    def _schedule_outreach(self, candidates: List[Dict], requisition_id: str,
                          schedule: Dict) -> Dict[str, Any]:
        """
        Schedule outreach for later

        Args:
            candidates: List of candidates
            requisition_id: Requisition ID
            schedule: Schedule configuration

        Returns:
            Scheduling result
        """
        scheduled_time = schedule.get('send_at', datetime.now())
        batch_size = schedule.get('batch_size', 10)
        interval_minutes = schedule.get('interval_minutes', 60)

        self.logger.info(f"Scheduling outreach for {len(candidates)} candidates")

        # Create schedule
        scheduled_batches = []
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i+batch_size]
            batch_time = scheduled_time

            scheduled_batches.append({
                'batch_number': i // batch_size + 1,
                'candidates': batch,
                'scheduled_for': batch_time,
                'status': 'scheduled'
            })

            # Increment time for next batch
            from datetime import timedelta
            scheduled_time = scheduled_time + timedelta(minutes=interval_minutes)

        return {
            'requisition_id': requisition_id,
            'total_candidates': len(candidates),
            'batches_scheduled': len(scheduled_batches),
            'schedule': scheduled_batches
        }

    def reset_daily_limit(self) -> None:
        """Reset daily message counter"""
        self.messages_sent_today = 0
        self.logger.info("Daily outreach limit reset")

    def can_handle(self, task: Dict[str, Any]) -> bool:
        """Check if this agent can handle the task"""
        return task.get('type') in ['outreach', 'generate_message', 'schedule_outreach']
