from typing import List, Dict, Any
import logging
from app.database import Neo4jService

logger = logging.getLogger(__name__)

# Neo4j Knowledge Graph Creation
class Neo4jKnowledgeGraphLoader:
    # Note: Text extraction/cleaning is expected to happen upstream (e.g., via GPT).


    @staticmethod
    def _generate_parameterized_queries(knowledge_elements: Dict[str, List[Any]]) -> List[tuple[str, Dict[str, Any]]]:
        """Generate parameterized Cypher queries and their parameters."""
        parameterized_queries = []
        
        # Generate parameterized queries for entities
        for entity in knowledge_elements.get("entities", []):
            # Use the new keys: 'text', 'label', 'attributes', 'embedding'
            entity_text = entity.get('text', '')
            entity_label_raw = entity.get('label', 'Entity')
            # Sanitize label
            label = ''.join(filter(lambda x: x.isalnum() or x == '_', entity_label_raw.replace(' ', '_')))
            if not label: label = 'Entity' # Default label

            # Skip creating entity if text is empty
            if not entity_text:
                logger.warning(f"Skipping entity creation due to empty text: {entity}")
                continue
            # Base query and params - Add :Document label alongside specific label
            query = f"MERGE (e:Document:{label} {{text: $text}})"
            params = {"text": entity_text}

            # Add attributes string if present
            attributes = entity.get('attributes') # This should be a JSON string or None
            if attributes is not None:
                query += " ON CREATE SET e.attributes = $attributes"
                query += " ON MATCH SET e.attributes = $attributes"
                params["attributes"] = attributes

            parameterized_queries.append((query, params))
        
        # Generate parameterized queries for relationships
        # Create a mapping from entity text to its primary label, using new keys
        entities_dict = {e.get('text', ''): ''.join(filter(lambda x: x.isalnum() or x == '_', e.get('label', 'Entity').replace(' ', '_'))) or 'Entity'
                         for e in knowledge_elements.get("entities", []) if e.get('text')}

        for relationship in knowledge_elements.get("relationships", []):
            # Use the new keys: 'subject', 'predicate', 'object'
            subject_text = relationship.get('subject', '')
            object_text = relationship.get('object', '')
            predicate_raw = relationship.get('predicate', 'RELATED_TO')

            # Skip creating relationship if subject or object text is empty
            if not subject_text or not object_text:
                logger.warning(f"Skipping relationship creation due to empty subject/object: {relationship}")
                continue
            # Get labels from our pre-computed dict
            subject_label_raw = entities_dict.get(subject_text, 'Entity')
            object_label_raw = entities_dict.get(object_text, 'Entity')

            # Use the already sanitized labels from the entities_dict
            subject_label = subject_label_raw
            object_label = object_label_raw
            # Sanitize predicate
            predicate = ''.join(filter(lambda x: x.isalnum() or x == '_', predicate_raw.upper().replace(' ', '_')))
            if not predicate: predicate = 'RELATED_TO'

            query = f"""
            MATCH (subject:Document:{subject_label} {{text: $subject_text}})
            MATCH (object:Document:{object_label} {{text: $object_text}})
            MERGE (subject)-[:{predicate}]->(object)
            """
            params = {
                "subject_text": subject_text,
                "object_text": object_text
            }
            parameterized_queries.append((query, params))
        
        return parameterized_queries

    @staticmethod
    def load_knowledge_graph(knowledge_elements: Dict[str, List[Any]]):
        """Generate and execute parameterized Cypher queries individually."""
        parameterized_queries = Neo4jKnowledgeGraphLoader._generate_parameterized_queries(knowledge_elements)
        if not parameterized_queries:
            logger.info("No parameterized queries generated.")
            return {"status": "success", "nodes_processed": 0, "relationships_processed": 0, "message": "No data to load."}

        # Initialize approximate counters (MERGE doesn't guarantee creation)
        nodes_processed = 0
        relationships_processed = 0
        errors = []

        try:
            # Execute each query individually
            for query, params in parameterized_queries:
                try:
                    Neo4jService.execute_query(query, parameters=params)
                    # Increment approximate counters based on query type
                    if "MERGE (e:" in query:
                        nodes_processed += 1
                    elif "MERGE (subject)-[:" in query:
                        relationships_processed += 1
                except Exception as query_error:
                    logger.error(f"Error executing query: {query} with params: {params}. Error: {query_error}")
                    errors.append(str(query_error))
                    # Continue processing even if one query fails, report errors at the end

            if errors:
                 # Report failure if any query errors occurred
                 error_message = "; ".join(errors)
                 logger.error(f"Completed loading knowledge graph with errors: {error_message}")
                 return {"status": "error", "message": f"Completed with errors: {error_message}", "nodes_processed": nodes_processed, "relationships_processed": relationships_processed}
            else:
                 logger.info(f"Successfully executed {len(parameterized_queries)} queries. Processed approx {nodes_processed} nodes and {relationships_processed} relationships.")
                 return {"status": "success", "nodes_processed": nodes_processed, "relationships_processed": relationships_processed}

        except Exception as e:
            # Catch unexpected exceptions during processing
            logger.error(f"Failed to load knowledge graph into Neo4j due to an unexpected error: {e}")
            return {"status": "error", "message": str(e)}