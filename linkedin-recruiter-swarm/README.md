# LinkedIn Recruiter Swarm

A multi-agent AI system for automated candidate sourcing and recruitment on LinkedIn. The swarm coordinates specialized agents to handle search, scoring, outreach, and follow-up, creating an autonomous recruiting pipeline.

## Overview

The LinkedIn Recruiter Swarm is designed to automate and optimize the recruiting workflow by using multiple specialized AI agents that work together to:

- **Search** for candidates across LinkedIn using various strategies
- **Score and rank** candidates based on multi-dimensional criteria
- **Generate personalized outreach** messages at scale
- **Manage follow-ups** and process candidate responses
- **Coordinate workflows** across the entire recruiting pipeline

## Architecture

### Multi-Agent System

The swarm consists of four specialized agents:

```
┌─────────────────────────────────────────────────────────┐
│                  Swarm Coordinator                       │
│  (Orchestrates agents and manages workflows)            │
└─────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Search Agent  │ │Scoring Agent │ │Outreach Agent│ │Follow-up     │
│              │ │              │ │              │ │Agent         │
│- Targeted    │ │- Multi-dim   │ │- Personalized│ │- Response    │
│- Broad       │ │  scoring     │ │  messaging   │ │  processing  │
│- Passive     │ │- Ranking     │ │- Rate        │ │- Interview   │
│- Similar     │ │- Tier assign │ │  limiting    │ │  scheduling  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Agent Responsibilities

#### 1. Search Agent (`SearchAgent`)
- Executes LinkedIn searches with multiple strategies
- Supports targeted, broad, passive, and similar-profile searches
- Handles search parameter optimization
- Manages result filtering and deduplication

**Key Methods:**
- `process()` - Execute search tasks
- `_targeted_search()` - Precise requirement matching
- `_broad_search()` - Relaxed criteria for more results
- `_passive_candidate_search()` - Find employed high-performers
- `_similar_profile_search()` - Find candidates similar to top performers

#### 2. Scoring Agent (`ScoringAgent`)
- Multi-dimensional candidate evaluation
- Weighted scoring across skills, experience, titles, location
- Enhanced scoring with culture fit, trajectory, diversity
- Automated tier assignment and recommendations

**Scoring Components:**
- Skill Match (40%)
- Experience Match (30%)
- Title Similarity (15%)
- Location Match (10%)
- Activity Score (5%)
- Enhanced factors (culture fit, trajectory, education)

**Key Methods:**
- `process()` - Score candidates
- `_score_candidates()` - Execute scoring algorithm
- `_enhance_scoring()` - Add additional scoring dimensions
- `_determine_tier()` - Assign candidate tier

#### 3. Outreach Agent (`OutreachAgent`)
- Generate personalized outreach messages
- Manage contact constraints and rate limiting
- Support multiple outreach strategies
- Track message delivery

**Outreach Strategies:**
- Personalized (high-touch, individualized)
- Bulk (template-based, efficient)
- InMail (LinkedIn premium messaging)
- Connection Request (with custom note)

**Key Methods:**
- `process()` - Execute outreach tasks
- `_personalized_outreach()` - High-personalization messages
- `_build_personalization_context()` - Extract personalization hooks
- `_enhance_message()` - Add personalization to templates

#### 4. Follow-up Agent (`FollowUpAgent`)
- Manage follow-up communications
- Process and analyze candidate responses
- Schedule interviews automatically
- Track engagement metrics

**Key Methods:**
- `process()` - Execute follow-up tasks
- `_execute_follow_up()` - Send follow-up messages
- `_process_responses()` - Analyze candidate replies
- `_schedule_interviews()` - Coordinate interview scheduling

### Swarm Coordinator (`RecruiterSwarm`)

The coordinator orchestrates all agents to execute complex recruiting workflows:

**Core Workflows:**
- `run_full_pipeline()` - Complete end-to-end recruiting pipeline
- `run_parallel_search()` - Execute multiple search strategies concurrently
- `run_adaptive_pipeline()` - Adjust strategy based on results
- `run_continuous_sourcing()` - Ongoing candidate sourcing

## Installation

### Prerequisites

- Python 3.9+
- Neo4j database (for knowledge graph)
- LinkedIn API credentials

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd linkedin-recruiter-swarm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

4. Configure swarm settings:
```bash
# Edit config/swarm_config.yaml with your preferences
```

5. Setup Neo4j knowledge graph:
```bash
# Start Neo4j instance
# Create database named 'recruiter'
# Update NEO4J_* environment variables
```

## Usage

### Basic Usage

```python
from linkedin_recruiter_swarm import RecruiterSwarm, LinkedInHunterInterface

