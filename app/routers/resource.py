from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.resource import Resource
from app.operations.resource import create_resource
from app.utils.minio_client import minio_client, BUCKET_NAME
from app.routers.dependencies import get_current_user
from app.schemas.resource import ResourceSchema, ResourceUpdateSchema
import uuid
from typing import Optional
from datetime import timedelta  # ✅ Add this import



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

@router.get("/", response_model=list[ResourceSchema])
async def list_resources(db: AsyncSession = Depends(get_db)):
    """Retrieve all resources."""
    result = await db.execute(select(Resource).options(joinedload(Resource.related_resources)))
    
    # ✅ Ensure unique results to avoid InvalidRequestError
    resources = result.unique().scalars().all()
    
    return resources


@router.get("/{resource_id}", response_model=ResourceSchema)
async def get_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a single resource by ID."""
    result = await db.execute(
        select(Resource)
        .filter(Resource.id == resource_id)
        .options(joinedload(Resource.related_resources))
    )
    resource = result.unique().scalar_one_or_none()  # ✅ FIXED

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return resource


from fastapi import File
from app.operations.resource import update_resource_file  # Ensure this function exists

@router.put("/{resource_id}", response_model=ResourceSchema)
async def update_resource(
    resource_id: uuid.UUID,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Update only provided fields."""
    
    # Fetch the resource
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    if resource.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this resource")
    
    # Update fields only if they are provided
    if name:
        resource.name = name
    if description:
        resource.description = description

    # If a new file is uploaded, replace the old file
    if file:
        new_file_path = await update_resource_file(db, resource, file)
        resource.file_path = new_file_path

    await db.commit()
    await db.refresh(resource)
    return resource




@router.delete("/{resource_id}")
async def delete_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Delete a resource."""
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resource")
    
    await db.delete(resource)
    await db.commit()
    return {"message": "Resource deleted successfully"}

@router.post("/{resource_id}/link/{related_resource_id}")
async def link_resources(
    resource_id: uuid.UUID, 
    related_resource_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Link two resources together."""
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    
    result_related = await db.execute(select(Resource).filter(Resource.id == related_resource_id))
    related_resource = result_related.scalar_one_or_none()
    
    if not resource or not related_resource:
        raise HTTPException(status_code=404, detail="One or both resources not found")
    
    if resource.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this resource")
    
    resource.related_resources.append(related_resource)
    await db.commit()
    return {"message": "Resources linked successfully"}

from datetime import timedelta  # ✅ Make sure this is imported

@router.get("/{resource_id}/download")
async def get_resource_download_link(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Generate a fresh presigned URL for downloading a resource."""
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # ✅ Ensure file_path exists
    if not resource.file_path:
        raise HTTPException(status_code=500, detail="File path is missing in the database")

    # ✅ Generate a new presigned URL
    try:
        external_url = minio_client.presigned_get_object(BUCKET_NAME, resource.file_path, expires=timedelta(seconds=3600))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

    return {"external_url": external_url}

