# Knowledge Graph RAG Pipeline Overview

This document outlines the workflow for processing text, storing it in a knowledge graph and vector database, and using this information to answer questions using a Retrieval-Augmented Generation (RAG) approach.

The pipeline integrates OpenAI, Qdrant, and Neo4j.

## 1. Data Ingestion (`/text-cleaning/clean` Endpoint)

This single endpoint handles the entire process of converting raw text into structured and searchable knowledge.

**Input:**
- A JSON object containing raw text: `{"raw_text": "..."}`

**Process:**

1.  **Basic Cleaning:** Performs simple text cleaning (e.g., removing extra whitespace).
2.  **Knowledge Extraction (OpenAI):** Sends the cleaned text to an OpenAI model (e.g., GPT-4) instructed to extract:
    *   **Entities:** Meaningful nouns or concepts (e.g., "Marie Curie", "Radioactivity") with their types (e.g., `PERSON`, `CONCEPT`) and relevant attributes (e.g., `["physicist", "chemist"]`).
    *   **Relationships:** Connections between entities (e.g., `(Marie Curie, CONDUCTED_RESEARCH_ON, Radioactivity)`).
    The output is expected in a specific JSON format.
3.  **Knowledge Enhancement (OpenAI):** Sends the extracted entities and relationships back to OpenAI for refinement. This step aims to add missing context, infer plausible relationships, and correct potential errors from the initial extraction.
4.  **Normalization (`_normalize_keys`):** Transforms the enhanced JSON data into formats suitable for Qdrant and Neo4j:
    *   Renames keys (e.g., `entity_name` -> `text`, `source_entity` -> `subject`).
    *   **Crucially, converts the list of attributes for each entity into a JSON string** (e.g., `["physicist"]` becomes `"[\"physicist\"]"`). This is necessary for storing the list as a single payload field in Qdrant.
5.  **Embedding Generation (OpenAI):** Generates vector embeddings for the `text` field of each extracted entity using an OpenAI embedding model (e.g., `text-embedding-3-small`).
6.  **Qdrant Upsert:** Stores the generated embeddings in the `theoforge_vectors` Qdrant collection. Each point includes:
    *   `id`: A unique identifier.
    *   `vector`: The embedding vector.
    *   `payload`: Contains the entity's `text`, `label` (type), and the `attributes` **as the JSON string** created during normalization.
7.  **Neo4j Load:** Uses the `Neo4jKnowledgeGraphLoader` to persist the normalized graph structure (entities as nodes, relationships as edges) into the Neo4j database. The loader creates nodes with properties (like `text`, `label`, and potentially stringified attributes if configured) and the corresponding relationships between them.

**Output:**
- A JSON response indicating the success or failure status of the Qdrant and Neo4j operations: `{"qdrant_status": "success", "neo4j_status": "success", ...}`

## 2. Retrieval and Response Generation (`/llm/generate-response` Endpoint)

This endpoint uses the ingested knowledge to answer user questions.

**Input:**
- A JSON object containing the user's question: `{"user_input": "..."}`

**Process (`get_relevant_context` and Endpoint Logic):**

1.  **Embed Query (OpenAI):** Generates a vector embedding for the `user_input` question using the same OpenAI embedding model used during ingestion.
2.  **Semantic Search (Qdrant):** Searches the `theoforge_vectors` collection in Qdrant using the query embedding. This retrieves the points (entities) whose stored text is semantically closest to the user's question.
3.  **Extract Initial Context:** From the top Qdrant search results, extracts the entity `text` and the associated `attributes` payload field (which is a JSON string).
4.  **Graph Traversal (Neo4j):** Queries the Neo4j database:
    *   Finds the nodes corresponding to the entity `text` values retrieved from Qdrant.
    *   Retrieves these nodes, their direct 1-hop neighbors, and the relationships connecting them.
    *   Fetches attributes stored as properties on these Neo4j nodes and neighbors.
5.  **Format Context:** Constructs a text-based context string for the LLM. This involves:
    *   Iterating through the Neo4j query results.
    *   Parsing the `attributes` JSON string retrieved from the *Qdrant payload* back into a Python list using `json.loads()`.
    *   Combining the entity names, parsed attributes (from Qdrant), relationship types (from Neo4j), and neighbor details (from Neo4j) into a readable format.
6.  **LLM Call (OpenAI):** Sends a prompt to an OpenAI chat model (e.g., GPT-4). The prompt includes:
    *   The original `user_input`.
    *   The formatted `context` string.
7.  **Return Response:** Returns the generated answer from the LLM to the user.

**Output:**
- A JSON object containing the LLM's response: `{"response": "..."}`

## Key Components Summary

*   **OpenAI:** Used for knowledge extraction/enhancement, embedding generation, and final response generation.
*   **Qdrant:** Stores vector embeddings of entities for fast semantic search based on the user's query.
*   **Neo4j:** Stores the structured knowledge graph (entities as nodes, relationships as edges) allowing retrieval of explicit connections and multi-hop context around entities identified by Qdrant.
