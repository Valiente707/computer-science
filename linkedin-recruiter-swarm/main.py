#!/usr/bin/env python3
"""
LinkedIn Recruiter Swarm - Main Example

Demonstrates how to use the recruiter swarm for automated candidate sourcing.
"""

import os
import yaml
import logging
from datetime import datetime
from dotenv import load_dotenv

# Mock implementations for demo purposes
# In production, these would be real implementations
class MockKnowledgeGraph:
    """Mock knowledge graph for demonstration"""

    def query(self, query: str, params: dict):
        """Mock query execution"""
        # Simulate requisition query
        if 'Requisition' in query:
            return [{
                'r': {
                    'requisition_id': params.get('req_id', 'REQ-12345'),
                    'job_title': 'Senior Software Engineer',
                    'department': 'Engineering',
                    'location': 'San Francisco, CA',
                    'min_years_experience': 5,
                    'required_skills': [
                        {'skill': 'Python', 'proficiency': 'expert'},
                        {'skill': 'Machine Learning', 'proficiency': 'advanced'},
                        {'skill': 'AWS', 'proficiency': 'intermediate'}
                    ]
                }
            }]
        return []

    def create_candidate(self, candidate):
        """Mock candidate creation"""
        pass

    def update_candidate(self, candidate_id, fields):
        """Mock candidate update"""
        pass

    def create_relationship(self, from_id, to_skill, relationship_type, attributes):
        """Mock relationship creation"""
        pass


class MockSemanticLayer:
    """Mock semantic layer for demonstration"""
    pass


class MockLinkedInAPI:
    """Mock LinkedIn API for demonstration"""

    def search(self, params: dict):
        """Mock LinkedIn search"""
        # Return mock profiles
        mock_profiles = []

        for i in range(50):
            profile = {
                'first_name': f'Candidate{i}',
                'last_name': f'Person{i}',
                'public_url': f'https://linkedin.com/in/candidate{i}',
                'email': f'candidate{i}@example.com',
                'current_title': 'Software Engineer' if i % 2 == 0 else 'Senior Software Engineer',
                'current_company': f'Tech Company {i % 10}',
                'location': 'San Francisco, CA' if i % 3 == 0 else 'New York, NY',
                'years_experience': 3 + (i % 10),
                'skills': ['Python', 'Machine Learning', 'AWS', 'Docker', 'Kubernetes'][:3 + (i % 3)],
                'connections': 500 + (i * 10),
                'endorsements': 10 + i,
                'recent_posts_count': i % 5
            }
            mock_profiles.append(profile)

        return mock_profiles


