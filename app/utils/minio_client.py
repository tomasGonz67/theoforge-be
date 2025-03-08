from minio import Minio
import os

# Read MinIO credentials from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "resources")

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Change to True if using HTTPS
)

# Ensure the bucket exists
found = minio_client.bucket_exists(BUCKET_NAME)
if not found:
    minio_client.make_bucket(BUCKET_NAME)
    print(f"Bucket '{BUCKET_NAME}' created successfully.")
else:
    print(f"Bucket '{BUCKET_NAME}' already exists.")
