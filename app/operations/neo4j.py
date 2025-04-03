from pydantic import BaseModel
from typing import List, Dict, Any
import re
import spacy

# Neo4j Knowledge Graph Creation
class ParagraphRequest(BaseModel):
    text: str

class Neo4jKnowledgeGraphGenerator:
    @staticmethod
    def preprocess_text(text: str) -> str:
        """Preprocess the input text by removing extra whitespaces and cleaning up punctuation."""
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_knowledge_elements(text: str) -> Dict[str, List[Any]]:
        """Use spaCy to extract key elements from the text for building a knowledge graph."""
        nlp = spacy.load("en_core_web_sm")
        nlp.add_pipe("merge_entities")
        
        # Process the text
        doc = nlp(text)
        entities = []
        relationships = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text.strip(),
                "label": ent.label_
            })
        
        for token in doc:
            if token.pos_ == "NOUN" and not any(token.text == ent['text'] for ent in entities):
                entities.append({
                    "text": token.text.strip(),
                    "label": "COMMON_NOUN"
                })
        
        # Extract subject-verb-object relationships
        for sent in doc.sents:
            for token in sent:
                if token.pos_ == "VERB":
                    subject = None
                    objects = []
                    
                    for child in token.children:
                        if child.dep_ in ["nsubj", "nsubjpass"]:
                            subject = " ".join([t.text for t in child.subtree]).strip()
                        
                        if child.dep_ in ["dobj", "pobj", "iobj"]:
                            obj = " ".join([t.text for t in child.subtree]).strip()
                            objects.append(obj)
                    
                    # Create relationships for each subject-object pair
                    if subject and objects:
                        for obj in objects:
                            relationships.append({
                                "subject": subject,
                                "predicate": token.lemma_,
                                "object": obj
                            })
        
        # Remove duplicates
        entities = list({v['text']: v for v in entities}.values())
        relationships = list({(r['subject'], r['predicate'], r['object']): r for r in relationships}.values())
        
        return {
            "entities": entities,
            "relationships": relationships
        }


    @staticmethod
    def create_neo4j_knowledge_graph(knowledge_elements: Dict[str, List[Any]]) -> List[str]:
        """Generate Cypher queries to create a knowledge graph in Neo4j."""
        queries = []
        
        # Create entity nodes with sanitized text
        for entity in knowledge_elements.get("entities", []):
            safe_text = entity['text'].replace("'", "\\'")
            create_entity_query = f"""
            MERGE (e:Entity {{text: '{safe_text}', type: '{entity['label']}'}})
            """
            queries.append(create_entity_query)
        
        # Create relationships between entities
        for relationship in knowledge_elements.get("relationships", []):
            safe_subject = relationship['subject'].replace("'", "\\'")
            safe_object = relationship['object'].replace("'", "\\'")
            safe_predicate = relationship['predicate'].replace("'", "\\'").upper().replace(" ", "_")

            create_relationship_query = f"""
            MATCH (subject:Entity {{text: '{safe_subject}'}})
            MATCH (object:Entity {{text: '{safe_object}'}})
            MERGE (subject)-[:{safe_predicate}]->(object)
            """
            queries.append(create_relationship_query)
        
        return queries