#!/usr/bin/env python3
"""
Setup Neo4j database schema and sample data
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from datetime import datetime, date
import uuid

# Load environment
load_dotenv()

try:
    from src.knowledge_graph import KnowledgeGraph
except ImportError:
    print("❌ Cannot import KnowledgeGraph. Make sure you're in the correct directory.")
    sys.exit(1)


def setup_schema(kg: KnowledgeGraph):
    """Setup database schema"""
    print("\n" + "=" * 80)
    print("  Setting up Neo4j Schema")
    print("=" * 80)

    try:
        kg.setup_schema()
        print("\n✓ Schema setup complete")
        return True
    except Exception as e:
        print(f"\n❌ Schema setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def load_sample_data(kg: KnowledgeGraph):
    """Load sample data into database"""
    print("\n" + "=" * 80)
    print("  Loading Sample Data")
    print("=" * 80)

    try:
        # Create sample skills
        print("\n1. Creating skills...")
        skills = [
            {'name': 'Python', 'category': 'Programming Language', 'demand_score': 0.95},
            {'name': 'Machine Learning', 'category': 'Technology', 'demand_score': 0.90},
            {'name': 'AWS', 'category': 'Cloud Platform', 'demand_score': 0.85},
            {'name': 'Docker', 'category': 'DevOps', 'demand_score': 0.80},
            {'name': 'Kubernetes', 'category': 'DevOps', 'demand_score': 0.75},
            {'name': 'React', 'category': 'Frontend Framework', 'demand_score': 0.85},
            {'name': 'Node.js', 'category': 'Backend Framework', 'demand_score': 0.80},
            {'name': 'PostgreSQL', 'category': 'Database', 'demand_score': 0.75},
        ]

        for skill in skills:
            kg.query("""
                MERGE (s:Skill {name: $name})
                SET s.category = $category,
                    s.demand_score = $demand_score
            """, skill)

        print(f"  ✓ Created {len(skills)} skills")

        # Create sample companies
        print("\n2. Creating companies...")
        companies = [
            {'name': 'Tech Corp', 'industry': 'Technology', 'size': 'large', 'prestige_score': 0.85},
            {'name': 'Startup Inc', 'industry': 'Technology', 'size': 'small', 'prestige_score': 0.65},
            {'name': 'Enterprise Co', 'industry': 'Enterprise Software', 'size': 'large', 'prestige_score': 0.80},
            {'name': 'AI Labs', 'industry': 'Artificial Intelligence', 'size': 'medium', 'prestige_score': 0.90},
        ]

        for company in companies:
            kg.query("""
                MERGE (c:Company {name: $name})
                SET c.industry = $industry,
                    c.size = $size,
                    c.prestige_score = $prestige_score
            """, company)

        print(f"  ✓ Created {len(companies)} companies")

        # Create sample requisition
        print("\n3. Creating requisition...")
        requisition = {
            'requisition_id': 'REQ-12345',
            'job_title': 'Senior Software Engineer',
            'department': 'Engineering',
            'location': 'San Francisco, CA',
            'min_years_experience': 5,
            'max_years_experience': 10,
            'status': 'open',
            'created_at': datetime.now()
        }

        kg.create_requisition(requisition)
        print(f"  ✓ Created requisition: {requisition['requisition_id']}")

        # Link requisition to required skills
        print("\n4. Linking requisition to skills...")
        required_skills = [
            ('Python', 'expert'),
            ('Machine Learning', 'advanced'),
            ('AWS', 'intermediate'),
        ]

        for skill_name, proficiency in required_skills:
            kg.link_requisition_skill(
                requisition_id='REQ-12345',
                skill_name=skill_name,
                proficiency_level=proficiency,
                required=True
            )

        print(f"  ✓ Linked {len(required_skills)} required skills")

        # Create sample candidates
        print("\n5. Creating candidates...")
        candidates = [
            {
                'candidate_id': f'CAND-{str(uuid.uuid4())[:8]}',
                'source': 'linkedin_sourced',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@example.com',
                'linkedin_url': 'https://linkedin.com/in/alicejohnson',
                'current_title': 'Senior Software Engineer',
                'current_company': 'Tech Corp',
                'location': 'San Francisco, CA',
                'years_experience': 7,
                'data_quality_score': 0.85,
                'profile_completeness': 0.90,
                'last_updated': datetime.now(),
                'source_confidence': 0.80,
                'can_contact': True
            },
            {
                'candidate_id': f'CAND-{str(uuid.uuid4())[:8]}',
                'source': 'linkedin_sourced',
                'first_name': 'Bob',
                'last_name': 'Smith',
                'email': 'bob.smith@example.com',
                'linkedin_url': 'https://linkedin.com/in/bobsmith',
                'current_title': 'Software Engineer',
                'current_company': 'Startup Inc',
                'location': 'San Francisco, CA',
                'years_experience': 5,
                'data_quality_score': 0.75,
                'profile_completeness': 0.85,
                'last_updated': datetime.now(),
                'source_confidence': 0.75,
                'can_contact': True
            },
            {
                'candidate_id': f'CAND-{str(uuid.uuid4())[:8]}',
                'source': 'linkedin_sourced',
                'first_name': 'Carol',
                'last_name': 'Williams',
                'email': 'carol.w@example.com',
                'linkedin_url': 'https://linkedin.com/in/carolwilliams',
                'current_title': 'ML Engineer',
                'current_company': 'AI Labs',
                'location': 'New York, NY',
                'years_experience': 6,
                'data_quality_score': 0.90,
                'profile_completeness': 0.95,
                'last_updated': datetime.now(),
                'source_confidence': 0.85,
                'can_contact': True
            },
        ]

        candidate_ids = []
        for candidate in candidates:
            cand_id = kg.create_candidate(candidate)
            candidate_ids.append((cand_id, candidate['current_company']))

        print(f"  ✓ Created {len(candidates)} candidates")

        # Link candidates to skills
        print("\n6. Linking candidates to skills...")
        candidate_skills = {
            0: ['Python', 'Machine Learning', 'AWS', 'Docker'],  # Alice
            1: ['Python', 'AWS', 'Docker', 'React'],             # Bob
            2: ['Python', 'Machine Learning', 'Kubernetes'],     # Carol
        }

        skill_count = 0
        for idx, skills in candidate_skills.items():
            for skill in skills:
                kg.create_relationship(
                    from_id=candidate_ids[idx][0],
                    to_skill=skill,
                    relationship_type='HAS_SKILL',
                    attributes={
                        'proficiency_level': 'advanced',
                        'verified': False,
                        'verification_source': 'LINKEDIN_PROFILE',
                        'years_experience': 3
                    }
                )
                skill_count += 1

        print(f"  ✓ Created {skill_count} candidate-skill relationships")

        # Link candidates to companies
        print("\n7. Linking candidates to companies...")
        for cand_id, company_name in candidate_ids:
            kg.query("""
                MATCH (c:Candidate {candidate_id: $cand_id})
                MATCH (comp:Company {name: $company_name})
                CREATE (c)-[:WORKED_AT {
                    title: c.current_title,
                    start_date: date('2020-01-01'),
                    tenure_months: 36
                }]->(comp)
            """, {'cand_id': cand_id, 'company_name': company_name})

        print(f"  ✓ Created {len(candidate_ids)} candidate-company relationships")

        print("\n✓ Sample data loaded successfully")
        return True

    except Exception as e:
        print(f"\n❌ Failed to load sample data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_statistics(kg: KnowledgeGraph):
    """Show database statistics"""
    print("\n" + "=" * 80)
    print("  Database Statistics")
    print("=" * 80)

    stats = kg.get_statistics()

    print(f"\nNodes:")
    print(f"  Candidates: {stats.get('candidate_count', 0)}")
    print(f"  Requisitions: {stats.get('requisition_count', 0)}")
    print(f"  Skills: {stats.get('skill_count', 0)}")
    print(f"  Companies: {stats.get('company_count', 0)}")
    print(f"  Messages: {stats.get('message_count', 0)}")
    print(f"  Interviews: {stats.get('interview_count', 0)}")

    print(f"\nRelationships:")
    print(f"  Total: {stats.get('relationship_count', 0)}")

    # Show some sample queries
    print("\nSample Data Preview:")

    # Show candidates
    candidates = kg.query("""
        MATCH (c:Candidate)
        RETURN c.candidate_id as id, c.first_name as first_name,
               c.last_name as last_name, c.current_title as title
        LIMIT 5
    """)

    if candidates:
        print("\n  Candidates:")
        for c in candidates:
            print(f"    - {c['first_name']} {c['last_name']} ({c['title']})")

    # Show skills
    skills = kg.query("""
        MATCH (s:Skill)
        RETURN s.name as name, s.category as category
        ORDER BY s.demand_score DESC
        LIMIT 5
    """)

    if skills:
        print("\n  Top Skills:")
        for s in skills:
            print(f"    - {s['name']} ({s['category']})")

    # Show requisitions
    reqs = kg.query("""
        MATCH (r:Requisition)
        RETURN r.requisition_id as id, r.job_title as title, r.status as status
        LIMIT 5
    """)

    if reqs:
        print("\n  Requisitions:")
        for r in reqs:
            print(f"    - {r['id']}: {r['title']} ({r['status']})")


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup Neo4j database for LinkedIn Recruiter Swarm')
    parser.add_argument('--schema-only', action='store_true', help='Only setup schema (no sample data)')
    parser.add_argument('--sample-data', action='store_true', help='Load sample data')
    parser.add_argument('--clear', action='store_true', help='Clear existing data (USE WITH CAUTION)')
    parser.add_argument('--stats', action='store_true', help='Show database statistics only')

    args = parser.parse_args()

    print("=" * 80)
    print("  Neo4j Database Setup")
    print("=" * 80)

    # Get connection details
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'recruiter123')
    database = os.getenv('NEO4J_DATABASE', 'neo4j')

    print(f"\nConnecting to Neo4j...")
    print(f"  URI: {uri}")
    print(f"  Database: {database}")

    try:
        # Connect to database
        kg = KnowledgeGraph(uri=uri, user=user, password=password, database=database)
        print("✓ Connected successfully")

        # Clear database if requested
        if args.clear:
            print("\n⚠️  WARNING: This will delete ALL data in the database!")
            response = input("Type 'DELETE_ALL_DATA' to confirm: ")
            if response == 'DELETE_ALL_DATA':
                kg.clear_database(confirm='DELETE_ALL_DATA')
                print("✓ Database cleared")
            else:
                print("Aborted")
                return

        # Show stats only
        if args.stats:
            show_statistics(kg)
            kg.close()
            return

        # Setup schema
        if not args.sample_data or not args.schema_only:
            if not setup_schema(kg):
                kg.close()
                sys.exit(1)

        # Load sample data
        if args.sample_data and not args.schema_only:
            if not load_sample_data(kg):
                kg.close()
                sys.exit(1)

        # Show statistics
        if args.sample_data or args.schema_only:
            show_statistics(kg)

        # Close connection
        kg.close()

        print("\n" + "=" * 80)
        print("  ✓ Setup Complete!")
        print("=" * 80)

        print("\nNext steps:")
        print("1. Test the connection:")
        print("   python test_neo4j.py")
        print("2. Run the swarm demo:")
        print("   python main.py")
        print("3. Access Neo4j Browser:")
        print("   http://localhost:7474")

    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
