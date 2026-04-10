import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import RequirementSignalLink

router = APIRouter(prefix='/api/links', tags=['links'])


@router.post('')
async def create_links(data: dict, db: AsyncSession = Depends(get_db)):
    requirement_id = data.get('requirementId')
    signal_ids = data.get('signalIds', [])
    if not requirement_id:
        raise HTTPException(status_code=400, detail='requirementId 必填')

    await db.execute(
        delete(RequirementSignalLink).where(
            RequirementSignalLink.requirement_id == requirement_id
        )
    )
    for sig_id in signal_ids:
        link = RequirementSignalLink(
            id=str(uuid.uuid4()),
            requirement_id=requirement_id,
            signal_id=sig_id,
        )
        db.add(link)
    await db.commit()
    return {'success': True}


@router.get('/{requirement_id}')
async def get_links(requirement_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RequirementSignalLink).where(
            RequirementSignalLink.requirement_id == requirement_id
        )
    )
    links = result.scalars().all()
    return {
        'success': True,
        'data': [{'requirementId': l.requirement_id, 'signalId': l.signal_id} for l in links],
    }


@router.delete('/{requirement_id}/{signal_id}')
async def delete_link(requirement_id: str, signal_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        delete(RequirementSignalLink).where(
            RequirementSignalLink.requirement_id == requirement_id,
            RequirementSignalLink.signal_id == signal_id,
        )
    )
    await db.commit()
    return {'success': True}
