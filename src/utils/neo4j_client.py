"""Neo4j database connection and operations"""
from neo4j import GraphDatabase
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import json

from ..utils.config import settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j database connection manager"""
    
    def __init__(self):
        """Initialize Neo4j connection"""
        self.driver = None
        self.connect()
    
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            auth = None
            if settings.neo4j_username and settings.neo4j_password:
                auth = (settings.neo4j_username, settings.neo4j_password)
            
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=auth
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
            
            # Initialize schema
            self._initialize_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _initialize_schema(self):
        """Initialize Neo4j schema with constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
                "CREATE CONSTRAINT conversation_id IF NOT EXISTS FOR (c:Conversation) REQUIRE c.conversation_id IS UNIQUE",
                "CREATE CONSTRAINT message_id IF NOT EXISTS FOR (m:Message) REQUIRE m.message_id IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint might already exist: {e}")
            
            # Create indexes
            indexes = [
                "CREATE INDEX user_created IF NOT EXISTS FOR (u:User) ON (u.created_at)",
                "CREATE INDEX message_timestamp IF NOT EXISTS FOR (m:Message) ON (m.timestamp)",
                "CREATE INDEX conversation_created IF NOT EXISTS FOR (c:Conversation) ON (c.created_at)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.debug(f"Index might already exist: {e}")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def create_user(self, user_id: str, attributes: Dict[str, Any]) -> Dict:
        """Create or update a user node"""
        with self.driver.session() as session:
            result = session.run(
                """
                MERGE (u:User {user_id: $user_id})
                SET u += $attributes,
                    u.updated_at = datetime()
                ON CREATE SET u.created_at = datetime()
                RETURN u
                """,
                user_id=user_id,
                attributes=attributes
            )
            return result.single()["u"]
    
    def create_conversation(self, conversation_id: str, user_id: str, metadata: Dict[str, Any] = None) -> Dict:
        """Create a new conversation"""
        with self.driver.session() as session:
            # Convert metadata to JSON string to avoid Neo4j map issues
            metadata_json = json.dumps(metadata) if metadata else "{}"
            
            result = session.run(
                """
                MERGE (u:User {user_id: $user_id})
                ON CREATE SET u.created_at = datetime()
                CREATE (c:Conversation {
                    conversation_id: $conversation_id,
                    created_at: datetime(),
                    metadata: $metadata
                })
                CREATE (u)-[:HAS_CONVERSATION]->(c)
                RETURN c
                """,
                conversation_id=conversation_id,
                user_id=user_id,
                metadata=metadata_json
            )
            record = result.single()
            return dict(record["c"]) if record else None
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                    agent_name: Optional[str] = None, metadata: Dict[str, Any] = None) -> Dict:
        """Add a message to a conversation"""
        with self.driver.session() as session:
            # Convert metadata to JSON string
            metadata_json = json.dumps(metadata) if metadata else "{}"
            
            result = session.run(
                """
                MATCH (c:Conversation {conversation_id: $conversation_id})
                CREATE (m:Message {
                    message_id: randomUUID(),
                    role: $role,
                    content: $content,
                    agent_name: $agent_name,
                    timestamp: datetime(),
                    metadata: $metadata
                })
                CREATE (c)-[:CONTAINS]->(m)
                RETURN m
                """,
                conversation_id=conversation_id,
                role=role,
                content=content,
                agent_name=agent_name,
                metadata=metadata_json
            )
            record = result.single()
            return dict(record["m"]) if record else None
    
    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve conversation history"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Conversation {conversation_id: $conversation_id})-[:CONTAINS]->(m:Message)
                RETURN m
                ORDER BY m.timestamp ASC
                LIMIT $limit
                """,
                conversation_id=conversation_id,
                limit=limit
            )
            return [record["m"] for record in result]
    
    def get_user_attributes(self, user_id: str) -> Optional[Dict]:
        """Get user attributes"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})
                RETURN u
                """,
                user_id=user_id
            )
            record = result.single()
            return dict(record["u"]) if record else None
    
    def update_user_attributes(self, user_id: str, attributes: Dict[str, Any]):
        """Update user attributes"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {user_id: $user_id})
                SET u += $attributes,
                    u.updated_at = datetime()
                """,
                user_id=user_id,
                attributes=attributes
            )
    
    def create_knowledge_graph(self, conversation_id: str, entities: List[Dict], 
                               relationships: List[Dict]):
        """Create knowledge graph from perception agent output"""
        with self.driver.session() as session:
            # Create entities
            for entity in entities:
                # Convert properties dict to JSON string
                properties_json = json.dumps(entity.get("properties", {}))
                
                session.run(
                    """
                    MERGE (e:Entity {name: $name, type: $type})
                    SET e.properties = $properties
                    WITH e
                    MATCH (c:Conversation {conversation_id: $conversation_id})
                    MERGE (c)-[:EXTRACTED_ENTITY]->(e)
                    """,
                    name=entity.get("name"),
                    type=entity.get("type"),
                    properties=properties_json,
                    conversation_id=conversation_id
                )
            
            # Create relationships
            for rel in relationships:
                # Convert properties dict to JSON string
                rel_properties_json = json.dumps(rel.get("properties", {}))
                
                session.run(
                    """
                    MATCH (e1:Entity {name: $source})
                    MATCH (e2:Entity {name: $target})
                    MERGE (e1)-[r:RELATES_TO {type: $rel_type}]->(e2)
                    SET r.properties = $properties
                    """,
                    source=rel.get("source"),
                    target=rel.get("target"),
                    rel_type=rel.get("type"),
                    properties=rel_properties_json
                )


# Global Neo4j connection instance
neo4j_db = Neo4jConnection()
