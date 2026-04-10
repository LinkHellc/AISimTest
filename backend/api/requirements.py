import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import Requirement as RequirementModel
from core.doc_parser import parse_docx

router = APIRouter(prefix='/api/requirements', tags=['requirements'])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/upload')
async def upload_requirements(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail='仅支持 .docx 格式文件')

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f'{file_id}.docx')
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    try:
        parsed = parse_docx(file_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f'文档解析失败: {str(e)}')

    await db.execute(delete(RequirementModel))
    for req in parsed:
        db_req = RequirementModel(
            id=req.id,
            title=req.title,
            description=req.description,
            acceptance_criteria=req.acceptance_criteria,
            parent_id=req.parent_id,
            source_location=req.source_location,
            level=req.level,
        )
        db.add(db_req)
    await db.commit()

    return {'success': True, 'data': [r.model_dump() for r in parsed]}


@router.get('')
async def get_requirements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RequirementModel))
    requirements = result.scalars().all()
    return {
        'success': True,
        'data': [
            {
                'id': r.id,
                'title': r.title,
                'description': r.description,
                'acceptanceCriteria': r.acceptance_criteria or [],
                'parentId': r.parent_id,
                'sourceLocation': r.source_location,
                'level': r.level,
            }
            for r in requirements
        ],
    }


@router.put('/{req_id}')
async def update_requirement(req_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RequirementModel).where(RequirementModel.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail='需求不存在')

    column_map = {
        'title': 'title',
        'description': 'description',
        'acceptanceCriteria': 'acceptance_criteria',
        'parentId': 'parent_id',
        'sourceLocation': 'source_location',
        'level': 'level',
    }
    for key, column in column_map.items():
        if key in data:
            setattr(req, column, data[key])

    await db.commit()
    return {'success': True}
