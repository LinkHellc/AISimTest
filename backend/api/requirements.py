import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db, get_db_session
from models.base import Requirement as RequirementModel, LLMConfig as LLMConfigModel
from core.doc_parser import parse_docx_with_llm
from core.interface_parser import parse_requirement_interface_excel
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
            signal_interfaces=req.signal_interfaces,
            scene_description=req.scene_description,
            function_description=req.function_description,
            entry_condition=req.entry_condition,
            execution_body=req.execution_body,
            exit_condition=req.exit_condition,
            post_exit_behavior=req.post_exit_behavior,
        )
        db.add(db_req)
    await db.commit()

    return {'success': True, 'data': [
        {
            'id': r.id,
            'title': r.title,
            'signalInterfaces': r.signal_interfaces or [],
            'sceneDescription': r.scene_description or '',
            'functionDescription': r.function_description or '',
            'entryCondition': r.entry_condition or '',
            'executionBody': r.execution_body or '',
            'exitCondition': r.exit_condition or '',
            'postExitBehavior': r.post_exit_behavior or '',
            'testModel': getattr(r, 'test_model', '') or '',
            'testUnitModel': getattr(r, 'test_unit_model', '') or '',
        }
        for r in parsed
    ]}


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
                'signalInterfaces': r.signal_interfaces or [],
                'sceneDescription': r.scene_description or '',
                'functionDescription': r.function_description or '',
                'entryCondition': r.entry_condition or '',
                'executionBody': r.execution_body or '',
                'exitCondition': r.exit_condition or '',
                'postExitBehavior': r.post_exit_behavior or '',
                'testModel': r.test_model or '',
                'testUnitModel': r.test_unit_model or '',
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
        'signalInterfaces': 'signal_interfaces',
        'sceneDescription': 'scene_description',
        'functionDescription': 'function_description',
        'entryCondition': 'entry_condition',
        'executionBody': 'execution_body',
        'exitCondition': 'exit_condition',
        'postExitBehavior': 'post_exit_behavior',
        'testModel': 'test_model',
        'testUnitModel': 'test_unit_model',
    }
    for key, column in column_map.items():
        if key in data:
            setattr(req, column, data[key])

    await db.commit()
    return {'success': True}


@router.delete('/{req_id}')
async def delete_requirement(req_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RequirementModel).where(RequirementModel.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail='需求不存在')
    await db.execute(delete(RequirementModel).where(RequirementModel.id == req_id))
    await db.commit()
    return {'success': True}


@router.post('/{req_id}/interfaces')
async def upload_requirement_interface(
    req_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传接口表 Excel，为指定需求导入信号接口（追加到 signalInterfaces 列表）"""
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail='仅支持 .xlsx/.xls 格式')

    # 查找需求
    result = await db.execute(select(RequirementModel).where(RequirementModel.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail='需求不存在')

    # 保存临时文件
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f'{uuid.uuid4()}_{file.filename}')
    with open(temp_path, 'wb') as f:
        f.write(await file.read())

    try:
        interfaces = parse_requirement_interface_excel(temp_path)
        # 以最新导入为准：直接替换现有信号列表
        new_signals = []
        for iface in interfaces:
            if iface.signal_name:
                new_signals.append({'name': iface.signal_name, 'type': iface.interface_name})

        req.signal_interfaces = new_signals
        await db.commit()
        return {
            'success': True,
            'data': {
                'added': len(new_signals),
                'total': len(new_signals),
                'signals': new_signals,
            }
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
