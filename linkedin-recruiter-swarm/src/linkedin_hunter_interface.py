"""
LinkedIn Hunter Interface - Base data interface for LinkedIn sourcing
"""

import uuid
from datetime import datetime, time
from typing import Dict, List, Optional, Any


class LinkedInHunterInterface:
    """
    Data interface for LinkedIn sourcing agent
    """

    def __init__(self, knowledge_graph, semantic_layer, linkedin_api):
        self.kg = knowledge_graph
        self.semantic = semantic_layer
        self.linkedin = linkedin_api
        self.messaging_templates = self.load_templates()

    def load_templates(self) -> Dict[str, Any]:
        """Load messaging templates for outreach"""
        # Placeholder - would load from database or config
        return {
            'initial_outreach': {
                'id': 'template_001',
                'name': 'Initial Outreach',
                'tone': 'professional_friendly'
            },
            'follow_up': {
                'id': 'template_002',
                'name': 'Follow-up',
                'tone': 'casual_professional'
            }
        }

    def find_candidates_for_req(self, requisition_id: str, max_results: int = 50) -> List[Dict]:
        """
        Find potential candidates on LinkedIn
        """
        # Get requisition requirements
        req_profile = self.get_requisition_profile(requisition_id)

        # Build LinkedIn search query
        search_params = self.build_linkedin_search(req_profile)

        # Execute search
        linkedin_profiles = self.linkedin.search(search_params)

        # Filter and score
        scored_candidates = []
        for profile in linkedin_profiles:
            # Check if already in our system
            existing = self.check_existing_candidate(profile)

            if existing:
                # Update profile with fresh LinkedIn data
                self.update_candidate_profile(existing, profile)
                scored_candidates.append({
                    'candidate_id': existing['candidate_id'],
                    'source': 'existing_database',
                    'profile': existing,
                    'score': self.score_candidate_match(existing, req_profile)
                })
            else:
                # New candidate - score and add
                score_result = self.score_linkedin_profile(profile, req_profile)
                if score_result['total_score'] >= 0.6:  # Threshold
                    scored_candidates.append({
                        'candidate_id': None,
                        'source': 'linkedin_new',
                        'profile': profile,
                        'score': score_result['total_score'],
                        'score_details': score_result
                    })

        # Sort by score
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)

        return scored_candidates[:max_results]

    def get_requisition_profile(self, requisition_id: str) -> Dict:
        """Get requisition details from knowledge graph"""
        query = """
        MATCH (r:Requisition {requisition_id: $req_id})
        RETURN r
        """
        result = self.kg.query(query, {'req_id': requisition_id})
        return result[0]['r'] if result else {}

    def build_linkedin_search(self, req_profile: Dict) -> Dict:
        """
        Convert req profile to LinkedIn search parameters
        """
        search_params = {
            'keywords': self.build_keyword_list(req_profile),
            'title': req_profile.get('job_title', ''),
            'location': req_profile.get('location', ''),
            'current_company_exclude': self.get_competitor_blacklist(),
            'years_experience': {
                'min': req_profile.get('min_years_experience', 0),
                'max': req_profile.get('max_years_experience') if req_profile.get('max_years_experience') else None
            }
        }

        # Add skills to search
        required_skills = [s['skill'] for s in req_profile.get('required_skills', [])]
        search_params['skills'] = required_skills[:5]  # LinkedIn limits skill filters

        # Add education if required
        if req_profile.get('education_requirements'):
            search_params['education_level'] = req_profile['education_requirements']['minimum_degree']

        return search_params

    def build_keyword_list(self, req_profile: Dict) -> List[str]:
        """Build keyword list from requisition"""
        keywords = []
        if 'job_title' in req_profile:
            keywords.append(req_profile['job_title'])
        if 'department' in req_profile:
            keywords.append(req_profile['department'])
        return keywords

    def get_competitor_blacklist(self) -> List[str]:
        """Get list of competitor companies to exclude"""
        # Placeholder - would query from knowledge graph
        return []

    def score_linkedin_profile(self, linkedin_profile: Dict, req_profile: Dict) -> Dict:
        """
        Score how well LinkedIn profile matches requirements
        """
        score_components = {}

        # Skill match (40% weight)
        profile_skills = set(linkedin_profile.get('skills', []))
        required_skills = set(s['skill'] for s in req_profile.get('required_skills', []))

        if required_skills:
            skill_overlap = len(profile_skills & required_skills) / len(required_skills)
        else:
            skill_overlap = 0.5  # Default if no required skills
        score_components['skill_match'] = skill_overlap * 0.4

        # Experience match (30% weight)
        profile_years = linkedin_profile.get('years_experience', 0)
        required_years = req_profile.get('min_years_experience', 0)

        if profile_years >= required_years:
            exp_score = min(1.0, profile_years / (required_years * 1.5)) if required_years > 0 else 1.0
        else:
            exp_score = (profile_years / required_years * 0.7) if required_years > 0 else 0.5

        score_components['experience_match'] = exp_score * 0.3

        # Title similarity (15% weight)
        title_sim = self.calculate_title_similarity(
            linkedin_profile.get('current_title', ''),
            req_profile.get('job_title', '')
        )
        score_components['title_match'] = title_sim * 0.15

        # Location match (10% weight)
        location_match = self.check_location_match(
            linkedin_profile.get('location'),
            req_profile.get('location')
        )
        score_components['location_match'] = location_match * 0.10

        # Activity/engagement (5% weight)
        activity_score = self.assess_linkedin_activity(linkedin_profile)
        score_components['activity_score'] = activity_score * 0.05

        total_score = sum(score_components.values())

        return {
            'total_score': total_score,
            'components': score_components,
            'confidence': self.calculate_confidence(score_components)
        }

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between job titles"""
        # Simple word overlap - in production would use semantic similarity
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        total = len(words1 | words2)

        return overlap / total if total > 0 else 0.0

    def check_location_match(self, candidate_location: Optional[str],
                            req_location: Optional[str]) -> float:
        """Check if locations match"""
        if not candidate_location or not req_location:
            return 0.5  # Neutral score if location not specified

        # Simple string matching - in production would use geocoding
        if candidate_location.lower() in req_location.lower() or \
           req_location.lower() in candidate_location.lower():
            return 1.0

        return 0.0

    def assess_linkedin_activity(self, linkedin_profile: Dict) -> float:
        """Assess LinkedIn activity/engagement level"""
        # Placeholder - would analyze posts, connections, endorsements
        activity_indicators = {
            'recent_posts': linkedin_profile.get('recent_posts_count', 0),
            'connections': linkedin_profile.get('connections', 0),
            'endorsements': linkedin_profile.get('endorsements', 0)
        }

        score = 0.0
        if activity_indicators['recent_posts'] > 5:
            score += 0.4
        if activity_indicators['connections'] > 500:
            score += 0.3
        if activity_indicators['endorsements'] > 10:
            score += 0.3

        return min(1.0, score)

    def calculate_confidence(self, score_components: Dict) -> float:
        """Calculate confidence in the scoring"""
        # Higher confidence when we have more data points with good scores
        non_zero_scores = sum(1 for v in score_components.values() if v > 0)
        total_scores = len(score_components)

        return non_zero_scores / total_scores if total_scores > 0 else 0.0

    def check_existing_candidate(self, linkedin_profile: Dict) -> Optional[Dict]:
        """
        Check if LinkedIn profile already exists in our system
        """
        linkedin_url = linkedin_profile.get('public_url', '')
        email = linkedin_profile.get('email')

        query = """
        MATCH (c:Candidate)
        WHERE c.linkedin_url = $linkedin_url
           OR c.email = $email
        RETURN c
        LIMIT 1
        """

        result = self.kg.query(query, {
            'linkedin_url': linkedin_url,
            'email': email
        })

        return result[0]['c'] if result else None

    def update_candidate_profile(self, existing: Dict, linkedin_profile: Dict) -> None:
        """Update existing candidate with fresh LinkedIn data"""
        update_fields = {
            'current_title': linkedin_profile.get('current_title'),
            'current_company': linkedin_profile.get('current_company'),
            'location': linkedin_profile.get('location'),
            'last_updated': datetime.now()
        }

        self.kg.update_candidate(existing['candidate_id'], update_fields)

    def score_candidate_match(self, candidate: Dict, req_profile: Dict) -> float:
        """Score existing candidate against requisition"""
        # Convert candidate to LinkedIn-like format and use standard scoring
        pseudo_profile = {
            'skills': candidate.get('skills', []),
            'years_experience': candidate.get('years_experience', 0),
            'current_title': candidate.get('current_title', ''),
            'location': candidate.get('location', '')
        }

        result = self.score_linkedin_profile(pseudo_profile, req_profile)
        return result['total_score']

    def create_candidate_from_linkedin(self, linkedin_profile: Dict) -> Dict:
        """
        Create new candidate record from LinkedIn data
        """
        candidate = {
            'candidate_id': str(uuid.uuid4()),
            'source': 'linkedin_sourced',
            'name': {
                'first_name': linkedin_profile.get('first_name', ''),
                'last_name': linkedin_profile.get('last_name', '')
            },
            'email': linkedin_profile.get('email'),  # May be null
            'linkedin_url': linkedin_profile.get('public_url', ''),
            'current_title': linkedin_profile.get('current_title'),
            'current_company': linkedin_profile.get('current_company'),
            'location': linkedin_profile.get('location'),
            'years_experience': linkedin_profile.get('years_experience'),

            # Data quality metadata
            'data_quality_score': 0.65,  # Lower for LinkedIn-sourced
            'profile_completeness': self.assess_profile_completeness(linkedin_profile),
            'last_updated': datetime.now(),
            'source_confidence': 0.70
        }

        # Create in knowledge graph
        self.kg.create_candidate(candidate)

        # Create skills relationships
        for skill in linkedin_profile.get('skills', []):
            self.kg.create_relationship(
                from_id=candidate['candidate_id'],
                to_skill=skill,
                relationship_type='HAS_SKILL',
                attributes={
                    'proficiency_level': 'UNKNOWN',  # Need to verify
                    'verified': False,
                    'verification_source': 'LINKEDIN_PROFILE'
                }
            )

        return candidate

    def assess_profile_completeness(self, profile: Dict) -> float:
        """Assess how complete a LinkedIn profile is"""
        required_fields = ['first_name', 'last_name', 'current_title',
                          'current_company', 'location', 'skills']

        present_fields = sum(1 for field in required_fields if profile.get(field))
        return present_fields / len(required_fields)

    def generate_outreach_message(self, candidate: Dict, requisition: Dict) -> Dict:
        """
        Generate personalized outreach message
        """
        # Get candidate context
        candidate_context = {
            'name': candidate['name']['first_name'],
            'current_title': candidate.get('current_title'),
            'current_company': candidate.get('current_company'),
            'skills': candidate.get('skills', [])
        }

        # Get req context
        req_context = {
            'job_title': requisition.get('job_title', ''),
            'company_name': 'Our Company',
            'department': requisition.get('department', ''),
            'key_responsibilities': requisition.get('key_responsibilities', []),
            'unique_selling_points': self.get_company_usps()
        }

        # Select appropriate template based on candidate profile
        template = self.select_message_template(candidate, requisition)

        # Generate personalized message
        message = self.llm_generate({
            'template': template,
            'candidate_context': candidate_context,
            'req_context': req_context,
            'tone': 'professional_friendly',
            'length': 'medium',  # 150-250 words
            'include_call_to_action': True,
            'personalization_level': 'high'
        })

        # Add tracking
        message['metadata'] = {
            'template_id': template.get('id'),
            'candidate_id': candidate.get('candidate_id'),
            'requisition_id': requisition.get('requisition_id'),
            'sent_by': 'linkedin_hunter_agent',
            'tracking_link': self.generate_tracking_link(candidate, requisition)
        }

        return message

    def get_company_usps(self) -> List[str]:
        """Get company unique selling points"""
        # Placeholder - would query from database
        return [
            "Innovative technology stack",
            "Strong career growth opportunities",
            "Competitive compensation and benefits"
        ]

    def select_message_template(self, candidate: Dict, requisition: Dict) -> Dict:
        """Select appropriate message template"""
        # Simple logic - in production would be more sophisticated
        return self.messaging_templates.get('initial_outreach', {})

    def llm_generate(self, params: Dict) -> Dict:
        """Generate message using LLM"""
        # Placeholder - would call actual LLM API
        template = params.get('template', {})
        candidate_ctx = params.get('candidate_context', {})
        req_ctx = params.get('req_context', {})

        message_text = f"""Hi {candidate_ctx.get('name', '')},

