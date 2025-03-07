from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.operations.resource import (
    create_resource, get_resource, get_all_resources,
    update_resource, delete_resource, link_related_resources, search_resources
)
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceOut
from app.database import get_db
from app.routers.dependencies import get_current_user
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

router = APIRouter(
    prefix="/resources",
    tags=["Resources"],
)

@router.post("/", response_model=ResourceOut)
async def create_new_resource(
    resource: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)  # ✅ Get the full `User` object
):
    """Create a new resource (only for registered users)."""
    return await create_resource(db=db, resource=resource, user=user)  # ✅ Pass full `User` object


@router.get("/{resource_id}", response_model=ResourceOut)
def read_resource(resource_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve a resource by ID."""
    return get_resource(db=db, resource_id=resource_id)

@router.get("/", response_model=List[ResourceOut])
async def read_all_resources(category: str = None, is_public: bool = None, db: AsyncSession = Depends(get_db)):
    """Retrieve all resources with optional filters."""
    return await get_all_resources(db=db, category=category, is_public=is_public)

@router.put("/{resource_id}", response_model=ResourceOut)
def update_existing_resource(
    resource_id: uuid.UUID, resource_update: ResourceUpdate, db: Session = Depends(get_db), user_id: uuid.UUID = Depends(get_current_user)
):
    """Update a resource (only the owner can update)."""
    return update_resource(db=db, resource_id=resource_id, resource_update=resource_update, user_id=user_id)

@router.delete("/{resource_id}")
def delete_existing_resource(resource_id: uuid.UUID, db: Session = Depends(get_db), user_id: uuid.UUID = Depends(get_current_user)):
    """Delete a resource (only the owner can delete)."""
    return delete_resource(db=db, resource_id=resource_id, user_id=user_id)

@router.post("/{resource_id}/link/{related_resource_id}")
def link_resources(
    resource_id: uuid.UUID, related_resource_id: uuid.UUID, db: Session = Depends(get_db), user_id: uuid.UUID = Depends(get_current_user)
):
    """Link two resources as related (only the owner can link)."""
    return link_related_resources(db=db, resource_id=resource_id, related_resource_id=related_resource_id, user_id=user_id)

@router.get("/search/", response_model=List[ResourceOut])
def search_for_resources(query: str, db: Session = Depends(get_db)):
    """Search resources by name or description."""
    return search_resources(db=db, query=query)
