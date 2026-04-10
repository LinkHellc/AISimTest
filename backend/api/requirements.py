import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db, get_db_session
from models.base import Requirement as RequirementModel, LLMConfig as LLMConfigModel
from core.doc_parser import parse_docx_with_llm
from api.config import decrypt_value

router = APIRouter(prefix='/api/requirements', tags=['requirements'])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def _get_llm_config() -> dict:
    """从数据库获取 LLM 配置用于文档解析"""
    async with get_db_session() as session:
        result = await session.execute(
            select(LLMConfigModel).where(LLMConfigModel.id == 'default')
        )
        config = result.scalar_one_or_none()
        if not config or not config.api_key:
            raise ValueError('LLM 未配置，请先在"设置"页面配置大模型 API')

        api_key = ''
        try:
            api_key = decrypt_value(config.api_key)
        except Exception:
            raise ValueError('API Key 解密失败，请重新配置')

        return {
            'api_key': api_key,
            'base_url': config.base_url or 'https://api.openai.com/v1',
            'model': config.model,
        }


@router.post('/upload')
async def upload_requirements(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail='仅支持 .docx 格式文件')

    # 保存上传文件
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f'{file_id}.docx')
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # 获取 LLM 配置
    try:
        llm_config = await _get_llm_config()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 使用 LLM 解析文档
    try:
        parsed = await parse_docx_with_llm(file_path, llm_config)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f'文档解析失败: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'LLM 调用失败: {str(e)}')

    if not parsed:
        raise HTTPException(status_code=422, detail='LLM 未能从文档中解析出任何需求')

    # 清空旧数据并写入新数据
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
