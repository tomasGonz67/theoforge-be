import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.database import Neo4jService
from app.schemas.philosophers import PhilosopherNode, PhilosopherLink, PhilosophersGraph

logger = logging.getLogger(__name__)

class PhilosophersGraphLoader:
    """Handler for importing and querying philosophers knowledge graph data"""
    
    @staticmethod
    def import_philosophers_from_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import philosophers and their relationships from JSON data into Neo4j.
        
        Args:
            json_data: Dictionary containing nodes and links arrays
            
        Returns:
            Dict with status and count information
        """
        try:
            # Create Neo4j constraints for unique Philosopher nodes by ID
            constraint_query = """
            CREATE CONSTRAINT philosopher_id_unique IF NOT EXISTS 
            FOR (p:Philosopher) REQUIRE p.id IS UNIQUE
            """
            Neo4jService.execute_query(constraint_query)
            
            # Convert JSON data to our schema models
            graph_data = PhilosophersGraph(**json_data)
            
            # Process each philosopher node
            nodes_processed = 0
            for node in graph_data.nodes:
                # Convert contributions list to JSON string (if present)
                contributions_json = json.dumps(node.contributions) if node.contributions else "[]"
                
                # Convert schools list to JSON string (if present)
                schools_json = json.dumps(node.schools) if node.schools else "[]"
                
                # Convert key_ideas list to JSON string (if present)
                key_ideas_json = json.dumps(node.key_ideas) if node.key_ideas else "[]"
                
                # Create or update the philosopher node
                create_node_query = """
                MERGE (p:Philosopher {id: $id})
                SET p.name = $name,
                    p.era = $era,
                    p.community = $community,
                    p.influenceScore = $influenceScore,
                    p.description = $description,
                    p.contributions = $contributions,
                    p.schools = $schools,
                    p.key_ideas = $key_ideas
                """
                
                Neo4jService.execute_query(
                    create_node_query,
                    parameters={
                        "id": node.id,
                        "name": node.name,
                        "era": node.era,
                        "community": node.community,
                        "influenceScore": node.influenceScore,
                        "description": node.description,
                        "contributions": contributions_json,
                        "schools": schools_json,
                        "key_ideas": key_ideas_json
                    }
                )
                nodes_processed += 1
            
            # Process each relationship
            relationships_processed = 0
            for link in graph_data.links:
                # Create the relationship with the appropriate type based on relation
                # Clean up the relation string to be usable as a Neo4j relationship type
                # Neo4j relationship types must be alphanumeric and underscores only
                import re
                # Replace all non-alphanumeric chars with underscores
                relation_type = re.sub(r'[^a-zA-Z0-9]', '_', link.relation.upper().replace(" ", "_"))
                # Remove consecutive underscores
                relation_type = re.sub(r'_+', '_', relation_type)
                # Make sure it starts with a letter (Neo4j requirement)
                if not relation_type or not relation_type[0].isalpha():
                    relation_type = "RELATED_TO"
                
                create_rel_query = f"""
                MATCH (source:Philosopher {{id: $source_id}}), (target:Philosopher {{id: $target_id}})
                MERGE (source)-[r:{relation_type} {{relation: $relation, strength: $strength}}]->(target)
                """
                
                Neo4jService.execute_query(
                    create_rel_query,
                    parameters={
                        "source_id": link.source,
                        "target_id": link.target,
                        "relation": link.relation,
                        "strength": link.strength
                    }
                )
                relationships_processed += 1
                
            return {
                "status": "success",
                "nodes_processed": nodes_processed,
                "relationships_processed": relationships_processed
            }
            
        except Exception as e:
            logger.error(f"Failed to import philosophers data: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def import_philosophers_from_file(json_file_path: str) -> Dict[str, Any]:
        """
        Import philosophers from a JSON file into Neo4j
        
        Args:
            json_file_path: Path to the JSON file
            
        Returns:
            Dict with status and count information
        """
        try:
            file_path = Path(json_file_path)
            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {json_file_path}"}
                
            with open(file_path, 'r') as file:
                json_data = json.load(file)
                
            return PhilosophersGraphLoader.import_philosophers_from_json(json_data)
            
        except Exception as e:
            logger.error(f"Failed to import philosophers from file: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def get_philosophers_graph() -> Optional[Dict[str, Any]]:
        """
        Retrieve the complete philosophers knowledge graph from Neo4j
        
        Returns:
            Dict with nodes and links arrays or None if error
        """
        try:
            # Query all philosopher nodes
            nodes_query = """
            MATCH (p:Philosopher)
            RETURN p.id AS id, 
                   p.name AS name,
                   p.era AS era,
                   p.community AS community,
                   p.influenceScore AS influenceScore,
                   p.description AS description,
                   p.contributions AS contributions,
                   p.schools AS schools,
                   p.key_ideas AS key_ideas
            """
            nodes_result = Neo4jService.execute_query(nodes_query)
            
            # Process nodes, converting JSON strings back to arrays
            nodes = []
            for node in nodes_result:
                # Convert JSON string contributions back to list if present
                if node.get('contributions'):
                    node['contributions'] = json.loads(node['contributions'])
                else:
                    node['contributions'] = []
                    
                # Convert JSON string schools back to list if present
                if node.get('schools'):
                    node['schools'] = json.loads(node['schools'])
                
                # Convert JSON string key_ideas back to list if present
                if node.get('key_ideas'):
                    node['key_ideas'] = json.loads(node['key_ideas'])
                    
                nodes.append(node)
            
            # Query all relationships between philosophers
            links_query = """
            MATCH (source:Philosopher)-[r]->(target:Philosopher)
            RETURN source.id AS source, 
                   target.id AS target,
                   r.relation AS relation,
                   r.strength AS strength,
                   type(r) AS type
            """
            links_result = Neo4jService.execute_query(links_query)
            
            # Process links, using the relation property for consistency with input format
            links = []
            for link in links_result:
                # Use the relation property if available, otherwise use the relationship type
                relation = link.get('relation')
                if not relation:
                    # Convert Neo4j relationship type (e.g., STUDENT_OF) to display format (e.g., "Student of")
                    relation = link.get('type').replace('_', ' ').title()
                
                links.append({
                    "source": link["source"],
                    "target": link["target"],
                    "relation": relation,
                    "strength": link["strength"]
                })
            
            return {
                "nodes": nodes,
                "links": links
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve philosophers graph: {e}")
            return None
