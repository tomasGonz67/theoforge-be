import uuid
import logging
from typing import List, Dict, Any

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

from settings.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(self, url: str, collection_name: str, vector_dimension: int):
        self.url = url
        self.collection_name = collection_name
        self.vector_dimension = vector_dimension
        # Use AsyncQdrantClient for compatibility with FastAPI
        self.client = AsyncQdrantClient(url=self.url)

    async def initialize_collection(self):
        """Ensures the Qdrant collection exists and has the correct configuration."""
        try:
            # Attempt to get collection info to check existence
            await self.client.get_collection(collection_name=self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists.")
            # Optional: Verify existing collection parameters match expected config
        except UnexpectedResponse as e:
            # If collection does not exist, Qdrant throws 404
            if e.status_code == 404:
                logger.info(f"Collection '{self.collection_name}' does not exist. Creating...")
                try:
                    await self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self.vector_dimension, distance=Distance.COSINE),
                        # Consider adding on_disk_payload=True if payload might become large
                    )
                    logger.info(f"Collection '{self.collection_name}' created successfully.")
                except UnexpectedResponse as create_exc:
                    logger.error(f"Failed to create Qdrant collection '{self.collection_name}' after check: {create_exc}")
                    raise create_exc # Re-raise the creation error
            else:
                # Re-raise unexpected errors (e.g., connection issues)
                logger.error(f"Failed to check Qdrant collection '{self.collection_name}' existence: {e}")
                raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred during Qdrant collection initialization: {e}")
            raise

    async def upsert_vectors(self, entities: List[Dict[str, Any]]):
        """Upserts entity vectors and metadata into the Qdrant collection."""
        points_to_upsert = []
        for entity in entities:
            entity_text = entity.get('text')
            embedding = entity.get('embedding')

            if not entity_text or not embedding:
                logger.warning(f"Skipping entity due to missing text or embedding: {entity.get('text', 'N/A')}")
                continue

            # Generate a stable UUID based on the entity text for potential idempotency
            # Alternatively, use uuid.uuid4() for guaranteed uniqueness on each run
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entity_text))

            payload = {
                'text': entity_text,
                'label': entity.get('label', 'Entity'),
                # Include attributes if needed, ensure it's serializable
                'attributes': entity.get('attributes') # Assuming attributes is already a JSON string or None
            }
            # Filter out None values from payload
            payload = {k: v for k, v in payload.items() if v is not None}

            points_to_upsert.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            )

        if not points_to_upsert:
            logger.info("No valid points to upsert into Qdrant.")
            return

        try:
            logger.info(f"Upserting {len(points_to_upsert)} points into collection '{self.collection_name}'...")
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points_to_upsert,
                wait=True # Wait for operation to complete
            )
            logger.info(f"Successfully upserted {len(points_to_upsert)} points.")
        except UnexpectedResponse as e:
            logger.error(f"Failed to upsert points into Qdrant collection '{self.collection_name}': {e}")
            # Potentially raise or handle retry logic
        except Exception as e:
            logger.error(f"An unexpected error occurred during Qdrant upsert: {e}")
            # Potentially raise

    async def close(self):
        """Closes the async Qdrant client."""
        await self.client.close()

# Singleton instance of the service, initialized with settings
qdrant_service = QdrantService(
    url=settings.qdrant_url,
    collection_name=settings.qdrant_collection,
    vector_dimension=settings.vector_dimension
)
