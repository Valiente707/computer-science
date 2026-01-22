"""
Tests for LinkedIn Recruiter Swarm
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock


class TestSearchAgent:
    """Test SearchAgent functionality"""

    def test_search_agent_initialization(self):
        """Test that SearchAgent initializes correctly"""
        from src.agents import SearchAgent

        mock_interface = Mock()
        agent = SearchAgent(
            agent_id='test_search',
            linkedin_interface=mock_interface
        )

        assert agent.agent_id == 'test_search'
        assert agent.linkedin == mock_interface
        assert agent.state['status'] == 'idle'

    def test_search_agent_can_handle_search_task(self):
        """Test that SearchAgent can handle search tasks"""
        from src.agents import SearchAgent

        mock_interface = Mock()
        agent = SearchAgent(agent_id='test', linkedin_interface=mock_interface)

        task = {'type': 'search', 'requisition_id': 'REQ-123'}
        assert agent.can_handle(task) is True

        task = {'type': 'score', 'requisition_id': 'REQ-123'}
        assert agent.can_handle(task) is False


class TestScoringAgent:
    """Test ScoringAgent functionality"""

    def test_scoring_agent_initialization(self):
        """Test that ScoringAgent initializes correctly"""
        from src.agents import ScoringAgent

        mock_interface = Mock()
        agent = ScoringAgent(
            agent_id='test_scoring',
            linkedin_interface=mock_interface
        )

        assert agent.agent_id == 'test_scoring'
        assert agent.min_threshold == 0.6

    def test_tier_determination(self):
        """Test tier assignment logic"""
        from src.agents import ScoringAgent

        mock_interface = Mock()
        agent = ScoringAgent(agent_id='test', linkedin_interface=mock_interface)

        assert agent._determine_tier(0.95) == 'excellent'
        assert agent._determine_tier(0.85) == 'strong'
        assert agent._determine_tier(0.75) == 'good'
        assert agent._determine_tier(0.65) == 'acceptable'
        assert agent._determine_tier(0.55) == 'below_threshold'


class TestOutreachAgent:
    """Test OutreachAgent functionality"""

    def test_outreach_agent_initialization(self):
        """Test that OutreachAgent initializes correctly"""
        from src.agents import OutreachAgent

        mock_interface = Mock()
        agent = OutreachAgent(
            agent_id='test_outreach',
            linkedin_interface=mock_interface,
            config={'daily_outreach_limit': 100}
        )

        assert agent.agent_id == 'test_outreach'
        assert agent.daily_limit == 100
        assert agent.messages_sent_today == 0

    def test_daily_limit_enforcement(self):
        """Test that daily limits are enforced"""
        from src.agents import OutreachAgent

        mock_interface = Mock()
        mock_interface.respect_contact_constraints = Mock(return_value={'allowed': True})
        mock_interface.generate_outreach_message = Mock(return_value={
            'subject': 'Test',
            'body': 'Test message'
        })
        mock_interface.get_requisition_profile = Mock(return_value={'job_title': 'Engineer'})

        agent = OutreachAgent(
            agent_id='test',
            linkedin_interface=mock_interface,
            config={'daily_outreach_limit': 2}
        )

        # Simulate sending messages
        agent.messages_sent_today = 2

        candidates = [
            {'candidate_id': 'c1', 'profile': {'first_name': 'Test'}},
            {'candidate_id': 'c2', 'profile': {'first_name': 'Test2'}}
        ]

        result = agent._execute_outreach(candidates, 'REQ-123', 'personalized')

        # Should skip both due to limit
        assert result['skipped'] == 2


class TestFollowUpAgent:
    """Test FollowUpAgent functionality"""

    def test_followup_agent_initialization(self):
        """Test that FollowUpAgent initializes correctly"""
        from src.agents import FollowUpAgent

        mock_interface = Mock()
        agent = FollowUpAgent(
            agent_id='test_followup',
            linkedin_interface=mock_interface
        )

        assert agent.agent_id == 'test_followup'
        assert agent.max_follow_ups == 3
        assert agent.follow_up_intervals['first'] == 3

    def test_should_follow_up_logic(self):
        """Test follow-up decision logic"""
        from src.agents import FollowUpAgent

        mock_interface = Mock()
        agent = FollowUpAgent(agent_id='test', linkedin_interface=mock_interface)

        # No history - should not follow up
        decision = agent._should_follow_up([])
        assert decision['should_follow_up'] is False

        # Max attempts reached
        history = [{'sent_at': datetime.now()} for _ in range(3)]
        decision = agent._should_follow_up(history)
        assert decision['should_follow_up'] is False
        assert decision.get('max_attempts') is True


class TestRecruiterSwarm:
    """Test RecruiterSwarm coordination"""

    def test_swarm_initialization(self):
        """Test that swarm initializes all agents"""
        from src import RecruiterSwarm

        mock_interface = Mock()
        swarm = RecruiterSwarm(
            linkedin_interface=mock_interface,
            config={'max_workers': 2}
        )

        assert len(swarm.agents) == 4
        assert 'search' in swarm.agents
        assert 'scoring' in swarm.agents
        assert 'outreach' in swarm.agents
        assert 'followup' in swarm.agents

    def test_top_candidate_selection(self):
        """Test selecting top candidates"""
        from src import RecruiterSwarm

        mock_interface = Mock()
        swarm = RecruiterSwarm(linkedin_interface=mock_interface)

        scored_candidates = [
            {'score': 0.9, 'candidate': {'id': '1'}},
            {'score': 0.85, 'candidate': {'id': '2'}},
            {'score': 0.8, 'candidate': {'id': '3'}},
            {'score': 0.75, 'candidate': {'id': '4'}},
        ]

        top = swarm._select_top_candidates(scored_candidates, 2)
        assert len(top) == 2
        assert top[0]['score'] == 0.9
        assert top[1]['score'] == 0.85

    def test_candidate_deduplication(self):
        """Test deduplication of candidates"""
        from src import RecruiterSwarm

        mock_interface = Mock()
        swarm = RecruiterSwarm(linkedin_interface=mock_interface)

        candidates = [
            {'public_url': 'https://linkedin.com/in/user1', 'name': 'User 1'},
            {'public_url': 'https://linkedin.com/in/user2', 'name': 'User 2'},
            {'public_url': 'https://linkedin.com/in/user1', 'name': 'User 1 Duplicate'},
            {'public_url': 'https://linkedin.com/in/user3', 'name': 'User 3'},
        ]

        unique = swarm._deduplicate_candidates(candidates)
        assert len(unique) == 3


class TestLinkedInHunterInterface:
    """Test LinkedInHunterInterface"""

    def test_interface_initialization(self):
        """Test interface initialization"""
        from src import LinkedInHunterInterface

        mock_kg = Mock()
        mock_semantic = Mock()
        mock_linkedin = Mock()

        interface = LinkedInHunterInterface(
            knowledge_graph=mock_kg,
            semantic_layer=mock_semantic,
            linkedin_api=mock_linkedin
        )

        assert interface.kg == mock_kg
        assert interface.semantic == mock_semantic
        assert interface.linkedin == mock_linkedin

    def test_title_similarity_calculation(self):
        """Test job title similarity"""
        from src import LinkedInHunterInterface

        mock_kg = Mock()
        mock_semantic = Mock()
        mock_linkedin = Mock()

        interface = LinkedInHunterInterface(mock_kg, mock_semantic, mock_linkedin)

        # Exact match
        sim = interface.calculate_title_similarity(
            'Software Engineer',
            'Software Engineer'
        )
        assert sim == 1.0

        # Partial overlap
        sim = interface.calculate_title_similarity(
            'Senior Software Engineer',
            'Software Engineer'
        )
        assert 0 < sim < 1.0

        # No overlap
        sim = interface.calculate_title_similarity(
            'Product Manager',
            'Software Engineer'
        )
        assert sim == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