I came across your profile and was impressed by your experience as {candidate_ctx.get('current_title', '')} at {candidate_ctx.get('current_company', '')}.

We have an exciting opportunity for a {req_ctx.get('job_title', '')} role in our {req_ctx.get('department', '')} department. Based on your background, I think you'd be a great fit.

Would you be open to a brief conversation about this opportunity?

Best regards"""

        return {
            'subject': f"Exciting opportunity: {req_ctx.get('job_title', '')}",
            'body': message_text,
            'generated_at': datetime.now()
        }

    def generate_tracking_link(self, candidate: Dict, requisition: Dict) -> str:
        """Generate tracking link for outreach"""
        tracking_id = uuid.uuid4()
        return f"https://track.example.com/{tracking_id}"

    def respect_contact_constraints(self, candidate_id: str) -> Dict:
        """
        Check if we can contact this candidate
        """
        query = """
        MATCH (c:Candidate {candidate_id: $candidate_id})
        RETURN c.can_contact as can_contact,
               c.last_contacted as last_contacted,
               c.contact_restrictions as restrictions
        """

        result = self.kg.query(query, {'candidate_id': candidate_id})

        if not result:
            return {'allowed': False, 'reason': 'candidate_not_found'}

        result = result[0]

        # Check permission
        if not result.get('can_contact', True):
            return {'allowed': False, 'reason': 'no_permission'}

        # Check time constraints
        if result.get('last_contacted'):
            days_since = (datetime.now() - result['last_contacted']).days
            if days_since < 7:
                return {
                    'allowed': False,
                    'reason': 'too_soon',
                    'wait_days': 7 - days_since
                }

        # Check time of day restrictions
        restrictions = result.get('restrictions', {})
        current_time = datetime.now().time()

        if restrictions.get('no_calls_before'):
            if current_time < time.fromisoformat(restrictions['no_calls_before']):
                return {'allowed': False, 'reason': 'outside_hours'}

        if restrictions.get('no_calls_after'):
            if current_time > time.fromisoformat(restrictions['no_calls_after']):
                return {'allowed': False, 'reason': 'outside_hours'}

        return {'allowed': True}
