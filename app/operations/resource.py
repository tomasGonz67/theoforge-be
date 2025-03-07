from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceUpdate
from app.routers.dependencies import get_current_user
import uuid
from app.models.user import User

async def create_resource(db: AsyncSession, resource: ResourceCreate, user: User):
    """Create a new resource associated with a user."""
    try:
        db_resource = Resource(
            id=uuid.uuid4(),
            name=resource.name,
            description=resource.description,
            category=resource.category,
            tags=resource.tags,
            profile_picture=resource.profile_picture,
            source_url=resource.source_url,
            user_id=user.id,  # ✅ Extract `id` from User object
            is_public=resource.is_public,
        )
        db.add(db_resource)
        await db.commit()
        await db.refresh(db_resource)
        return db_resource
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def get_resource(db: AsyncSession, resource_id: uuid.UUID):
    """Retrieve a resource by ID."""
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    db_resource = result.scalars().first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return db_resource

async def get_all_resources(db: AsyncSession, category: str = None, is_public: bool = None):
    """Retrieve all resources with optional filtering."""
    stmt = select(Resource)
    if category:
        stmt = stmt.filter(Resource.category == category)
    if is_public is not None:
        stmt = stmt.filter(Resource.is_public == is_public)

    result = await db.execute(stmt)
    return result.scalars().all()

async def update_resource(
    db: AsyncSession, resource_id: uuid.UUID, resource_update: ResourceUpdate, user: User
):
    """Update a resource if the user is the owner."""
    try:
        result = await db.execute(select(Resource).filter(Resource.id == resource_id))
        db_resource = result.scalars().first()

        if not db_resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        if db_resource.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this resource")

        # Update only the fields that were provided
        update_data = resource_update.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_resource, key, value)

        db.add(db_resource)
        await db.commit()
        await db.refresh(db_resource)

        return db_resource

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def delete_resource(db: AsyncSession, resource_id: uuid.UUID, user):
    """Delete a resource if the user is the owner."""
    try:
        result = await db.execute(select(Resource).filter(Resource.id == resource_id))
        db_resource = result.scalars().first()

        if not db_resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        if db_resource.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this resource")

        await db.delete(db_resource)  # ✅ Use `await` to delete asynchronously
        await db.commit()  # ✅ Use `await` to commit changes

        return {"message": "Resource deleted successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def link_related_resources(db: AsyncSession, resource_id: uuid.UUID, related_resource_id: uuid.UUID, user):
    """Link two resources as related, if the user owns the primary resource."""
    try:
        # Fetch resources asynchronously
        result = await db.execute(select(Resource).filter(Resource.id == resource_id))
        primary_resource = result.scalars().first()

        result = await db.execute(select(Resource).filter(Resource.id == related_resource_id))
        related_resource = result.scalars().first()

        if not primary_resource or not related_resource:
            raise HTTPException(status_code=404, detail="One or both resources not found")

        if primary_resource.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to link resources")

        # ✅ Link resources correctly
        primary_resource.related_resources.append(related_resource)
        await db.commit()

        return {"message": "Resources linked successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def search_resources(db: AsyncSession, query: str):
    """Search for resources by name or description."""
    stmt = select(Resource).filter(
        (Resource.name.ilike(f"%{query}%")) | (Resource.description.ilike(f"%{query}%"))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
