"""
Knowledge Graph implementation using Neo4j
"""

from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime


class KnowledgeGraph:
    """Neo4j knowledge graph for recruiter data"""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Initialize knowledge graph connection

        Args:
            uri: Neo4j connection URI (e.g., 'bolt://localhost:7687')
            user: Username
            password: Password
            database: Database name (default: 'neo4j')
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Connected to Neo4j at {uri}")

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def query(self, cypher: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute Cypher query

        Args:
            cypher: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher, parameters or {})
                records = [dict(record) for record in result]
                self.logger.debug(f"Query executed: {cypher[:100]}... returned {len(records)} records")
                return records
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            self.logger.error(f"Query: {cypher}")
            self.logger.error(f"Parameters: {parameters}")
            raise

    def create_candidate(self, candidate: Dict) -> str:
        """
        Create candidate node

        Args:
            candidate: Candidate properties dictionary

        Returns:
            Created candidate ID
        """
        cypher = """
        CREATE (c:Candidate $properties)
        RETURN c.candidate_id as id
        """
        result = self.query(cypher, {'properties': candidate})
        candidate_id = result[0]['id'] if result else None
        self.logger.info(f"Created candidate: {candidate_id}")
        return candidate_id

    def update_candidate(self, candidate_id: str, fields: Dict) -> None:
        """
        Update candidate properties

        Args:
            candidate_id: Candidate ID to update
            fields: Dictionary of fields to update
        """
        # Add last_updated timestamp
        fields['last_updated'] = datetime.now()

        cypher = """
        MATCH (c:Candidate {candidate_id: $candidate_id})
        SET c += $fields
        RETURN c.candidate_id as id
        """
        result = self.query(cypher, {
            'candidate_id': candidate_id,
            'fields': fields
        })

        if result:
            self.logger.info(f"Updated candidate: {candidate_id}")
        else:
            self.logger.warning(f"Candidate not found: {candidate_id}")

    def get_candidate(self, candidate_id: str) -> Optional[Dict]:
        """
        Get candidate by ID

        Args:
            candidate_id: Candidate ID

        Returns:
            Candidate properties or None
        """
        cypher = """
        MATCH (c:Candidate {candidate_id: $candidate_id})
        RETURN c
        """
        result = self.query(cypher, {'candidate_id': candidate_id})
        return result[0]['c'] if result else None

    def find_candidates_by_skills(self, skills: List[str], min_matches: int = 1) -> List[Dict]:
        """
        Find candidates with specific skills

        Args:
            skills: List of skill names
            min_matches: Minimum number of skills that must match

        Returns:
            List of matching candidates with skill match count
        """
        cypher = """
        MATCH (c:Candidate)-[:HAS_SKILL]->(s:Skill)
        WHERE s.name IN $skills
        WITH c, count(DISTINCT s) as skill_matches
        WHERE skill_matches >= $min_matches
        RETURN c as candidate, skill_matches
        ORDER BY skill_matches DESC
        """
        result = self.query(cypher, {
            'skills': skills,
            'min_matches': min_matches
        })
        return result

    def create_relationship(self, from_id: str, to_skill: str,
                          relationship_type: str, attributes: Dict) -> None:
        """
        Create relationship between candidate and skill

        Args:
            from_id: Candidate ID
            to_skill: Skill name
            relationship_type: Relationship type (should be 'HAS_SKILL')
            attributes: Relationship properties
        """
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
        self.logger.info(f"Created {relationship_type} relationship: {from_id} -> {to_skill}")

    def create_requisition(self, requisition: Dict) -> str:
        """
        Create requisition node

        Args:
            requisition: Requisition properties

        Returns:
            Created requisition ID
        """
        cypher = """
        CREATE (r:Requisition $properties)
        RETURN r.requisition_id as id
        """
        result = self.query(cypher, {'properties': requisition})
        req_id = result[0]['id'] if result else None
        self.logger.info(f"Created requisition: {req_id}")
        return req_id

    def link_requisition_skill(self, requisition_id: str, skill_name: str,
                              proficiency_level: str, required: bool = True) -> None:
        """
        Link requisition to required skill

        Args:
            requisition_id: Requisition ID
            skill_name: Skill name
            proficiency_level: Required proficiency level
            required: Whether skill is required (vs preferred)
        """
        cypher = """
        MATCH (r:Requisition {requisition_id: $req_id})
        MERGE (s:Skill {name: $skill_name})
        CREATE (r)-[:REQUIRES_SKILL {
            proficiency_level: $proficiency,
            required: $required
        }]->(s)
        """
        self.query(cypher, {
            'req_id': requisition_id,
            'skill_name': skill_name,
            'proficiency': proficiency_level,
            'required': required
        })

    def create_message(self, message: Dict) -> str:
        """
        Create message node

        Args:
            message: Message properties

        Returns:
            Created message ID
        """
        cypher = """
        CREATE (m:Message $properties)
        RETURN m.message_id as id
        """
        result = self.query(cypher, {'properties': message})
        msg_id = result[0]['id'] if result else None
        self.logger.info(f"Created message: {msg_id}")
        return msg_id

    def link_message_to_candidate(self, candidate_id: str, message_id: str,
                                  read: bool = False, responded: bool = False) -> None:
        """
        Link message to candidate

        Args:
            candidate_id: Candidate ID
            message_id: Message ID
            read: Whether message was read
            responded: Whether candidate responded
        """
        cypher = """
        MATCH (c:Candidate {candidate_id: $candidate_id})
        MATCH (m:Message {message_id: $message_id})
        CREATE (c)-[:RECEIVED {
            read: $read,
            responded: $responded
        }]->(m)
        """
        self.query(cypher, {
            'candidate_id': candidate_id,
            'message_id': message_id,
            'read': read,
            'responded': responded
        })

    def setup_schema(self) -> None:
        """
        Setup database schema (constraints and indexes)
        Call this once when initializing a new database
        """
        schema_queries = [
            # Constraints
            "CREATE CONSTRAINT candidate_id IF NOT EXISTS FOR (c:Candidate) REQUIRE c.candidate_id IS UNIQUE",
            "CREATE CONSTRAINT requisition_id IF NOT EXISTS FOR (r:Requisition) REQUIRE r.requisition_id IS UNIQUE",
            "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT message_id IF NOT EXISTS FOR (m:Message) REQUIRE m.message_id IS UNIQUE",

            # Indexes
            "CREATE INDEX candidate_email IF NOT EXISTS FOR (c:Candidate) ON (c.email)",
            "CREATE INDEX candidate_linkedin IF NOT EXISTS FOR (c:Candidate) ON (c.linkedin_url)",
            "CREATE INDEX requisition_status IF NOT EXISTS FOR (r:Requisition) ON (r.status)",
            "CREATE INDEX skill_category IF NOT EXISTS FOR (s:Skill) ON (s.category)",
        ]

        self.logger.info("Setting up database schema...")
        for query in schema_queries:
            try:
                self.query(query)
                self.logger.info(f"✓ {query[:50]}...")
            except Exception as e:
                self.logger.warning(f"Schema setup warning: {str(e)}")

        self.logger.info("Schema setup complete")

    def get_statistics(self) -> Dict[str, int]:
        """
        Get database statistics

        Returns:
            Dictionary with node and relationship counts
        """
        stats = {}

        # Count nodes by type
        node_types = ['Candidate', 'Requisition', 'Skill', 'Company', 'Message', 'Interview']
        for node_type in node_types:
            result = self.query(f"MATCH (n:{node_type}) RETURN count(n) as count")
            stats[f'{node_type.lower()}_count'] = result[0]['count'] if result else 0

        # Count total relationships
        result = self.query("MATCH ()-[r]->() RETURN count(r) as count")
        stats['relationship_count'] = result[0]['count'] if result else 0

        return stats

    def clear_database(self, confirm: str = "") -> None:
        """
        Clear all data from database (USE WITH CAUTION!)

        Args:
            confirm: Must pass "DELETE_ALL_DATA" to confirm
        """
        if confirm != "DELETE_ALL_DATA":
            raise ValueError("Must confirm deletion by passing 'DELETE_ALL_DATA'")

        self.logger.warning("CLEARING ALL DATA FROM DATABASE")
        self.query("MATCH (n) DETACH DELETE n")
        self.logger.info("Database cleared")
