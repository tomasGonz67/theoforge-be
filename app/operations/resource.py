from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceUpdate
from app.routers.dependencies import get_current_user
from sqlalchemy.dialects.postgresql import UUID
import uuid

def create_resource(db: Session, resource: ResourceCreate, user_id: uuid.UUID):
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
            user_id=user_id,
            is_public=resource.is_public,
        )
        db.add(db_resource)
        db.commit()
        db.refresh(db_resource)
        return db_resource
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred while creating resource")

def get_resource(db: Session, resource_id: uuid.UUID):
    """Retrieve a resource by ID."""
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return db_resource

def get_all_resources(db: Session, category: str = None, is_public: bool = None):
    """Retrieve all resources with optional filtering by category or public/private status."""
    query = db.query(Resource)
    if category:
        query = query.filter(Resource.category == category)
    if is_public is not None:
        query = query.filter(Resource.is_public == is_public)
    return query.all()

def update_resource(db: Session, resource_id: uuid.UUID, resource_update: ResourceUpdate, user_id: uuid.UUID):
    """Update a resource if the user is the owner."""
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    if db_resource.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this resource")

    for key, value in resource_update.dict(exclude_unset=True).items():
        setattr(db_resource, key, value)

    db.commit()
    db.refresh(db_resource)
    return db_resource

def delete_resource(db: Session, resource_id: uuid.UUID, user_id: uuid.UUID):
    """Delete a resource if the user is the owner."""
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if db_resource.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resource")

    db.delete(db_resource)
    db.commit()
    return {"message": "Resource deleted successfully"}

def link_related_resources(db: Session, resource_id: uuid.UUID, related_resource_id: uuid.UUID, user_id: uuid.UUID):
    """Link two resources as related, if the user owns the primary resource."""
    primary_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    related_resource = db.query(Resource).filter(Resource.id == related_resource_id).first()

    if not primary_resource or not related_resource:
        raise HTTPException(status_code=404, detail="One or both resources not found")

    if primary_resource.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to link resources")

    primary_resource.related_resources.append(related_resource)
    db.commit()
    return {"message": "Resources linked successfully"}

def search_resources(db: Session, query: str):
    """Search for resources by name or description."""
    return db.query(Resource).filter(
        (Resource.name.ilike(f"%{query}%")) | (Resource.description.ilike(f"%{query}%"))
    ).all()
