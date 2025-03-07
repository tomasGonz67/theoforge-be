from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.resource import Resource
from app.schemas.resource import ResourceSchema, ResourceCreateSchema, ResourceUpdateSchema
import uuid

router = APIRouter()


@router.get("/resources/", response_model=list[ResourceSchema])
async def get_resources(db: AsyncSession = Depends(get_db)):
    """Retrieve all resources"""
    async with db.begin():
        result = await db.execute(
            select(Resource).options(selectinload(Resource.related_resources))
        )
        resources = result.scalars().all()
    
    return resources


@router.get("/resources/{resource_id}", response_model=ResourceSchema)
async def get_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a single resource by ID"""
    async with db.begin():
        result = await db.execute(
            select(Resource).options(selectinload(Resource.related_resources)).filter(Resource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
    
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource


@router.post("/resources/", response_model=ResourceSchema)
async def create_resource(resource_data: ResourceCreateSchema, db: AsyncSession = Depends(get_db)):
    """Create a new resource"""
    new_resource = Resource(**resource_data.dict())
    
    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)
    
    return new_resource


@router.put("/resources/{resource_id}", response_model=ResourceSchema)
async def update_resource(resource_id: uuid.UUID, resource_data: ResourceUpdateSchema, db: AsyncSession = Depends(get_db)):
    """Update an existing resource"""
    async with db.begin():
        result = await db.execute(
            select(Resource).filter(Resource.id == resource_id)
        )
        resource = result.scalar_one_or_none()

    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    for key, value in resource_data.dict(exclude_unset=True).items():
        setattr(resource, key, value)

    await db.commit()
    await db.refresh(resource)
    
    return resource


@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a resource"""
    async with db.begin():
        result = await db.execute(
            select(Resource).filter(Resource.id == resource_id)
        )
        resource = result.scalar_one_or_none()

    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.delete(resource)
    await db.commit()

    return {"message": "Resource deleted successfully"}
