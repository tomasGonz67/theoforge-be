from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceUpdate
import uuid
from app.models.user import User

async def create_resource(db: AsyncSession, resource: ResourceCreate, user: User):
    """Create a new resource associated with a user."""
    try:
        db_resource = Resource(
            id=uuid.uuid4(),
            **resource.dict(),
            user_id=user.id  # ✅ Ensure correct ownership
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

        for key, value in resource_update.dict(exclude_unset=True).items():
            setattr(db_resource, key, value)

        await db.commit()
        await db.refresh(db_resource)

        return db_resource

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def delete_resource(db: AsyncSession, resource_id: uuid.UUID, user: User):
    """Delete a resource if the user is the owner."""
    try:
        result = await db.execute(select(Resource).filter(Resource.id == resource_id))
        db_resource = result.scalars().first()

        if not db_resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        if db_resource.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this resource")

        await db.delete(db_resource)
        await db.commit()

        return {"message": "Resource deleted successfully"}

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
