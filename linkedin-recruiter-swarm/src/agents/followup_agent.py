"""
Follow-up Agent - Manages responses and follow-up communication
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent


class FollowUpAgent(BaseAgent):
    """
    Specialized agent for managing follow-up communications and responses.
    Handles response tracking, follow-up scheduling, and interview coordination.
    """

    def __init__(self, agent_id: str, linkedin_interface, config: Dict = None):
        """
        Initialize Follow-up Agent

        Args:
            agent_id: Unique agent identifier
            linkedin_interface: LinkedInHunterInterface instance
            config: Configuration dictionary
        """
        super().__init__(agent_id, config)
        self.linkedin = linkedin_interface
        self.follow_up_intervals = config.get('follow_up_intervals', {
            'first': 3,   # days
            'second': 7,
            'final': 14
        })
        self.max_follow_ups = config.get('max_follow_ups', 3)

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process follow-up task

        Args:
            task: Task with follow-up parameters

        Returns:
            Dictionary with follow-up results
        """
        task_type = task.get('type', 'follow_up')

        if task_type == 'follow_up':
            return self._execute_follow_up(task.get('candidates', []), task.get('requisition_id'))
        elif task_type == 'process_responses':
            return self._process_responses(task.get('responses', []))
        elif task_type == 'schedule_interviews':
            return self._schedule_interviews(task.get('candidates', []), task.get('requisition_id'))
        elif task_type == 'check_pending':
            return self._check_pending_follow_ups(task.get('requisition_id'))
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _execute_follow_up(self, candidates: List[Dict], requisition_id: str) -> Dict[str, Any]:
        """
        Execute follow-up communications

        Args:
            candidates: List of candidates to follow up with
            requisition_id: Requisition ID

        Returns:
            Follow-up results
        """
        self.logger.info(f"Executing follow-up for {len(candidates)} candidates")

        results = {
            'requisition_id': requisition_id,
            'total_candidates': len(candidates),
            'follow_ups_sent': 0,
            'skipped': 0,
            'max_attempts_reached': 0,
            'details': []
        }

        for candidate in candidates:
            candidate_id = candidate.get('candidate_id')

            # Get outreach history
            outreach_history = self._get_outreach_history(candidate_id)

            # Determine if follow-up is needed
            follow_up_decision = self._should_follow_up(outreach_history)

            if not follow_up_decision['should_follow_up']:
                results['skipped'] += 1
                results['details'].append({
                    'candidate_id': candidate_id,
                    'status': 'skipped',
                    'reason': follow_up_decision['reason']
                })
                continue

            if follow_up_decision.get('max_attempts'):
                results['max_attempts_reached'] += 1
                results['details'].append({
                    'candidate_id': candidate_id,
                    'status': 'max_attempts',
                    'attempts': len(outreach_history)
                })
                continue

            # Generate follow-up message
            try:
                follow_up_msg = self._generate_follow_up_message(
                    candidate,
                    outreach_history,
                    requisition_id
                )

                # Send follow-up
                sent = self._send_follow_up(follow_up_msg, candidate)

                if sent:
                    results['follow_ups_sent'] += 1

                results['details'].append({
                    'candidate_id': candidate_id,
                    'status': 'sent' if sent else 'failed',
                    'follow_up_number': len(outreach_history) + 1,
                    'message': follow_up_msg
                })

            except Exception as e:
                self.logger.error(f"Follow-up failed for candidate {candidate_id}: {str(e)}")
                results['details'].append({
                    'candidate_id': candidate_id,
                    'status': 'failed',
                    'error': str(e)
                })

        return results

    def _get_outreach_history(self, candidate_id: str) -> List[Dict]:
        """
        Get outreach history for candidate

        Args:
            candidate_id: Candidate ID

        Returns:
            List of outreach attempts
        """
        # Placeholder - would query from knowledge graph
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})-[:RECEIVED]->(m:Message)
        RETURN m
        ORDER BY m.sent_at DESC
        """

        # Simulated result
        return []

    def _should_follow_up(self, outreach_history: List[Dict]) -> Dict:
        """
        Determine if follow-up should be sent

        Args:
            outreach_history: Previous outreach attempts

        Returns:
            Decision dictionary
        """
        if not outreach_history:
            return {
                'should_follow_up': False,
                'reason': 'no_initial_outreach'
            }

        # Check max attempts
        if len(outreach_history) >= self.max_follow_ups:
            return {
                'should_follow_up': False,
                'reason': 'max_attempts_reached',
                'max_attempts': True
            }

        # Check last contact time
        last_contact = outreach_history[0].get('sent_at', datetime.now())
        days_since = (datetime.now() - last_contact).days

        # Determine appropriate interval
        attempt_number = len(outreach_history)
        if attempt_number == 1:
            required_interval = self.follow_up_intervals['first']
        elif attempt_number == 2:
            required_interval = self.follow_up_intervals['second']
        else:
            required_interval = self.follow_up_intervals['final']

        if days_since < required_interval:
            return {
                'should_follow_up': False,
                'reason': 'too_soon',
                'days_until_follow_up': required_interval - days_since
            }

        return {
            'should_follow_up': True,
            'reason': 'due_for_follow_up',
            'attempt_number': attempt_number + 1
        }

    def _generate_follow_up_message(self, candidate: Dict, outreach_history: List[Dict],
                                    requisition_id: str) -> Dict:
        """
        Generate follow-up message

        Args:
            candidate: Candidate information
            outreach_history: Previous outreach
            requisition_id: Requisition ID

        Returns:
            Follow-up message
        """
        profile = candidate.get('profile', candidate)
        attempt_number = len(outreach_history) + 1

        # Get requisition details
        req_profile = self.linkedin.get_requisition_profile(requisition_id)

        # Select follow-up template based on attempt number
        template = self._select_follow_up_template(attempt_number)

        # Generate message
        name = profile.get('name', {}).get('first_name', 'there')
        job_title = req_profile.get('job_title', 'opportunity')

        messages = {
            1: f"""Hi {name},

