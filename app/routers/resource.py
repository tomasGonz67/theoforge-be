from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.resource import Resource
from app.operations.resource import create_resource
from app.utils.minio_client import minio_client, BUCKET_NAME
from app.routers.dependencies import get_current_user
from app.schemas.resource import ResourceSchema
import uuid

router = APIRouter(prefix="/resources", tags=["Resources"])

@router.post("/", response_model=ResourceSchema)
async def upload_resource(
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Upload a file and create a resource record."""
    if not file:
        raise HTTPException(status_code=400, detail="File is required")

    return await create_resource(db, file, title, description, user)


@router.get("/{resource_id}/download")
async def download_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Generate a presigned URL for a resource."""
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    try:
        # Generate a presigned URL for downloading the file
        url = minio_client.presigned_get_object(BUCKET_NAME, resource.file_path)
        return {"download_url": url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File retrieval failed: {str(e)}")
