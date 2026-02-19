"""
Responsible Persons API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ...core.database import get_database
from ...models.user import UserInDB
from ...models.responsible_person import ResponsiblePerson, ResponsiblePersonInDB
from ...schemas.responsible_person import (
    ResponsiblePersonCreate,
    ResponsiblePersonResponse,
)
from ...api.dependencies import get_current_user


router = APIRouter(prefix="/responsible-persons", tags=["Responsible Persons"])


@router.post("", response_model=ResponsiblePersonResponse, status_code=status.HTTP_201_CREATED)
async def create_responsible_person(
    event_id: str,
    person_data: ResponsiblePersonCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Create responsible person for event."""
    # Verify user owns event
    event = await db["events"].find_one({
        "_id": ObjectId(event_id),
        "organizer_id": current_user.id,
    })
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    person = ResponsiblePerson(event_id=event_id, **person_data.model_dump())
    result = await db["responsible_persons"].insert_one(person.model_dump())

    person_dict = person.model_dump()
    person_dict["_id"] = str(result.inserted_id)

    return ResponsiblePersonResponse(**person_dict)


@router.get("", response_model=list[ResponsiblePersonResponse])
async def list_responsible_persons(
    event_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """List responsible persons for event."""
    # Verify user owns event
    event = await db["events"].find_one({
        "_id": ObjectId(event_id),
        "organizer_id": current_user.id,
    })
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    persons = []
    async for person_doc in db["responsible_persons"].find({"event_id": event_id}):
        person_doc["_id"] = str(person_doc["_id"])
        persons.append(ResponsiblePersonResponse(**person_doc))

    return persons
