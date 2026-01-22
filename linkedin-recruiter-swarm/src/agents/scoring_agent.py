"""
Scoring Agent - Evaluates and ranks candidates
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ScoringAgent(BaseAgent):
    """
    Specialized agent for scoring and ranking candidates.
    Evaluates candidate fit using multiple criteria and provides
    detailed scoring breakdowns.
    """

    def __init__(self, agent_id: str, linkedin_interface, config: Dict = None):
        """
        Initialize Scoring Agent

        Args:
            agent_id: Unique agent identifier
            linkedin_interface: LinkedInHunterInterface instance
            config: Configuration dictionary
        """
        super().__init__(agent_id, config)
        self.linkedin = linkedin_interface
        self.scoring_weights = config.get('scoring_weights', {
            'skill_match': 0.40,
            'experience_match': 0.30,
            'title_match': 0.15,
            'location_match': 0.10,
            'activity_score': 0.05
        })
        self.min_threshold = config.get('min_threshold', 0.6)

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process scoring task

        Args:
            task: Task with candidates and requisition info

        Returns:
            Dictionary with scored and ranked candidates
        """
        task_type = task.get('type', 'score')
        candidates = task.get('candidates', [])
        requisition_id = task.get('requisition_id')

        if task_type == 'score':
            return self._score_candidates(candidates, requisition_id)
        elif task_type == 'rescore':
            return self._rescore_candidates(candidates, requisition_id, task.get('criteria'))
        elif task_type == 'compare':
            return self._compare_candidates(task.get('candidate_ids', []), requisition_id)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _score_candidates(self, candidates: List[Dict], requisition_id: str) -> Dict[str, Any]:
        """
        Score all candidates for a requisition

        Args:
            candidates: List of candidate profiles
            requisition_id: Requisition ID to score against

        Returns:
            Scored and ranked candidates
        """
        self.logger.info(f"Scoring {len(candidates)} candidates for requisition {requisition_id}")

        req_profile = self.linkedin.get_requisition_profile(requisition_id)

        scored_candidates = []
        for candidate in candidates:
            profile = candidate if 'profile' not in candidate else candidate['profile']

            # Score the profile
            score_result = self.linkedin.score_linkedin_profile(profile, req_profile)

            # Add additional scoring dimensions
            enhanced_score = self._enhance_scoring(profile, req_profile, score_result)

            # Only include candidates above threshold
            if enhanced_score['total_score'] >= self.min_threshold:
                scored_candidates.append({
                    'candidate': candidate,
                    'score': enhanced_score['total_score'],
                    'score_breakdown': enhanced_score,
                    'ranking_tier': self._determine_tier(enhanced_score['total_score']),
                    'recommendation': self._generate_recommendation(enhanced_score)
                })

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)

        # Add ranking position
        for idx, candidate in enumerate(scored_candidates):
            candidate['rank'] = idx + 1

        return {
            'requisition_id': requisition_id,
            'total_candidates_scored': len(candidates),
            'candidates_above_threshold': len(scored_candidates),
            'scored_candidates': scored_candidates,
            'score_statistics': self._calculate_statistics(scored_candidates)
        }

    def _enhance_scoring(self, profile: Dict, req_profile: Dict, base_score: Dict) -> Dict:
        """
        Enhance base scoring with additional factors

        Args:
            profile: Candidate profile
            req_profile: Requisition profile
            base_score: Base score from LinkedInHunterInterface

        Returns:
            Enhanced score dictionary
        """
        enhanced_components = base_score['components'].copy()

        # Add diversity scoring (bonus points)
        diversity_score = self._calculate_diversity_score(profile)
        if diversity_score > 0:
            enhanced_components['diversity_bonus'] = diversity_score * 0.05

        # Add cultural fit indicators
        culture_fit = self._assess_cultural_fit(profile, req_profile)
        enhanced_components['culture_fit'] = culture_fit * 0.05

        # Add career trajectory analysis
        trajectory_score = self._analyze_career_trajectory(profile)
        enhanced_components['career_trajectory'] = trajectory_score * 0.05

        # Add education quality score
        education_score = self._score_education(profile, req_profile)
        enhanced_components['education_quality'] = education_score * 0.05

        # Recalculate total with enhanced components
        total_score = sum(enhanced_components.values())

        # Normalize to 0-1 range
        total_score = min(1.0, total_score)

        return {
            'total_score': total_score,
            'components': enhanced_components,
            'confidence': base_score.get('confidence', 0.5),
            'flags': self._identify_flags(profile, enhanced_components)
        }

    def _calculate_diversity_score(self, profile: Dict) -> float:
        """Calculate diversity indicators"""
        # Placeholder - would use more sophisticated analysis
        # Could consider: underrepresented groups, geographic diversity, etc.
        # For now, return neutral score
        return 0.0

    def _assess_cultural_fit(self, profile: Dict, req_profile: Dict) -> float:
        """
        Assess cultural fit indicators

        Args:
            profile: Candidate profile
            req_profile: Requisition requirements

        Returns:
            Culture fit score (0-1)
        """
        fit_score = 0.0

        # Company size preference
        current_company_size = profile.get('current_company_size', 'unknown')
        target_company_size = req_profile.get('company_size', 'unknown')

        if current_company_size == target_company_size:
            fit_score += 0.3

        # Industry alignment
        current_industry = profile.get('industry', '')
        target_industry = req_profile.get('industry', '')

        if current_industry and target_industry:
            if current_industry.lower() == target_industry.lower():
                fit_score += 0.4
            elif self._is_adjacent_industry(current_industry, target_industry):
                fit_score += 0.2

        # Work style indicators (from profile activity)
        work_style_match = self._match_work_style(profile, req_profile)
        fit_score += work_style_match * 0.3

        return min(1.0, fit_score)

    def _is_adjacent_industry(self, industry1: str, industry2: str) -> bool:
        """Check if industries are adjacent/related"""
        # Simplified - would use industry taxonomy
        adjacent_pairs = {
            ('tech', 'software'),
            ('finance', 'fintech'),
            ('healthcare', 'biotech')
        }

        i1_lower = industry1.lower()
        i2_lower = industry2.lower()

        return (i1_lower, i2_lower) in adjacent_pairs or (i2_lower, i1_lower) in adjacent_pairs

    def _match_work_style(self, profile: Dict, req_profile: Dict) -> float:
        """Match work style preferences"""
        # Placeholder - would analyze profile for work style indicators
        return 0.5

    def _analyze_career_trajectory(self, profile: Dict) -> float:
        """
        Analyze career progression trajectory

        Args:
            profile: Candidate profile

        Returns:
            Trajectory score (0-1)
        """
        work_history = profile.get('work_history', [])

        if not work_history or len(work_history) < 2:
            return 0.5  # Neutral if insufficient data

        trajectory_score = 0.0

        # Check for upward movement in titles
        title_progression = self._check_title_progression(work_history)
        trajectory_score += title_progression * 0.4

        # Check for increasing company prestige
        company_progression = self._check_company_progression(work_history)
        trajectory_score += company_progression * 0.3

        # Check for skill expansion
        skill_growth = self._check_skill_growth(work_history)
        trajectory_score += skill_growth * 0.3

        return min(1.0, trajectory_score)

    def _check_title_progression(self, work_history: List[Dict]) -> float:
        """Check if titles show progression"""
        # Simplified - would use seniority level mapping
        seniority_map = {
            'intern': 1, 'junior': 2, 'associate': 3,
            'engineer': 4, 'senior': 5, 'lead': 6,
            'staff': 7, 'principal': 8, 'director': 9
        }

        levels = []
        for job in work_history:
            title = job.get('title', '').lower()
            for key, level in seniority_map.items():
                if key in title:
                    levels.append(level)
                    break

        if len(levels) < 2:
            return 0.5

        # Check if generally increasing
        increasing = sum(1 for i in range(len(levels)-1) if levels[i+1] > levels[i])
        return increasing / (len(levels) - 1) if len(levels) > 1 else 0.5

    def _check_company_progression(self, work_history: List[Dict]) -> float:
        """Check company prestige progression"""
        # Placeholder - would use company prestige database
        return 0.5

    def _check_skill_growth(self, work_history: List[Dict]) -> float:
        """Check skill expansion over time"""
        # Placeholder - would analyze skill additions over time
        return 0.5

    def _score_education(self, profile: Dict, req_profile: Dict) -> float:
        """
        Score education background

        Args:
            profile: Candidate profile
            req_profile: Requisition requirements

        Returns:
            Education score (0-1)
        """
        education = profile.get('education', [])
        req_education = req_profile.get('education_requirements', {})

        if not education:
            return 0.3 if not req_education else 0.0

        score = 0.0

        # Check degree level
        highest_degree = self._get_highest_degree(education)
        required_degree = req_education.get('minimum_degree', 'bachelors')

        degree_levels = {'highschool': 1, 'associates': 2, 'bachelors': 3, 'masters': 4, 'phd': 5}
        candidate_level = degree_levels.get(highest_degree, 0)
        required_level = degree_levels.get(required_degree, 3)

        if candidate_level >= required_level:
            score += 0.6
        else:
            score += 0.3 * (candidate_level / required_level)

        # Check field of study relevance
        relevant_fields = req_education.get('preferred_fields', [])
        if relevant_fields:
            candidate_fields = [e.get('field_of_study', '') for e in education]
            if any(field in relevant_fields for field in candidate_fields):
                score += 0.4

        return min(1.0, score)

    def _get_highest_degree(self, education: List[Dict]) -> str:
        """Get highest degree from education list"""
        degree_levels = {'highschool': 1, 'associates': 2, 'bachelors': 3, 'masters': 4, 'phd': 5}

        highest = 'highschool'
        highest_level = 0

        for edu in education:
            degree = edu.get('degree', '').lower()
            for deg_name, level in degree_levels.items():
                if deg_name in degree and level > highest_level:
                    highest = deg_name
                    highest_level = level

        return highest

    def _identify_flags(self, profile: Dict, score_components: Dict) -> List[str]:
        """
        Identify any flags or concerns about candidate

        Args:
            profile: Candidate profile
            score_components: Score component breakdown

        Returns:
            List of flag strings
        """
        flags = []

        # Check for job hopping
        work_history = profile.get('work_history', [])
        avg_tenure = self._calculate_average_tenure(work_history)
        if avg_tenure < 12:  # Less than 1 year average
            flags.append('short_tenure_pattern')

        # Check for employment gaps
        if self._has_employment_gaps(work_history):
            flags.append('employment_gaps')

        # Check for overqualification
        if score_components.get('experience_match', 0) > 0.9:
            if profile.get('years_experience', 0) > 15:
                flags.append('potential_overqualification')

        # Check for underqualification
        if score_components.get('skill_match', 0) < 0.3:
            flags.append('skill_gap_concern')

        # Check for location mismatch
        if score_components.get('location_match', 0) < 0.3:
            flags.append('location_mismatch')

        return flags

    def _calculate_average_tenure(self, work_history: List[Dict]) -> float:
        """Calculate average job tenure in months"""
        if not work_history:
            return 0

        tenures = [job.get('tenure_months', 0) for job in work_history if job.get('tenure_months')]

        return sum(tenures) / len(tenures) if tenures else 0

    def _has_employment_gaps(self, work_history: List[Dict]) -> bool:
        """Check for significant employment gaps"""
        # Placeholder - would analyze date ranges
        return False

    def _determine_tier(self, score: float) -> str:
        """
        Determine candidate tier based on score

        Args:
            score: Total score

        Returns:
            Tier string
        """
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.8:
            return 'strong'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.6:
            return 'acceptable'
        else:
            return 'below_threshold'

    def _generate_recommendation(self, score_result: Dict) -> str:
        """
        Generate hiring recommendation

        Args:
            score_result: Score breakdown

        Returns:
            Recommendation string
        """
        score = score_result['total_score']
        flags = score_result.get('flags', [])

        if score >= 0.9 and not flags:
            return 'strongly_recommend'
        elif score >= 0.8:
            if flags:
                return 'recommend_with_review'
            return 'recommend'
        elif score >= 0.7:
            return 'consider'
        elif score >= 0.6:
            return 'possible_backup'
        else:
            return 'pass'

    def _rescore_candidates(self, candidates: List[Dict], requisition_id: str,
                           custom_criteria: Dict) -> Dict[str, Any]:
        """Rescore with custom criteria"""
        # Update weights temporarily
        original_weights = self.scoring_weights.copy()

        if custom_criteria:
            self.scoring_weights.update(custom_criteria.get('weights', {}))

        # Rescore
        result = self._score_candidates(candidates, requisition_id)

        # Restore original weights
        self.scoring_weights = original_weights

        return result

    def _compare_candidates(self, candidate_ids: List[str], requisition_id: str) -> Dict[str, Any]:
        """Compare specific candidates"""
        # Placeholder - would fetch candidates and provide detailed comparison
        return {
            'requisition_id': requisition_id,
            'candidates_compared': len(candidate_ids),
            'comparison': 'detailed_comparison_would_go_here'
        }

    def _calculate_statistics(self, scored_candidates: List[Dict]) -> Dict:
        """Calculate scoring statistics"""
        if not scored_candidates:
            return {}

        scores = [c['score'] for c in scored_candidates]

        return {
            'mean_score': sum(scores) / len(scores),
            'median_score': sorted(scores)[len(scores) // 2],
            'min_score': min(scores),
            'max_score': max(scores),
            'tier_distribution': self._tier_distribution(scored_candidates)
        }

    def _tier_distribution(self, scored_candidates: List[Dict]) -> Dict:
        """Calculate distribution across tiers"""
        from collections import Counter
        tiers = [c['ranking_tier'] for c in scored_candidates]
        return dict(Counter(tiers))

    def can_handle(self, task: Dict[str, Any]) -> bool:
        """Check if this agent can handle the task"""
        return task.get('type') in ['score', 'rescore', 'compare']
