"""
Search Agent - Finds candidates on LinkedIn
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class SearchAgent(BaseAgent):
    """
    Specialized agent for searching and discovering candidates on LinkedIn.
    Handles query building, search execution, and initial filtering.
    """

    def __init__(self, agent_id: str, linkedin_interface, config: Dict = None):
        """
        Initialize Search Agent

        Args:
            agent_id: Unique agent identifier
            linkedin_interface: LinkedInHunterInterface instance
            config: Configuration dictionary
        """
        super().__init__(agent_id, config)
        self.linkedin = linkedin_interface
        self.search_strategies = {
            'broad': self._broad_search,
            'targeted': self._targeted_search,
            'passive': self._passive_candidate_search,
            'similar_profile': self._similar_profile_search
        }

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process search task

        Args:
            task: Task with requisition_id and search parameters

        Returns:
            Dictionary with candidate results
        """
        task_type = task.get('type', 'search')
        requisition_id = task.get('requisition_id')
        search_strategy = task.get('strategy', 'targeted')
        max_results = task.get('max_results', 50)

        if task_type == 'search':
            return self._execute_search(requisition_id, search_strategy, max_results)
        elif task_type == 'expand_search':
            return self._expand_search(requisition_id, task.get('existing_candidates', []))
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _execute_search(self, requisition_id: str, strategy: str, max_results: int) -> Dict[str, Any]:
        """Execute candidate search"""
        self.logger.info(f"Executing {strategy} search for requisition {requisition_id}")

        # Get the search function for this strategy
        search_func = self.search_strategies.get(strategy, self._targeted_search)

        # Execute search
        candidates = search_func(requisition_id, max_results)

        return {
            'requisition_id': requisition_id,
            'strategy': strategy,
            'candidates_found': len(candidates),
            'candidates': candidates,
            'search_metadata': {
                'max_results': max_results,
                'filters_applied': self._get_applied_filters(requisition_id)
            }
        }

    def _targeted_search(self, requisition_id: str, max_results: int) -> List[Dict]:
        """
        Targeted search focusing on exact requirements
        """
        req_profile = self.linkedin.get_requisition_profile(requisition_id)
        search_params = self.linkedin.build_linkedin_search(req_profile)

        # Add strict filters for targeted search
        search_params['exact_title_match'] = True
        search_params['min_skill_overlap'] = 0.7

        # Execute search via LinkedIn interface
        results = self.linkedin.linkedin.search(search_params)

        # Initial filtering
        filtered_results = []
        for profile in results[:max_results * 2]:  # Get extra for filtering
            if self._meets_minimum_criteria(profile, req_profile):
                filtered_results.append(profile)

            if len(filtered_results) >= max_results:
                break

        self.logger.info(f"Targeted search found {len(filtered_results)} candidates")
        return filtered_results

    def _broad_search(self, requisition_id: str, max_results: int) -> List[Dict]:
        """
        Broad search with relaxed criteria to find more candidates
        """
        req_profile = self.linkedin.get_requisition_profile(requisition_id)
        search_params = self.linkedin.build_linkedin_search(req_profile)

        # Relax criteria for broad search
        if 'min_years_experience' in search_params.get('years_experience', {}):
            search_params['years_experience']['min'] = max(
                0,
                search_params['years_experience']['min'] - 2
            )

        # Expand location radius
        search_params['location_radius'] = 100  # miles

        results = self.linkedin.linkedin.search(search_params)

        self.logger.info(f"Broad search found {len(results[:max_results])} candidates")
        return results[:max_results]

    def _passive_candidate_search(self, requisition_id: str, max_results: int) -> List[Dict]:
        """
        Search for passive candidates (not actively looking)
        """
        req_profile = self.linkedin.get_requisition_profile(requisition_id)
        search_params = self.linkedin.build_linkedin_search(req_profile)

        # Focus on employed candidates at stable companies
        search_params['employment_status'] = 'employed'
        search_params['tenure_min_months'] = 12  # At current job for 1+ years

        # Look for high-engagement profiles
        search_params['activity_level'] = 'high'

        results = self.linkedin.linkedin.search(search_params)

        # Filter for passive indicators
        passive_candidates = []
        for profile in results:
            if self._is_passive_candidate(profile):
                passive_candidates.append(profile)

            if len(passive_candidates) >= max_results:
                break

        self.logger.info(f"Passive search found {len(passive_candidates)} candidates")
        return passive_candidates

    def _similar_profile_search(self, requisition_id: str, max_results: int) -> List[Dict]:
        """
        Find candidates similar to top performers
        """
        # Get top performers for this role
        top_performers = self._get_top_performers(requisition_id)

        if not top_performers:
            # Fall back to targeted search
            return self._targeted_search(requisition_id, max_results)

        # Build composite profile from top performers
        composite_profile = self._build_composite_profile(top_performers)

        # Search for similar candidates
        search_params = self._profile_to_search_params(composite_profile)
        results = self.linkedin.linkedin.search(search_params)

        self.logger.info(f"Similar profile search found {len(results[:max_results])} candidates")
        return results[:max_results]

    def _expand_search(self, requisition_id: str, existing_candidates: List[Dict]) -> Dict[str, Any]:
        """
        Expand search to find additional candidates
        """
        self.logger.info("Expanding search with alternative criteria")

        # Analyze existing candidates to identify patterns
        patterns = self._analyze_candidate_patterns(existing_candidates)

        # Try different search strategies
        additional_candidates = []

        # Strategy 1: Broaden skills
        skill_variants = self._generate_skill_variants(patterns.get('common_skills', []))
        additional_candidates.extend(self._search_with_alternative_skills(requisition_id, skill_variants))

        # Strategy 2: Adjacent titles
        title_variants = self._generate_title_variants(patterns.get('common_titles', []))
        additional_candidates.extend(self._search_with_alternative_titles(requisition_id, title_variants))

        # Deduplicate
        seen_urls = {c.get('public_url') for c in existing_candidates}
        unique_candidates = [
            c for c in additional_candidates
            if c.get('public_url') not in seen_urls
        ]

        return {
            'requisition_id': requisition_id,
            'expansion_strategy': 'multi_strategy',
            'candidates_found': len(unique_candidates),
            'candidates': unique_candidates[:50]  # Limit expansion
        }

    def _meets_minimum_criteria(self, profile: Dict, req_profile: Dict) -> bool:
        """Check if profile meets minimum requirements"""
        # Check years of experience
        min_years = req_profile.get('min_years_experience', 0)
        if profile.get('years_experience', 0) < min_years * 0.8:  # Allow 20% flexibility
            return False

        # Check required skills
        required_skills = set(s['skill'] for s in req_profile.get('required_skills', []))
        profile_skills = set(profile.get('skills', []))

        if required_skills:
            overlap = len(required_skills & profile_skills) / len(required_skills)
            if overlap < 0.3:  # Must have at least 30% skill overlap
                return False

        return True

    def _is_passive_candidate(self, profile: Dict) -> bool:
        """Determine if candidate appears to be passive"""
        # Indicators: employed, stable tenure, not "open to work"
        if profile.get('open_to_opportunities'):
            return False

        tenure_months = profile.get('current_job_tenure_months', 0)
        if tenure_months < 6:  # Too new to be stable passive candidate
            return False

        return True

    def _get_top_performers(self, requisition_id: str) -> List[Dict]:
        """Get top performers for similar roles"""
        # Placeholder - would query from knowledge graph
        return []

    def _build_composite_profile(self, top_performers: List[Dict]) -> Dict:
        """Build composite profile from top performers"""
        # Aggregate common attributes
        all_skills = []
        all_titles = []

        for performer in top_performers:
            all_skills.extend(performer.get('skills', []))
            all_titles.append(performer.get('current_title', ''))

        # Find most common skills
        from collections import Counter
        skill_counts = Counter(all_skills)
        common_skills = [skill for skill, count in skill_counts.most_common(10)]

        return {
            'common_skills': common_skills,
            'common_titles': all_titles,
            'avg_years_experience': sum(p.get('years_experience', 0) for p in top_performers) / len(top_performers)
        }

    def _profile_to_search_params(self, profile: Dict) -> Dict:
        """Convert composite profile to search parameters"""
        return {
            'skills': profile.get('common_skills', [])[:5],
            'title': profile.get('common_titles', [''])[0],
            'years_experience': {
                'min': int(profile.get('avg_years_experience', 0) * 0.7),
                'max': int(profile.get('avg_years_experience', 0) * 1.3)
            }
        }

    def _analyze_candidate_patterns(self, candidates: List[Dict]) -> Dict:
        """Analyze patterns in existing candidates"""
        from collections import Counter

        all_skills = []
        all_titles = []

        for candidate in candidates:
            all_skills.extend(candidate.get('profile', {}).get('skills', []))
            if candidate.get('profile', {}).get('current_title'):
                all_titles.append(candidate['profile']['current_title'])

        skill_counts = Counter(all_skills)
        title_counts = Counter(all_titles)

        return {
            'common_skills': [skill for skill, _ in skill_counts.most_common(15)],
            'common_titles': [title for title, _ in title_counts.most_common(5)]
        }

    def _generate_skill_variants(self, skills: List[str]) -> List[str]:
        """Generate variant skills"""
        # Placeholder - would use semantic similarity
        variants = skills.copy()

        # Add common variants
        skill_map = {
            'Python': ['Python3', 'Python 3', 'Django', 'Flask'],
            'JavaScript': ['JS', 'TypeScript', 'Node.js', 'React'],
            'Machine Learning': ['ML', 'Deep Learning', 'AI', 'Data Science']
        }

        for skill in skills:
            if skill in skill_map:
                variants.extend(skill_map[skill])

        return list(set(variants))

    def _generate_title_variants(self, titles: List[str]) -> List[str]:
        """Generate variant job titles"""
        # Placeholder - would use semantic similarity
        variants = titles.copy()

        # Common title mappings
        title_map = {
            'Software Engineer': ['Developer', 'Programmer', 'Software Developer'],
            'Data Scientist': ['ML Engineer', 'Data Analyst', 'Analytics Engineer'],
            'Product Manager': ['Product Owner', 'Technical Product Manager']
        }

        for title in titles:
            for key, values in title_map.items():
                if key.lower() in title.lower():
                    variants.extend(values)

        return list(set(variants))

    def _search_with_alternative_skills(self, requisition_id: str, skills: List[str]) -> List[Dict]:
        """Search with alternative skills"""
        # Simplified implementation
        return []

    def _search_with_alternative_titles(self, requisition_id: str, titles: List[str]) -> List[Dict]:
        """Search with alternative titles"""
        # Simplified implementation
        return []

    def _get_applied_filters(self, requisition_id: str) -> Dict:
        """Get filters that were applied to search"""
        req_profile = self.linkedin.get_requisition_profile(requisition_id)
        return {
            'location': req_profile.get('location'),
            'min_years': req_profile.get('min_years_experience'),
            'required_skills': [s['skill'] for s in req_profile.get('required_skills', [])]
        }

    def can_handle(self, task: Dict[str, Any]) -> bool:
        """Check if this agent can handle the task"""
        return task.get('type') in ['search', 'expand_search']