# Initialize components
kg = KnowledgeGraph(uri=NEO4J_URI, auth=(user, password))
linkedin_api = LinkedInAPI(credentials)
semantic_layer = SemanticLayer()

# Create interface
linkedin_interface = LinkedInHunterInterface(
    knowledge_graph=kg,
    semantic_layer=semantic_layer,
    linkedin_api=linkedin_api
)

# Initialize swarm
swarm = RecruiterSwarm(
    linkedin_interface=linkedin_interface,
    config=load_config('config/swarm_config.yaml')
)

# Run full pipeline
result = swarm.run_full_pipeline(
    requisition_id="REQ-12345",
    pipeline_config={
        'search_strategy': 'targeted',
        'max_search_results': 100,
        'outreach_count': 20
    }
)

print(f"Pipeline completed!")
print(f"Candidates found: {result['stages']['search']['candidates_found']}")
print(f"Messages sent: {result['stages']['outreach']['messages_sent']}")
```

### Advanced Usage

#### Parallel Search Strategies

```python
# Run multiple search strategies in parallel
result = swarm.run_parallel_search(
    requisition_id="REQ-12345",
    strategies=['targeted', 'broad', 'passive']
)

print(f"Total unique candidates: {result['total_candidates']}")
```

#### Adaptive Pipeline

```python
# Automatically adjust strategy to reach target
result = swarm.run_adaptive_pipeline(
    requisition_id="REQ-12345",
    target_candidate_count=50
)

print(f"Status: {result['status']}")
print(f"Qualified candidates: {result['qualified_found']}")
```

#### Processing Responses

```python
# Process candidate responses
responses = [
    {
        'candidate_id': 'cand_001',
        'message': 'Yes, I am interested in learning more!',
        'received_at': datetime.now()
    }
]

result = swarm.process_candidate_responses(
    requisition_id="REQ-12345",
    responses=responses
)

print(f"Interested: {result['analysis']['interested']}")
print(f"Interviews scheduled: {result['actions_taken']}")
```

#### Continuous Sourcing

```python
# Setup continuous sourcing campaign
result = swarm.run_continuous_sourcing(
    requisition_id="REQ-12345",
    duration_days=30
)

