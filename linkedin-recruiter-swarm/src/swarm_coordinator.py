"""
Swarm Coordinator - Orchestrates multiple recruiting agents
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .agents import SearchAgent, ScoringAgent, OutreachAgent, FollowUpAgent


class RecruiterSwarm:
    """
    Coordinates multiple specialized agents to execute recruiting workflows.

    The swarm orchestrates:
    - Candidate search and discovery
    - Scoring and ranking
    - Personalized outreach
    - Follow-up management

    Agents work autonomously but are coordinated by the swarm for
    complex multi-step recruiting pipelines.
    """

    def __init__(self, linkedin_interface, config: Optional[Dict] = None):
        """
        Initialize Recruiter Swarm

        Args:
            linkedin_interface: LinkedInHunterInterface instance
            config: Configuration dictionary
        """
        self.linkedin = linkedin_interface
        self.config = config or {}
        self.logger = self._setup_logger()

        # Initialize agents
        self.agents = self._initialize_agents()

        # Execution state
        self.state = {
            'active_workflows': {},
            'completed_workflows': [],
            'total_candidates_processed': 0,
            'created_at': datetime.now()
        }

        # Thread pool for parallel execution
        self.max_workers = config.get('max_workers', 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for swarm"""
        logger = logging.getLogger('RecruiterSwarm')
        logger.setLevel(logging.INFO)

        # Add console handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all specialized agents"""
        self.logger.info("Initializing agent swarm")

        agents = {
            'search': SearchAgent(
                agent_id='search_001',
                linkedin_interface=self.linkedin,
                config=self.config.get('search_agent', {})
            ),
            'scoring': ScoringAgent(
                agent_id='scoring_001',
                linkedin_interface=self.linkedin,
                config=self.config.get('scoring_agent', {})
            ),
            'outreach': OutreachAgent(
                agent_id='outreach_001',
                linkedin_interface=self.linkedin,
                config=self.config.get('outreach_agent', {})
            ),
            'followup': FollowUpAgent(
                agent_id='followup_001',
                linkedin_interface=self.linkedin,
                config=self.config.get('followup_agent', {})
            )
        }

        self.logger.info(f"Initialized {len(agents)} agents")
        return agents

    def run_full_pipeline(self, requisition_id: str, pipeline_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run complete recruiting pipeline for a requisition

        Pipeline stages:
        1. Search for candidates
        2. Score and rank candidates
        3. Execute outreach to top candidates
        4. Setup follow-up tracking

        Args:
            requisition_id: Requisition to recruit for
            pipeline_config: Optional pipeline configuration

        Returns:
            Pipeline execution results
        """
        self.logger.info(f"Starting full pipeline for requisition {requisition_id}")

        workflow_id = f"workflow_{requisition_id}_{datetime.now().timestamp()}"
        self.state['active_workflows'][workflow_id] = {
            'requisition_id': requisition_id,
            'started_at': datetime.now(),
            'status': 'running'
        }

        config = pipeline_config or {}

        try:
            # Stage 1: Search for candidates
            self.logger.info("Stage 1: Searching for candidates")
            search_result = self._run_search_stage(requisition_id, config)

            # Stage 2: Score candidates
            self.logger.info(f"Stage 2: Scoring {len(search_result.get('candidates', []))} candidates")
            scoring_result = self._run_scoring_stage(
                search_result['candidates'],
                requisition_id,
                config
            )

            # Stage 3: Outreach to top candidates
            top_candidates = self._select_top_candidates(
                scoring_result['scored_candidates'],
                config.get('outreach_count', 20)
            )

            self.logger.info(f"Stage 3: Outreach to {len(top_candidates)} top candidates")
            outreach_result = self._run_outreach_stage(
                top_candidates,
                requisition_id,
                config
            )

            # Stage 4: Setup follow-up tracking
            self.logger.info("Stage 4: Setting up follow-up tracking")
            followup_setup = self._setup_followup_tracking(
                outreach_result['details'],
                requisition_id
            )

            # Compile results
            pipeline_result = {
                'workflow_id': workflow_id,
                'requisition_id': requisition_id,
                'status': 'completed',
                'stages': {
                    'search': {
                        'candidates_found': search_result.get('candidates_found', 0),
                        'strategy': search_result.get('strategy')
                    },
                    'scoring': {
                        'candidates_scored': scoring_result.get('total_candidates_scored', 0),
                        'above_threshold': scoring_result.get('candidates_above_threshold', 0),
                        'statistics': scoring_result.get('score_statistics', {})
                    },
                    'outreach': {
                        'messages_sent': outreach_result.get('messages_sent', 0),
                        'skipped': outreach_result.get('skipped', 0)
                    },
                    'followup': followup_setup
                },
                'completed_at': datetime.now(),
                'duration_seconds': (datetime.now() - self.state['active_workflows'][workflow_id]['started_at']).total_seconds()
            }

            # Update state
            self.state['active_workflows'][workflow_id]['status'] = 'completed'
            self.state['completed_workflows'].append(workflow_id)
            self.state['total_candidates_processed'] += search_result.get('candidates_found', 0)

            self.logger.info(f"Pipeline completed successfully: {workflow_id}")
            return pipeline_result

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.state['active_workflows'][workflow_id]['status'] = 'failed'
            self.state['active_workflows'][workflow_id]['error'] = str(e)

            return {
                'workflow_id': workflow_id,
                'requisition_id': requisition_id,
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.now()
            }

    def _run_search_stage(self, requisition_id: str, config: Dict) -> Dict[str, Any]:
        """Run search stage"""
        search_task = {
            'type': 'search',
            'requisition_id': requisition_id,
            'strategy': config.get('search_strategy', 'targeted'),
            'max_results': config.get('max_search_results', 100)
        }

        result = self.agents['search'].execute_task(search_task)
        return result['result']

    def _run_scoring_stage(self, candidates: List[Dict], requisition_id: str, config: Dict) -> Dict[str, Any]:
        """Run scoring stage"""
        scoring_task = {
            'type': 'score',
            'candidates': candidates,
            'requisition_id': requisition_id
        }

        result = self.agents['scoring'].execute_task(scoring_task)
        return result['result']

    def _run_outreach_stage(self, candidates: List[Dict], requisition_id: str, config: Dict) -> Dict[str, Any]:
        """Run outreach stage"""
        outreach_task = {
            'type': 'outreach',
            'candidates': candidates,
            'requisition_id': requisition_id,
            'strategy': config.get('outreach_strategy', 'personalized')
        }

        result = self.agents['outreach'].execute_task(outreach_task)
        return result['result']

    def _setup_followup_tracking(self, outreach_details: List[Dict], requisition_id: str) -> Dict[str, Any]:
        """Setup follow-up tracking for contacted candidates"""
        # Extract successfully contacted candidates
        contacted = [
            detail for detail in outreach_details
            if detail.get('status') == 'sent'
        ]

        return {
            'candidates_tracked': len(contacted),
            'follow_up_scheduled': True,
            'first_follow_up_days': self.agents['followup'].follow_up_intervals['first']
        }

    def _select_top_candidates(self, scored_candidates: List[Dict], count: int) -> List[Dict]:
        """Select top N candidates by score"""
        # Already sorted by score in scoring agent
        return scored_candidates[:count]

    def run_parallel_search(self, requisition_id: str, strategies: List[str]) -> Dict[str, Any]:
        """
        Run multiple search strategies in parallel

        Args:
            requisition_id: Requisition ID
            strategies: List of search strategies to run

        Returns:
            Combined search results
        """
        self.logger.info(f"Running {len(strategies)} search strategies in parallel")

        futures = []
        for strategy in strategies:
            task = {
                'type': 'search',
                'requisition_id': requisition_id,
                'strategy': strategy,
                'max_results': 50
            }

            future = self.executor.submit(self.agents['search'].execute_task, task)
            futures.append((strategy, future))

        # Collect results
        all_candidates = []
        results_by_strategy = {}

        for strategy, future in futures:
            try:
                result = future.result(timeout=60)
                candidates = result['result']['candidates']
                all_candidates.extend(candidates)
                results_by_strategy[strategy] = {
                    'candidates_found': len(candidates),
                    'status': 'success'
                }
            except Exception as e:
                self.logger.error(f"Strategy {strategy} failed: {str(e)}")
                results_by_strategy[strategy] = {
                    'candidates_found': 0,
                    'status': 'failed',
                    'error': str(e)
                }

        # Deduplicate candidates
        unique_candidates = self._deduplicate_candidates(all_candidates)

        return {
            'requisition_id': requisition_id,
            'strategies_executed': len(strategies),
            'total_candidates': len(unique_candidates),
            'results_by_strategy': results_by_strategy,
            'candidates': unique_candidates
        }

    def _deduplicate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Remove duplicate candidates"""
        seen = set()
        unique = []

        for candidate in candidates:
            # Use LinkedIn URL as unique identifier
            linkedin_url = candidate.get('public_url', '')
            if linkedin_url and linkedin_url not in seen:
                seen.add(linkedin_url)
                unique.append(candidate)

        return unique

    def run_continuous_sourcing(self, requisition_id: str, duration_days: int = 7) -> Dict[str, Any]:
        """
        Run continuous sourcing over a period of time

        Args:
            requisition_id: Requisition ID
            duration_days: How many days to run

        Returns:
            Continuous sourcing configuration
        """
        self.logger.info(f"Setting up continuous sourcing for {duration_days} days")

        # In production, this would set up scheduled tasks
        # For now, return configuration

        return {
            'requisition_id': requisition_id,
            'mode': 'continuous',
            'duration_days': duration_days,
            'schedule': {
                'search_frequency': 'daily',
                'outreach_batch_size': 10,
                'follow_up_checks': 'daily'
            },
            'status': 'configured'
        }

    def process_candidate_responses(self, requisition_id: str, responses: List[Dict]) -> Dict[str, Any]:
        """
        Process candidate responses and trigger appropriate actions

        Args:
            requisition_id: Requisition ID
            responses: List of candidate responses

        Returns:
            Processing results
        """
        self.logger.info(f"Processing {len(responses)} candidate responses")

        # Use follow-up agent to analyze responses
        task = {
            'type': 'process_responses',
            'responses': responses
        }

        result = self.agents['followup'].execute_task(task)
        response_analysis = result['result']

        # Take actions based on responses
        actions_taken = []

        # Schedule interviews for interested candidates
        if response_analysis['interested'] > 0:
            interested_candidates = [
                r for r in response_analysis['processed']
                if r['category'] == 'interested'
            ]

            schedule_task = {
                'type': 'schedule_interviews',
                'candidates': interested_candidates,
                'requisition_id': requisition_id
            }

            schedule_result = self.agents['followup'].execute_task(schedule_task)
            actions_taken.append({
                'action': 'schedule_interviews',
                'result': schedule_result['result']
            })

        return {
            'requisition_id': requisition_id,
            'responses_processed': len(responses),
            'analysis': response_analysis,
            'actions_taken': actions_taken
        }

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get current status of the swarm"""
        agent_statuses = {}
        for name, agent in self.agents.items():
            agent_statuses[name] = agent.get_status()

        return {
            'swarm_state': self.state,
            'agents': agent_statuses,
            'active_workflows': len(self.state['active_workflows']),
            'completed_workflows': len(self.state['completed_workflows'])
        }

    def reset_swarm(self) -> None:
        """Reset all agents in the swarm"""
        self.logger.info("Resetting swarm")

        for agent in self.agents.values():
            agent.reset()

        self.state = {
            'active_workflows': {},
            'completed_workflows': [],
            'total_candidates_processed': 0,
            'created_at': datetime.now()
        }

    def shutdown(self) -> None:
        """Shutdown the swarm and cleanup resources"""
        self.logger.info("Shutting down swarm")
        self.executor.shutdown(wait=True)

    def run_adaptive_pipeline(self, requisition_id: str, target_candidate_count: int = 50) -> Dict[str, Any]:
        """
        Run adaptive pipeline that adjusts strategy based on results

        Args:
            requisition_id: Requisition ID
            target_candidate_count: Target number of qualified candidates

        Returns:
            Pipeline results
        """
        self.logger.info(f"Starting adaptive pipeline (target: {target_candidate_count} candidates)")

        qualified_candidates = []
        attempts = 0
        max_attempts = 3

        while len(qualified_candidates) < target_candidate_count and attempts < max_attempts:
            attempts += 1

            # Adjust strategy based on attempt
            if attempts == 1:
                strategy = 'targeted'
            elif attempts == 2:
                strategy = 'broad'
            else:
                strategy = 'passive'

            self.logger.info(f"Attempt {attempts}: Using {strategy} strategy")

            # Search
            search_result = self._run_search_stage(
                requisition_id,
                {'search_strategy': strategy, 'max_search_results': 100}
            )

            # Score
            scoring_result = self._run_scoring_stage(
                search_result['candidates'],
                requisition_id,
                {}
            )

            # Add qualified candidates
            new_qualified = scoring_result['scored_candidates']
            qualified_candidates.extend(new_qualified)

            self.logger.info(f"Found {len(new_qualified)} qualified candidates (total: {len(qualified_candidates)})")

            # If we have enough, break
            if len(qualified_candidates) >= target_candidate_count:
                break

        # Deduplicate
        unique_qualified = self._deduplicate_candidates(qualified_candidates)

        # Outreach to top candidates
        top_candidates = self._select_top_candidates(
            unique_qualified,
            min(target_candidate_count, len(unique_qualified))
        )

        outreach_result = self._run_outreach_stage(
            top_candidates,
            requisition_id,
            {}
        )

        return {
            'requisition_id': requisition_id,
            'mode': 'adaptive',
            'attempts': attempts,
            'target': target_candidate_count,
            'qualified_found': len(unique_qualified),
            'outreach_sent': outreach_result.get('messages_sent', 0),
            'status': 'completed' if len(unique_qualified) >= target_candidate_count else 'partial'
        }
