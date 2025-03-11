from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
from app.models.resource import Resource, ResourceType
from app.utils.minio_client import minio_client, BUCKET_NAME
import uuid
import mimetypes
from datetime import timedelta

async def create_resource(db: AsyncSession, file: UploadFile, name: str, description: str, user):
    """Upload a file to MinIO and store metadata in the database."""
    try:
        # Determine file type
        extension = file.filename.split(".")[-1].lower()
        resource_type = ResourceType.OTHER
        if extension in ["jpg", "jpeg", "png", "gif"]:
            resource_type = ResourceType.IMAGE
        elif extension in ["pdf"]:
            resource_type = ResourceType.PDF

        # Generate a unique filename
        file_id = str(uuid.uuid4())
        object_name = f"{user.id}/{file_id}.{extension}"  # Internal MinIO path

        # Upload file to MinIO
        minio_client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=object_name,
            data=file.file,
            length=-1,
            part_size=10 * 1024 * 1024,  # 10MB chunk size
            content_type=mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        )

        # ✅ Generate a presigned URL correctly using timedelta
        external_url = minio_client.presigned_get_object(BUCKET_NAME, object_name, expires=timedelta(seconds=3600))

        # ✅ Create the new resource with correct field names
        new_resource = Resource(
            id=uuid.uuid4(),
            user_id=user.id,
            resource_type=resource_type,
            name=name,
            description=description,
            file_path=object_name,  # Store internal MinIO object key
            external_url=external_url   # Store public MinIO URL
        )

        db.add(new_resource)
        await db.commit()
        await db.refresh(new_resource)

        return new_resource

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")



async def update_resource_file(db: AsyncSession, resource: Resource, file: UploadFile):
    """Upload a new file and update internal/external file paths."""
    file_id = str(uuid.uuid4())
    object_name = f"{resource.user_id}/{file_id}-{file.filename}"  # Internal path

    # Upload new file to MinIO
    minio_client.put_object(BUCKET_NAME, object_name, file.file, file.size)

    # Generate a new presigned URL
    external_url = minio_client.presigned_get_object(BUCKET_NAME, object_name, expires=timedelta(seconds=3600))

    # Update resource in DB
    resource.internal_path = object_name
    resource.external_url = external_url
    await db.commit()
    await db.refresh(resource)

    return object_name
