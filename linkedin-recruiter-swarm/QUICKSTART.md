# Quick Start Guide

Get started with the LinkedIn Recruiter Swarm in 5 minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd linkedin-recruiter-swarm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# (For demo, you can leave defaults)
nano .env
```

## Run Demo

```bash
# Run the demo with mock data
python main.py
```

Expected output:
```
================================================================================
  LinkedIn Recruiter Swarm - Demo
================================================================================

  A multi-agent AI system for automated candidate sourcing

================================================================================
  EXAMPLE 1: Full Recruiting Pipeline
================================================================================

Running full recruiting pipeline...

✓ Pipeline Status: completed
✓ Duration: 2.3 seconds

📊 Pipeline Results:
  Search:
    - Strategy: targeted
    - Candidates found: 50
  Scoring:
    - Candidates scored: 50
    - Above threshold: 35
    - Mean score: 0.68
  Outreach:
    - Messages sent: 10
    - Skipped: 0
```

## Basic Usage

```python
from src import RecruiterSwarm, LinkedInHunterInterface

# Initialize components (use your real implementations)
linkedin_interface = LinkedInHunterInterface(
    knowledge_graph=your_kg,
    semantic_layer=your_semantic,
    linkedin_api=your_api
)

# Create swarm
swarm = RecruiterSwarm(linkedin_interface=linkedin_interface)

# Run pipeline
result = swarm.run_full_pipeline(
    requisition_id='REQ-12345',
    pipeline_config={
        'search_strategy': 'targeted',
        'outreach_count': 20
    }
)

print(f"Found {result['stages']['search']['candidates_found']} candidates")
print(f"Sent {result['stages']['outreach']['messages_sent']} messages")
```

## Key Concepts

### 1. Agents

The swarm consists of 4 specialized agents:

- **SearchAgent**: Finds candidates on LinkedIn
- **ScoringAgent**: Evaluates and ranks candidates
- **OutreachAgent**: Sends personalized messages
- **FollowUpAgent**: Manages follow-ups and responses

### 2. Workflows

Three main workflow types:

```python
# Full pipeline (all stages)
swarm.run_full_pipeline(requisition_id)

# Parallel search (multiple strategies)
swarm.run_parallel_search(requisition_id, strategies)

# Adaptive pipeline (adjusts strategy)
swarm.run_adaptive_pipeline(requisition_id, target_count)
```

### 3. Configuration

Edit `config/swarm_config.yaml` to customize:

```yaml
scoring_agent:
  min_threshold: 0.6  # Minimum score to consider
  scoring_weights:
    skill_match: 0.40
    experience_match: 0.30

outreach_agent:
  daily_outreach_limit: 50
  default_strategy: "personalized"
```

## Next Steps

1. **Integrate with real LinkedIn API**
   - Get LinkedIn API credentials
   - Replace `MockLinkedInAPI` with real implementation

2. **Setup Neo4j database**
   - Install Neo4j
   - Create 'recruiter' database
   - Update connection settings in `.env`

3. **Customize scoring**
   - Adjust weights in `config/swarm_config.yaml`
   - Add custom scoring criteria

4. **Create message templates**
   - Design templates for your company
   - Add personalization hooks

5. **Deploy to production**
   - Setup monitoring
   - Configure rate limits
   - Enable logging

## Troubleshooting

### Import errors

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Config not found

```bash
# Check that config directory exists
ls -la config/

# Config file should exist
ls -la config/swarm_config.yaml
```

### Mock data only

The demo uses mock data by default. To use real LinkedIn data:

1. Get LinkedIn API credentials
2. Implement real `LinkedInAPI` class
3. Replace mocks in `main.py`

## Resources

- Full documentation: [README.md](README.md)
- Configuration reference: [config/swarm_config.yaml](config/swarm_config.yaml)
- Example code: [main.py](main.py)
- Tests: [tests/test_swarm.py](tests/test_swarm.py)

## Getting Help

- Check the [README](README.md) for detailed documentation
- Review [examples in main.py](main.py)
- Open an issue on GitHub

## What's Next?

Explore the full documentation to learn about:
- Advanced search strategies
- Custom scoring models
- Response processing
- Interview scheduling
- Analytics and monitoring

Happy recruiting! 🚀
