from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.resource import Resource
from app.schemas.resource import ResourceSchema, ResourceCreateSchema, ResourceUpdateSchema
from app.routers.dependencies import get_current_user
import uuid

router = APIRouter()


@router.get("/resources/", response_model=list[ResourceSchema])
async def get_resources(db: AsyncSession = Depends(get_db)):
    """Retrieve all resources"""
    result = await db.execute(
        select(Resource).options(selectinload(Resource.related_resources))
    )
    return result.scalars().all()


@router.get("/resources/{resource_id}", response_model=ResourceSchema)
async def get_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a single resource by ID"""
    result = await db.execute(
        select(Resource).options(selectinload(Resource.related_resources)).filter(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource


@router.post("/resources/", response_model=ResourceSchema)
async def create_resource(
    resource_data: ResourceCreateSchema, 
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Create a new resource associated with a user"""
    
    # Convert resource_data into a dictionary but exclude user_id to prevent duplication
    resource_dict = resource_data.dict(exclude={"user_id"})  

    new_resource = Resource(
        id=uuid.uuid4(),
        **resource_dict,  # ✅ Unpack the dict (without user_id)
        user_id=user.id    # ✅ Assign user_id explicitly
    )

    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)
    
    return new_resource

@router.post("/resources/{resource_id}/link/{related_resource_id}")
async def link_related_resources(
    resource_id: uuid.UUID,
    related_resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Link two resources as related, if the user owns the primary resource."""
    try:
        # Fetch primary resource with relationships preloaded
        result = await db.execute(
            select(Resource)
            .options(selectinload(Resource.related_resources))  # ✅ Preload relationships
            .filter(Resource.id == resource_id)
        )
        primary_resource = result.scalars().first()

        # Fetch related resource (without lazy loading issues)
        result = await db.execute(select(Resource).filter(Resource.id == related_resource_id))
        related_resource = result.scalars().first()

        # Ensure both resources exist
        if not primary_resource or not related_resource:
            raise HTTPException(status_code=404, detail="One or both resources not found")

        # Ensure user owns the primary resource
        if primary_resource.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this resource")

        # ✅ Append the related resource properly
        if related_resource not in primary_resource.related_resources:
            primary_resource.related_resources.append(related_resource)

        await db.commit()
        await db.refresh(primary_resource)  # ✅ Refresh after commit to update relationships

        return {"message": "Resources linked successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



@router.put("/resources/{resource_id}", response_model=ResourceSchema)
async def update_resource(
    resource_id: uuid.UUID, 
    resource_data: ResourceUpdateSchema, 
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Update an existing resource"""
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    if resource.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this resource")

    for key, value in resource_data.dict(exclude_unset=True).items():
        setattr(resource, key, value)

    await db.commit()
    await db.refresh(resource)
    
    return resource


@router.delete("/resources/{resource_id}")
async def delete_resource(
    resource_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Delete a resource"""
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resource")

    await db.delete(resource)
    await db.commit()

    return {"message": "Resource deleted successfully"}