print(f"Continuous sourcing configured for {result['duration_days']} days")
```

## Configuration

### Swarm Configuration (`config/swarm_config.yaml`)

Key configuration sections:

- **swarm**: General swarm settings (workers, parallelism)
- **search_agent**: Search strategies and parameters
- **scoring_agent**: Scoring weights and thresholds
- **outreach_agent**: Messaging templates and rate limits
- **followup_agent**: Follow-up intervals and scheduling
- **pipeline**: Pipeline stage configuration
- **features**: Feature flags

### Environment Variables (`.env`)

Required variables:
- `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`: LinkedIn API credentials
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Knowledge graph database
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: LLM for message generation (optional)

## Workflow Examples

### Standard Recruiting Pipeline

```python
# 1. Define requisition in knowledge graph
requisition = {
    'requisition_id': 'REQ-12345',
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

# 2. Run pipeline
result = swarm.run_full_pipeline(
    requisition_id='REQ-12345',
    pipeline_config={
        'search_strategy': 'targeted',
        'max_search_results': 100,
        'outreach_count': 25,
        'outreach_strategy': 'personalized'
    }
)

# 3. Monitor results
print(f"Search: {result['stages']['search']}")
print(f"Scoring: {result['stages']['scoring']}")
print(f"Outreach: {result['stages']['outreach']}")
```

### High-Volume Recruiting

```python
# Use parallel search and bulk outreach
parallel_result = swarm.run_parallel_search(
    requisition_id='REQ-12345',
    strategies=['targeted', 'broad', 'similar_profile']
)

# Score all candidates
scoring_task = {
    'type': 'score',
    'candidates': parallel_result['candidates'],
    'requisition_id': 'REQ-12345'
}
scoring_result = swarm.agents['scoring'].execute_task(scoring_task)

# Bulk outreach to qualified candidates
outreach_task = {
    'type': 'outreach',
    'candidates': scoring_result['result']['scored_candidates'][:50],
    'requisition_id': 'REQ-12345',
    'strategy': 'bulk'
}
outreach_result = swarm.agents['outreach'].execute_task(outreach_task)
```

## API Reference

### RecruiterSwarm

#### Methods

**`run_full_pipeline(requisition_id: str, pipeline_config: Dict) -> Dict`**
- Execute complete recruiting pipeline
- Returns: Pipeline results with all stages

**`run_parallel_search(requisition_id: str, strategies: List[str]) -> Dict`**
- Run multiple search strategies in parallel
- Returns: Combined and deduplicated results

**`run_adaptive_pipeline(requisition_id: str, target_candidate_count: int) -> Dict`**
- Adaptive pipeline that adjusts strategy
- Returns: Results with adaptive strategy information

**`process_candidate_responses(requisition_id: str, responses: List[Dict]) -> Dict`**
- Process candidate responses and take actions
- Returns: Analysis and actions taken

**`get_swarm_status() -> Dict`**
- Get current swarm status
- Returns: Status of all agents and workflows

## Performance Considerations

### Parallelization

The swarm uses `ThreadPoolExecutor` for parallel execution:
- Concurrent search strategies
- Parallel scoring of candidates
- Batch outreach processing

Configure `max_workers` in config to control parallelism.

### Rate Limiting

Built-in rate limiting for LinkedIn API:
- Daily outreach limits
- Messages per hour throttling
- InMail credit management

### Caching

Search results can be cached to reduce API calls:
- Configure `enable_cache` and `cache_ttl_hours` in search agent config

## Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

## Best Practices

1. **Start with targeted search** - Use broad/passive only when needed
2. **Monitor score distributions** - Adjust weights if scores cluster
3. **Personalize top candidates** - Use bulk outreach for lower tiers
4. **Respect contact constraints** - Never override rate limits
5. **Process responses promptly** - Engage interested candidates quickly
6. **Iterate on messaging** - A/B test templates and track response rates
7. **Use adaptive pipeline** - Let the swarm find the right strategy

## Limitations

- Requires LinkedIn API access (partner or enterprise)
- Rate limits apply based on LinkedIn account type
- Neo4j database required for knowledge graph
- Response analysis is keyword-based (enhance with NLP for production)
- Message generation uses templates (integrate LLM for production)

## Future Enhancements

- [ ] Advanced NLP for response analysis
- [ ] LLM integration for dynamic message generation
- [ ] ML-based scoring model training
- [ ] Multi-channel outreach (email, Twitter, etc.)
- [ ] Automated interview calendar integration
- [ ] Real-time analytics dashboard
- [ ] A/B testing framework for messaging
- [ ] Candidate engagement scoring
- [ ] Predictive time-to-hire modeling

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check documentation in `/docs`
- Review examples in `/examples`

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                    LinkedIn Recruiter Swarm                    │
└───────────────────────────────────────────────────────────────┘

┌─────────────────────┐         ┌──────────────────────────────┐
│   LinkedIn API      │◄────────│   LinkedIn Hunter Interface  │
│   - Search          │         │   - Query building           │
│   - Profiles        │         │   - Data normalization       │
│   - Messaging       │         │   - Template management      │
└─────────────────────┘         └──────────────┬───────────────┘
                                               │
┌─────────────────────┐                        │
│  Knowledge Graph    │◄───────────────────────┤
│  (Neo4j)            │                        │
│  - Candidates       │                        │
│  - Requisitions     │                        ▼
│  - Relationships    │         ┌──────────────────────────────┐
│  - Skills           │         │   Recruiter Swarm            │
│  - Companies        │         │   (SwarmCoordinator)         │
└─────────────────────┘         └──────────────┬───────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
        ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
        │   Search Agent      │   │   Scoring Agent     │   │   Outreach Agent    │
        │                     │   │                     │   │                     │
        │   - Targeted        │   │   - Multi-dim       │   │   - Personalized    │
        │   - Broad           │   │   - Enhanced        │   │   - Bulk            │
        │   - Passive         │   │   - Tier assign     │   │   - InMail          │
        │   - Similar         │   │   - Ranking         │   │   - Rate limiting   │
        └─────────────────────┘   └─────────────────────┘   └─────────────────────┘
                                               │
                                               ▼
                                  ┌─────────────────────┐
                                  │   Follow-up Agent   │
                                  │                     │
                                  │   - Follow-ups      │
                                  │   - Response proc   │
                                  │   - Interview sched │
                                  │   - Engagement      │
                                  └─────────────────────┘

                    Data Flow:
                    1. Requisition → Search → Candidates
                    2. Candidates → Scoring → Ranked Candidates
                    3. Ranked → Outreach → Messages Sent
                    4. Responses → Follow-up → Interviews
```

## Example Output

```
Pipeline completed!

Stages:
  Search:
    - Strategy: targeted
    - Candidates found: 87

  Scoring:
    - Candidates scored: 87
    - Above threshold: 52
    - Score statistics:
      - Mean: 0.73
      - Median: 0.71
      - Tier distribution:
        - excellent: 8
        - strong: 15
        - good: 19
        - acceptable: 10

  Outreach:
    - Messages sent: 20
    - Skipped: 0
    - Failed: 0

  Follow-up:
    - Candidates tracked: 20
    - First follow-up in: 3 days

Duration: 45.3 seconds
Status: completed
```
