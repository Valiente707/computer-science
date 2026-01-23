#!/usr/bin/env python3
"""
Test Neo4j connection and setup
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("  Neo4j Connection Test")
print("=" * 80)

# Check if neo4j package is installed
try:
    from neo4j import GraphDatabase
    print("\n✓ neo4j package installed")
except ImportError:
    print("\n❌ neo4j package not installed")
    print("\nInstall with: pip install neo4j")
    sys.exit(1)

# Get connection details
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'recruiter123')
database = os.getenv('NEO4J_DATABASE', 'neo4j')

print(f"\nConnection Details:")
print(f"  URI: {uri}")
print(f"  User: {user}")
print(f"  Password: {'*' * len(password)}")
print(f"  Database: {database}")

# Test basic connection
print("\n" + "-" * 80)
print("Testing basic connection...")
print("-" * 80)

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session(database=database) as session:
        # Test query
        result = session.run("RETURN 'Connection successful!' as message, datetime() as timestamp")
        record = result.single()
        print(f"\n✓ {record['message']}")
        print(f"✓ Server time: {record['timestamp']}")

        # Get Neo4j version
        result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
        for record in result:
            print(f"✓ {record['name']}: {record['versions'][0]}")

    print("\n✓ Basic connection test PASSED")

except Exception as e:
    print(f"\n❌ Connection failed: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Make sure Neo4j is running:")
    print("   - Docker: docker ps | grep neo4j")
    print("   - Desktop: Check Neo4j Desktop application")
    print("   - Service: sudo systemctl status neo4j")
    print("2. Check your .env file has correct credentials")
    print("3. Verify Neo4j is listening on port 7687")
    print("4. Check firewall settings")
    sys.exit(1)

# Test with KnowledgeGraph class
print("\n" + "-" * 80)
print("Testing KnowledgeGraph class...")
print("-" * 80)

try:
    from src.knowledge_graph import KnowledgeGraph

    kg = KnowledgeGraph(uri=uri, user=user, password=password, database=database)

    # Get statistics
    stats = kg.get_statistics()
    print(f"\n✓ KnowledgeGraph initialized")
    print(f"\nDatabase Statistics:")
    print(f"  Candidates: {stats.get('candidate_count', 0)}")
    print(f"  Requisitions: {stats.get('requisition_count', 0)}")
    print(f"  Skills: {stats.get('skill_count', 0)}")
    print(f"  Companies: {stats.get('company_count', 0)}")
    print(f"  Messages: {stats.get('message_count', 0)}")
    print(f"  Total Relationships: {stats.get('relationship_count', 0)}")

    kg.close()
    print("\n✓ KnowledgeGraph test PASSED")

except Exception as e:
    print(f"\n❌ KnowledgeGraph test failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    if driver:
        driver.close()

# All tests passed
print("\n" + "=" * 80)
print("  ✓ All tests PASSED!")
print("=" * 80)

print("\nNext steps:")
print("1. Run setup script to create schema:")
print("   python setup_neo4j.py")
print("2. Load sample data:")
print("   python setup_neo4j.py --sample-data")
print("3. Run the swarm demo:")
print("   python main.py")

print("\n")