def load_config(config_path: str = 'config/swarm_config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print("Using default configuration")
        return {}


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_separator(title: str = ""):
    """Print a visual separator"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def example_full_pipeline():
    """Example: Run full recruiting pipeline"""
    from src import LinkedInHunterInterface, RecruiterSwarm

    print_separator("EXAMPLE 1: Full Recruiting Pipeline")

    # Initialize components
    kg = MockKnowledgeGraph()
    semantic = MockSemanticLayer()
    linkedin_api = MockLinkedInAPI()

    # Create interface
    linkedin_interface = LinkedInHunterInterface(
        knowledge_graph=kg,
        semantic_layer=semantic,
        linkedin_api=linkedin_api
    )

    # Load config
    config = load_config()

    # Initialize swarm
    swarm = RecruiterSwarm(
        linkedin_interface=linkedin_interface,
        config=config
    )

    # Run pipeline
    print("Running full recruiting pipeline...")
    result = swarm.run_full_pipeline(
        requisition_id='REQ-12345',
        pipeline_config={
            'search_strategy': 'targeted',
            'max_search_results': 50,
            'outreach_count': 10
        }
    )

    # Display results
    print(f"\n✓ Pipeline Status: {result['status']}")
    print(f"✓ Duration: {result['duration_seconds']:.1f} seconds")

    print("\n📊 Pipeline Results:")
    print(f"  Search:")
    print(f"    - Strategy: {result['stages']['search']['strategy']}")
    print(f"    - Candidates found: {result['stages']['search']['candidates_found']}")

    print(f"  Scoring:")
    print(f"    - Candidates scored: {result['stages']['scoring']['candidates_scored']}")
    print(f"    - Above threshold: {result['stages']['scoring']['above_threshold']}")

    stats = result['stages']['scoring']['statistics']
    print(f"    - Mean score: {stats.get('mean_score', 0):.2f}")
    print(f"    - Tier distribution: {stats.get('tier_distribution', {})}")

    print(f"  Outreach:")
    print(f"    - Messages sent: {result['stages']['outreach']['messages_sent']}")
    print(f"    - Skipped: {result['stages']['outreach']['skipped']}")

    return swarm


def example_parallel_search(swarm):
    """Example: Parallel search strategies"""
    print_separator("EXAMPLE 2: Parallel Search Strategies")

    print("Running multiple search strategies in parallel...")
    result = swarm.run_parallel_search(
        requisition_id='REQ-12345',
        strategies=['targeted', 'broad', 'passive']
    )

    print(f"\n✓ Strategies executed: {result['strategies_executed']}")
    print(f"✓ Total unique candidates: {result['total_candidates']}")

    print("\n📊 Results by Strategy:")
    for strategy, stats in result['results_by_strategy'].items():
        print(f"  {strategy}:")
        print(f"    - Candidates: {stats['candidates_found']}")
        print(f"    - Status: {stats['status']}")


def example_adaptive_pipeline(swarm):
    """Example: Adaptive pipeline"""
    print_separator("EXAMPLE 3: Adaptive Pipeline")

    print("Running adaptive pipeline (adjusts strategy based on results)...")
    result = swarm.run_adaptive_pipeline(
        requisition_id='REQ-12345',
        target_candidate_count=30
    )

    print(f"\n✓ Status: {result['status']}")
    print(f"✓ Attempts: {result['attempts']}")
    print(f"✓ Target: {result['target']} candidates")
    print(f"✓ Qualified found: {result['qualified_found']}")
    print(f"✓ Outreach sent: {result['outreach_sent']}")


def example_response_processing(swarm):
    """Example: Process candidate responses"""
    print_separator("EXAMPLE 4: Process Candidate Responses")

    # Simulate candidate responses
    responses = [
        {
            'candidate_id': 'cand_001',
            'message': 'Yes, I am very interested! When can we schedule a call?',
            'received_at': datetime.now()
        },
        {
            'candidate_id': 'cand_002',
            'message': 'Thanks for reaching out. Tell me more about the role.',
            'received_at': datetime.now()
        },
        {
            'candidate_id': 'cand_003',
            'message': 'Not interested at this time, thanks.',
            'received_at': datetime.now()
        }
    ]

    print(f"Processing {len(responses)} candidate responses...")
    result = swarm.process_candidate_responses(
        requisition_id='REQ-12345',
        responses=responses
    )

    print(f"\n✓ Responses processed: {result['responses_processed']}")

    analysis = result['analysis']
    print(f"\n📊 Response Analysis:")
    print(f"  - Interested: {analysis['interested']}")
    print(f"  - Not interested: {analysis['not_interested']}")
    print(f"  - Needs clarification: {analysis['needs_clarification']}")

    if result['actions_taken']:
        print(f"\n⚡ Actions Taken:")
        for action in result['actions_taken']:
            print(f"  - {action['action']}: {action['result']}")


def example_swarm_status(swarm):
    """Example: Get swarm status"""
    print_separator("EXAMPLE 5: Swarm Status")

    status = swarm.get_swarm_status()

    print("📈 Swarm Status:")
    print(f"  Active workflows: {status['active_workflows']}")
    print(f"  Completed workflows: {status['completed_workflows']}")

    print(f"\n🤖 Agent Status:")
    for agent_name, agent_status in status['agents'].items():
        state = agent_status['state']
        print(f"  {agent_name}:")
        print(f"    - Status: {state['status']}")
        print(f"    - Tasks completed: {state['tasks_completed']}")
        print(f"    - Tasks failed: {state['tasks_failed']}")


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("  LinkedIn Recruiter Swarm - Demo")
    print("=" * 80)
    print("\n  A multi-agent AI system for automated candidate sourcing\n")

    # Load environment
    load_dotenv()

    # Setup logging
    setup_logging()

    try:
        # Example 1: Full Pipeline
        swarm = example_full_pipeline()

        # Example 2: Parallel Search
        example_parallel_search(swarm)

        # Example 3: Adaptive Pipeline
        example_adaptive_pipeline(swarm)

        # Example 4: Response Processing
        example_response_processing(swarm)

        # Example 5: Swarm Status
        example_swarm_status(swarm)

        # Cleanup
        print_separator("Cleanup")
        print("Shutting down swarm...")
        swarm.shutdown()
        print("✓ Swarm shutdown complete")

        print_separator("Demo Complete!")
        print("Check the README.md for more usage examples and documentation.\n")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
