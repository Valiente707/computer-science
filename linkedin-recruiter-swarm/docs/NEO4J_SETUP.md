# Neo4j Knowledge Graph Setup Guide

Complete guide for setting up Neo4j as the knowledge graph backend for LinkedIn Recruiter Swarm.

## Table of Contents
1. [Installation](#installation)
2. [Database Setup](#database-setup)
3. [Schema Design](#schema-design)
4. [Sample Data](#sample-data)
5. [Connection Configuration](#connection-configuration)
6. [Integration with Swarm](#integration-with-swarm)
7. [Troubleshooting](#troubleshooting)

## Installation

### Option 1: Docker (Recommended)

**Step 1: Install Docker**
```bash
# Check if Docker is installed
docker --version

# If not installed, visit: https://docs.docker.com/get-docker/
```

**Step 2: Run Neo4j Container**
```bash
# Pull and run Neo4j
docker run \
    --name neo4j-recruiter \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/recruiter123 \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v neo4j_data:/data \
    -v neo4j_logs:/logs \
    -d \
    neo4j:latest

# Check if running
docker ps | grep neo4j
```

**Step 3: Access Neo4j Browser**
```
Open browser: http://localhost:7474
Username: neo4j
Password: recruiter123
```

### Option 2: Desktop Application

**Step 1: Download Neo4j Desktop**
- Visit: https://neo4j.com/download/
- Download Neo4j Desktop for your OS
- Install and launch

**Step 2: Create Database**
1. Click "New" → "Create a Local DBMS"
2. Name: "recruiter"
3. Password: "recruiter123"
4. Version: 5.x (latest)
5. Click "Create"

**Step 3: Start Database**
1. Click "Start" button
2. Wait for status to show "Active"
3. Click "Open" to access Neo4j Browser

### Option 3: Linux Server

**Step 1: Install Neo4j**
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Update and install
sudo apt-get update
sudo apt-get install neo4j

# Start Neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Check status
sudo systemctl status neo4j
```

**Step 2: Set Initial Password**
```bash
# Reset password
sudo neo4j-admin set-initial-password recruiter123

# Restart
sudo systemctl restart neo4j
```

## Database Setup

### Create Database

**Using Neo4j Browser:**
```cypher
// Create database (if using Enterprise Edition)
CREATE DATABASE recruiter;

// Switch to database
:use recruiter;
```

**Using Community Edition:**
```cypher
// Community edition only supports one database
// Use the default 'neo4j' database
:use neo4j;
```

### Install APOC Plugin (Optional but Recommended)

APOC provides utility functions for data manipulation.

**Docker:**
```bash
# Already included with -e NEO4J_PLUGINS='["apoc"]'
```

**Desktop:**
1. Click on database
2. Go to "Plugins" tab
3. Install "APOC"
4. Restart database

**Linux:**
```bash
# Download APOC
cd /var/lib/neo4j/plugins
sudo wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.13.0/apoc-5.13.0-core.jar

# Edit config
sudo nano /etc/neo4j/neo4j.conf

# Add this line:
dbms.security.procedures.unrestricted=apoc.*

# Restart
sudo systemctl restart neo4j
```

## Schema Design

### Node Types

The recruiter knowledge graph has the following node types:

```cypher
// 1. Candidate nodes
(:Candidate {
    candidate_id: String,
    source: String,
    first_name: String,
    last_name: String,
    email: String,
    linkedin_url: String,
    current_title: String,
    current_company: String,
    location: String,
    years_experience: Integer,
    data_quality_score: Float,
    profile_completeness: Float,
    last_updated: DateTime,
    source_confidence: Float,
    can_contact: Boolean,
    last_contacted: DateTime,
    contact_restrictions: Map
})

// 2. Requisition nodes
(:Requisition {
    requisition_id: String,
    job_title: String,
    department: String,
    location: String,
    min_years_experience: Integer,
    max_years_experience: Integer,
    status: String,
    created_at: DateTime,
    filled_at: DateTime
})

// 3. Skill nodes
(:Skill {
    skill_id: String,
    name: String,
    category: String,
    demand_score: Float
})

// 4. Company nodes
(:Company {
    company_id: String,
    name: String,
    industry: String,
    size: String,
    prestige_score: Float
})

// 5. Message nodes
(:Message {
    message_id: String,
    type: String,
    subject: String,
    body: String,
    sent_at: DateTime,
    template_id: String,
    personalization_score: Float
})

// 6. Interview nodes
(:Interview {
    interview_id: String,
    scheduled_time: DateTime,
    duration_minutes: Integer,
    type: String,
    status: String,
    interviewer: String
})
```

### Relationship Types

```cypher
// Candidate relationships
(:Candidate)-[:HAS_SKILL {
    proficiency_level: String,
    verified: Boolean,
    verification_source: String,
    years_experience: Integer
}]->(:Skill)

(:Candidate)-[:WORKED_AT {
    title: String,
    start_date: Date,
    end_date: Date,
    tenure_months: Integer
}]->(:Company)

(:Candidate)-[:APPLIED_TO {
    applied_at: DateTime,
    status: String,
    stage: String
}]->(:Requisition)

(:Candidate)-[:RECEIVED {
    read: Boolean,
    responded: Boolean,
    response_sentiment: String
}]->(:Message)

(:Candidate)-[:SCHEDULED_FOR]->(:Interview)

// Requisition relationships
(:Requisition)-[:REQUIRES_SKILL {
    proficiency_level: String,
    required: Boolean
}]->(:Skill)

(:Requisition)-[:SENT_MESSAGE]->(:Message)
```

### Create Schema

**Run in Neo4j Browser:**

```cypher
// Create constraints (enforce uniqueness)
CREATE CONSTRAINT candidate_id IF NOT EXISTS
FOR (c:Candidate) REQUIRE c.candidate_id IS UNIQUE;

CREATE CONSTRAINT requisition_id IF NOT EXISTS
FOR (r:Requisition) REQUIRE r.requisition_id IS UNIQUE;

CREATE CONSTRAINT skill_name IF NOT EXISTS
FOR (s:Skill) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT company_name IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT message_id IF NOT EXISTS
FOR (m:Message) REQUIRE m.message_id IS UNIQUE;

// Create indexes (improve query performance)
CREATE INDEX candidate_email IF NOT EXISTS
FOR (c:Candidate) ON (c.email);

CREATE INDEX candidate_linkedin IF NOT EXISTS
FOR (c:Candidate) ON (c.linkedin_url);

CREATE INDEX requisition_status IF NOT EXISTS
FOR (r:Requisition) ON (r.status);

CREATE INDEX skill_category IF NOT EXISTS
FOR (s:Skill) ON (s.category);
```

## Sample Data

### Load Sample Data

**Create sample requisition:**

```cypher
// Create a requisition
CREATE (r:Requisition {
    requisition_id: 'REQ-12345',
    job_title: 'Senior Software Engineer',
    department: 'Engineering',
    location: 'San Francisco, CA',
    min_years_experience: 5,
    max_years_experience: 10,
    status: 'open',
    created_at: datetime()
})

// Create required skills
CREATE (s1:Skill {name: 'Python', category: 'Programming Language', demand_score: 0.95})
CREATE (s2:Skill {name: 'Machine Learning', category: 'Technology', demand_score: 0.90})
CREATE (s3:Skill {name: 'AWS', category: 'Cloud Platform', demand_score: 0.85})
CREATE (s4:Skill {name: 'Docker', category: 'DevOps', demand_score: 0.80})
CREATE (s5:Skill {name: 'Kubernetes', category: 'DevOps', demand_score: 0.75})

// Link requisition to required skills
MATCH (r:Requisition {requisition_id: 'REQ-12345'})
MATCH (s:Skill) WHERE s.name IN ['Python', 'Machine Learning', 'AWS']
CREATE (r)-[:REQUIRES_SKILL {
    proficiency_level: 'advanced',
    required: true
}]->(s)

RETURN r, s;
```

**Create sample candidates:**

```cypher
// Create candidates
CREATE (c1:Candidate {
    candidate_id: 'CAND-001',
    source: 'linkedin_sourced',
    first_name: 'Alice',
    last_name: 'Johnson',
    email: 'alice.johnson@example.com',
    linkedin_url: 'https://linkedin.com/in/alicejohnson',
    current_title: 'Senior Software Engineer',
    current_company: 'Tech Corp',
    location: 'San Francisco, CA',
    years_experience: 7,
    data_quality_score: 0.85,
    profile_completeness: 0.90,
    last_updated: datetime(),
    source_confidence: 0.80,
    can_contact: true
})

CREATE (c2:Candidate {
    candidate_id: 'CAND-002',
    source: 'linkedin_sourced',
    first_name: 'Bob',
    last_name: 'Smith',
    email: 'bob.smith@example.com',
    linkedin_url: 'https://linkedin.com/in/bobsmith',
    current_title: 'Software Engineer',
    current_company: 'Startup Inc',
    location: 'San Francisco, CA',
    years_experience: 5,
    data_quality_score: 0.75,
    profile_completeness: 0.85,
    last_updated: datetime(),
    source_confidence: 0.75,
    can_contact: true
})

// Create companies
CREATE (comp1:Company {name: 'Tech Corp', industry: 'Technology', size: 'large', prestige_score: 0.85})
CREATE (comp2:Company {name: 'Startup Inc', industry: 'Technology', size: 'small', prestige_score: 0.65})

// Link candidates to skills
MATCH (c:Candidate {candidate_id: 'CAND-001'})
MATCH (s:Skill) WHERE s.name IN ['Python', 'Machine Learning', 'AWS', 'Docker']
CREATE (c)-[:HAS_SKILL {
    proficiency_level: 'expert',
    verified: false,
    verification_source: 'LINKEDIN_PROFILE',
    years_experience: 5
}]->(s)

MATCH (c:Candidate {candidate_id: 'CAND-002'})
MATCH (s:Skill) WHERE s.name IN ['Python', 'AWS', 'Docker']
CREATE (c)-[:HAS_SKILL {
    proficiency_level: 'advanced',
    verified: false,
    verification_source: 'LINKEDIN_PROFILE',
    years_experience: 3
}]->(s)

// Link candidates to companies
MATCH (c:Candidate {candidate_id: 'CAND-001'}), (comp:Company {name: 'Tech Corp'})
CREATE (c)-[:WORKED_AT {
    title: 'Senior Software Engineer',
    start_date: date('2020-01-01'),
    tenure_months: 48
}]->(comp)

MATCH (c:Candidate {candidate_id: 'CAND-002'}), (comp:Company {name: 'Startup Inc'})
CREATE (c)-[:WORKED_AT {
    title: 'Software Engineer',
    start_date: date('2021-06-01'),
    tenure_months: 30
}]->(comp)

RETURN 'Sample data created successfully' as status;
```

### Verify Data

```cypher
// Count nodes
MATCH (c:Candidate) RETURN count(c) as candidates;
MATCH (r:Requisition) RETURN count(r) as requisitions;
MATCH (s:Skill) RETURN count(s) as skills;

// View relationships
MATCH (c:Candidate)-[r:HAS_SKILL]->(s:Skill)
RETURN c.first_name, c.last_name, type(r) as relationship, s.name
LIMIT 10;

// View requisition with skills
MATCH (r:Requisition {requisition_id: 'REQ-12345'})-[:REQUIRES_SKILL]->(s:Skill)
RETURN r.job_title, collect(s.name) as required_skills;
```

## Connection Configuration

### Update Environment Variables

Edit `.env` file:

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=recruiter123
NEO4J_DATABASE=neo4j  # or 'recruiter' if using Enterprise
```

### Test Connection

Create `test_neo4j.py`:

```python
#!/usr/bin/env python3
"""Test Neo4j connection"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Connection details
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'recruiter123')
database = os.getenv('NEO4J_DATABASE', 'neo4j')

print(f"Testing connection to Neo4j...")
print(f"URI: {uri}")
print(f"User: {user}")
print(f"Database: {database}")

try:
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Test connection
    with driver.session(database=database) as session:
        result = session.run("RETURN 'Connection successful!' as message")
        record = result.single()
        print(f"\n✓ {record['message']}")

        # Count nodes
        result = session.run("MATCH (n) RETURN count(n) as node_count")
        count = result.single()['node_count']
        print(f"✓ Total nodes in database: {count}")

        # Count candidates
        result = session.run("MATCH (c:Candidate) RETURN count(c) as count")
        candidates = result.single()['count']
        print(f"✓ Candidates: {candidates}")

        # Count requisitions
        result = session.run("MATCH (r:Requisition) RETURN count(r) as count")
        reqs = result.single()['count']
        print(f"✓ Requisitions: {reqs}")

    driver.close()
    print("\n✓ Connection test passed!")

except Exception as e:
    print(f"\n❌ Connection failed: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Make sure Neo4j is running")
    print("2. Check URI, username, and password in .env")
    print("3. Verify firewall allows port 7687")
```

Run test:
```bash
cd linkedin-recruiter-swarm
python test_neo4j.py
```

## Integration with Swarm

### Create KnowledgeGraph Class

Create `src/knowledge_graph.py`:

```python
"""
Knowledge Graph implementation using Neo4j
"""

from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import logging


class KnowledgeGraph:
    """Neo4j knowledge graph for recruiter data"""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Initialize knowledge graph connection

        Args:
            uri: Neo4j connection URI
            user: Username
            password: Password
            database: Database name
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.logger = logging.getLogger(__name__)

    def close(self):
        """Close database connection"""
        self.driver.close()

    def query(self, cypher: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute Cypher query

        Args:
            cypher: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, parameters or {})
            return [dict(record) for record in result]

    def create_candidate(self, candidate: Dict) -> None:
        """Create candidate node"""
        cypher = """
        CREATE (c:Candidate $properties)
        RETURN c
        """
        self.query(cypher, {'properties': candidate})
        self.logger.info(f"Created candidate: {candidate.get('candidate_id')}")

    def update_candidate(self, candidate_id: str, fields: Dict) -> None:
        """Update candidate properties"""
        cypher = """
        MATCH (c:Candidate {candidate_id: $candidate_id})
        SET c += $fields
        RETURN c
        """
        self.query(cypher, {
            'candidate_id': candidate_id,
            'fields': fields
        })
        self.logger.info(f"Updated candidate: {candidate_id}")

    def create_relationship(self, from_id: str, to_skill: str,
                          relationship_type: str, attributes: Dict) -> None:
        """Create relationship between candidate and skill"""
        cypher = """
        MATCH (c:Candidate {candidate_id: $from_id})
        MERGE (s:Skill {name: $skill_name})
        CREATE (c)-[r:HAS_SKILL $attributes]->(s)
        RETURN r
        """
        self.query(cypher, {
            'from_id': from_id,
            'skill_name': to_skill,
            'attributes': attributes
        })
```

### Update LinkedInHunterInterface

Modify `src/linkedin_hunter_interface.py` to use real KnowledgeGraph:

```python
# At the top of the file
from .knowledge_graph import KnowledgeGraph
```

### Initialize in main.py

Update `main.py`:

```python
from src.knowledge_graph import KnowledgeGraph
import os

# Initialize real knowledge graph
kg = KnowledgeGraph(
    uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    user=os.getenv('NEO4J_USER', 'neo4j'),
    password=os.getenv('NEO4J_PASSWORD', 'recruiter123'),
    database=os.getenv('NEO4J_DATABASE', 'neo4j')
)

# Use with interface
linkedin_interface = LinkedInHunterInterface(
    knowledge_graph=kg,  # Real KG instead of mock
    semantic_layer=semantic,
    linkedin_api=linkedin_api
)
```

## Troubleshooting

### Connection Issues

**Error: "Failed to establish connection"**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs neo4j-recruiter

# Test connectivity
telnet localhost 7687
```

**Error: "Authentication failed"**
```bash
# Reset password
docker exec -it neo4j-recruiter neo4j-admin set-initial-password newpassword

# Update .env file with new password
```

### Performance Issues

**Slow queries:**
```cypher
// Create indexes on frequently queried properties
CREATE INDEX candidate_name IF NOT EXISTS
FOR (c:Candidate) ON (c.last_name);

CREATE INDEX skill_name_idx IF NOT EXISTS
FOR (s:Skill) ON (s.name);

// Analyze query performance
EXPLAIN MATCH (c:Candidate)-[:HAS_SKILL]->(s:Skill)
WHERE s.name = 'Python'
RETURN c;
```

### Memory Issues

Edit Neo4j config:
```bash
# Docker
docker run \
    -e NEO4J_dbms_memory_heap_initial__size=1G \
    -e NEO4J_dbms_memory_heap_max__size=2G \
    ...

# Linux: Edit /etc/neo4j/neo4j.conf
dbms.memory.heap.initial_size=1G
dbms.memory.heap.max_size=2G
```

## Next Steps

1. **Expand Schema**: Add more node types (Education, Certifications, etc.)
2. **Import Real Data**: Load your existing candidate database
3. **Setup Backups**: Configure automated backups
4. **Monitoring**: Setup Neo4j monitoring dashboard
5. **Security**: Configure SSL/TLS for production

## Useful Queries

### Find candidates for requisition
```cypher
MATCH (r:Requisition {requisition_id: 'REQ-12345'})-[:REQUIRES_SKILL]->(required:Skill)
MATCH (c:Candidate)-[:HAS_SKILL]->(required)
WITH c, count(DISTINCT required) as skill_matches
RETURN c.candidate_id, c.first_name, c.last_name, skill_matches
ORDER BY skill_matches DESC;
```

### Analyze skill demand
```cypher
MATCH (c:Candidate)-[:HAS_SKILL]->(s:Skill)
RETURN s.name, count(c) as candidate_count
ORDER BY candidate_count DESC
LIMIT 10;
```

### Find candidates by company
```cypher
MATCH (c:Candidate)-[:WORKED_AT]->(comp:Company {name: 'Tech Corp'})
RETURN c.first_name, c.last_name, c.current_title;
```

## Resources

- **Neo4j Documentation**: https://neo4j.com/docs/
- **Cypher Manual**: https://neo4j.com/docs/cypher-manual/current/
- **Python Driver**: https://neo4j.com/docs/python-manual/current/
- **APOC Documentation**: https://neo4j.com/labs/apoc/

Need help? Check the [Neo4j Community Forum](https://community.neo4j.com/)