I wanted to follow up on my previous message about the {job_title} opportunity.

I understand you're busy, but I'd love to share more details about this role if you're interested.

Would you have 15 minutes this week for a quick call?

Best regards""",
            2: f"""Hi {name},

Just checking in one more time about the {job_title} role.

If the timing isn't right or you're not interested, no problem at all - just let me know.

Otherwise, I'd be happy to answer any questions you might have.

Thanks""",
            3: f"""Hi {name},

This will be my last follow-up about the {job_title} opportunity.

If you'd like to learn more, feel free to reach out anytime. Otherwise, I'll assume you're not interested at this time.

Best of luck with your current role!

Best regards"""
        }

        message_body = messages.get(attempt_number, messages[3])

        return {
            'type': 'follow_up',
            'attempt_number': attempt_number,
            'subject': f"Following up: {job_title} opportunity",
            'body': message_body,
            'candidate_id': profile.get('candidate_id'),
            'requisition_id': requisition_id,
            'template_id': template.get('id'),
            'generated_at': datetime.now()
        }

    def _select_follow_up_template(self, attempt_number: int) -> Dict:
        """Select appropriate follow-up template"""
        templates = {
            1: {'id': 'follow_up_1', 'tone': 'friendly_reminder'},
            2: {'id': 'follow_up_2', 'tone': 'casual_check_in'},
            3: {'id': 'follow_up_3', 'tone': 'final_notice'}
        }
        return templates.get(attempt_number, templates[3])

    def _send_follow_up(self, message: Dict, candidate: Dict) -> bool:
        """
        Send follow-up message

        Args:
            message: Message to send
            candidate: Candidate information

        Returns:
            True if sent successfully
        """
        # Simulated send
        self.logger.info(f"Sending follow-up #{message['attempt_number']} to candidate")
        return True

    def _process_responses(self, responses: List[Dict]) -> Dict[str, Any]:
        """
        Process candidate responses

        Args:
            responses: List of responses to process

        Returns:
            Processing results
        """
        self.logger.info(f"Processing {len(responses)} responses")

        results = {
            'total_responses': len(responses),
            'interested': 0,
            'not_interested': 0,
            'needs_clarification': 0,
            'processed': []
        }

        for response in responses:
            # Analyze response sentiment
            analysis = self._analyze_response(response)

            # Categorize response
            category = analysis['category']
            if category == 'interested':
                results['interested'] += 1
                # Schedule next step
                next_step = self._determine_next_step(response, 'interested')
            elif category == 'not_interested':
                results['not_interested'] += 1
                next_step = {'action': 'mark_inactive', 'reason': analysis.get('reason')}
            else:
                results['needs_clarification'] += 1
                next_step = {'action': 'send_clarification'}

            results['processed'].append({
                'candidate_id': response.get('candidate_id'),
                'category': category,
                'sentiment_score': analysis.get('sentiment_score'),
                'next_step': next_step
            })

        return results

    def _analyze_response(self, response: Dict) -> Dict:
        """
        Analyze candidate response sentiment

        Args:
            response: Response data

        Returns:
            Analysis results
        """
        message_text = response.get('message', '').lower()

        # Simple keyword-based analysis (would use NLP in production)
        interested_keywords = ['interested', 'yes', 'tell me more', 'schedule', 'call', 'meeting']
        not_interested_keywords = ['not interested', 'no thanks', 'pass', 'not looking']

        interested_count = sum(1 for keyword in interested_keywords if keyword in message_text)
        not_interested_count = sum(1 for keyword in not_interested_keywords if keyword in message_text)

        if interested_count > not_interested_count:
            return {
                'category': 'interested',
                'sentiment_score': 0.8,
                'confidence': 0.7
            }
        elif not_interested_count > interested_count:
            return {
                'category': 'not_interested',
                'sentiment_score': 0.2,
                'confidence': 0.7,
                'reason': 'explicit_decline'
            }
        else:
            return {
                'category': 'needs_clarification',
                'sentiment_score': 0.5,
                'confidence': 0.4
            }

    def _determine_next_step(self, response: Dict, category: str) -> Dict:
        """
        Determine next step based on response

        Args:
            response: Response data
            category: Response category

        Returns:
            Next step action
        """
        if category == 'interested':
            return {
                'action': 'schedule_interview',
                'priority': 'high',
                'suggested_times': self._suggest_interview_times()
            }
        elif category == 'not_interested':
            return {
                'action': 'mark_inactive',
                'reason': 'candidate_declined'
            }
        else:
            return {
                'action': 'request_clarification',
                'questions': self._generate_clarification_questions(response)
            }

    def _suggest_interview_times(self) -> List[datetime]:
        """Suggest interview time slots"""
        # Generate next 5 business days, 2 slots per day
        suggested_times = []
        current = datetime.now()

        slots_per_day = 2
        days_ahead = 5

        for day in range(1, days_ahead + 1):
            date = current + timedelta(days=day)

            # Skip weekends
            if date.weekday() >= 5:
                continue

            # Morning slot (10 AM)
            morning = date.replace(hour=10, minute=0, second=0, microsecond=0)
            suggested_times.append(morning)

            # Afternoon slot (2 PM)
            afternoon = date.replace(hour=14, minute=0, second=0, microsecond=0)
            suggested_times.append(afternoon)

        return suggested_times[:10]  # Return 10 slots

    def _generate_clarification_questions(self, response: Dict) -> List[str]:
        """Generate clarification questions"""
        return [
            "Are you currently open to new opportunities?",
            "What aspects of the role are you most interested in?",
            "When would be a good time to discuss further?"
        ]

    def _schedule_interviews(self, candidates: List[Dict], requisition_id: str) -> Dict[str, Any]:
        """
        Schedule interviews for interested candidates

        Args:
            candidates: List of candidates
            requisition_id: Requisition ID

        Returns:
            Scheduling results
        """
        self.logger.info(f"Scheduling interviews for {len(candidates)} candidates")

        results = {
            'requisition_id': requisition_id,
            'total_candidates': len(candidates),
            'interviews_scheduled': 0,
            'scheduling_failed': 0,
            'scheduled_interviews': []
        }

        available_slots = self._suggest_interview_times()

        for idx, candidate in enumerate(candidates):
            if idx >= len(available_slots):
                self.logger.warning("No more available interview slots")
                results['scheduling_failed'] += 1
                continue

            try:
                interview = {
                    'candidate_id': candidate.get('candidate_id'),
                    'requisition_id': requisition_id,
                    'scheduled_time': available_slots[idx],
                    'duration_minutes': 30,
                    'type': 'phone_screen',
                    'interviewer': 'TBD',
                    'status': 'scheduled'
                }

                results['interviews_scheduled'] += 1
                results['scheduled_interviews'].append(interview)

            except Exception as e:
                self.logger.error(f"Failed to schedule interview: {str(e)}")
                results['scheduling_failed'] += 1

        return results

    def _check_pending_follow_ups(self, requisition_id: str) -> Dict[str, Any]:
        """
        Check for pending follow-ups that need to be sent

        Args:
            requisition_id: Requisition ID

        Returns:
            Pending follow-ups
        """
        # Placeholder - would query knowledge graph for pending follow-ups
        query = """
        MATCH (c:Candidate)-[:APPLIED_TO]->(r:Requisition {requisition_id: $req_id})
        WHERE c.last_contacted < datetime() - duration('P3D')
        AND c.follow_up_count < 3
        RETURN c
        """

        # Simulated result
        pending = []

        return {
            'requisition_id': requisition_id,
            'pending_count': len(pending),
            'candidates': pending
        }

    def can_handle(self, task: Dict[str, Any]) -> bool:
        """Check if this agent can handle the task"""
        return task.get('type') in ['follow_up', 'process_responses', 'schedule_interviews', 'check_pending']
