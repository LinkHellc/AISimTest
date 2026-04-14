"""
信号库 API - 管理全局信号定义库
"""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.dialects.sqlite import insert

from database import get_db
from models.base import SignalLibrary
from core.interface_parser import parse_signal_library_excel, parse_signal_library_directory

router = APIRouter(prefix='/api/signals/library', tags=['signal-library'])


# ---------- 上传接口表 Excel ----------

@router.post('/upload')
async def upload_signal_library(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传单个接口表 Excel，智能合并到信号库"""
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail='仅支持 .xlsx/.xls 格式')

    # 保存临时文件
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f'{uuid.uuid4()}_{file.filename}')

    with open(temp_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    try:
        # 解析 Excel
        parsed_signals = parse_signal_library_excel(temp_path)

        if not parsed_signals:
            return {'success': True, 'data': {'added': 0, 'updated': 0, 'message': '未找到有效信号数据'}}

        # 智能合并：按 name 去重，已存在则更新字段，新增则插入
        added = 0
        updated = 0

        for sig in parsed_signals:
            # 检查是否已存在
            result = await db.execute(
                select(SignalLibrary).where(SignalLibrary.name == sig.name)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新字段
                existing.description = sig.description
                existing.data_type = sig.data_type
                existing.unit = sig.unit
                existing.value_table = sig.value_table
                existing.initial_value = sig.initial_value
                existing.bus = sig.bus
                existing.storage_class = sig.storage_class
                existing.dimension = sig.dimension
                existing.factor = sig.factor
                existing.offset = sig.offset
                existing.min_value = sig.min_value
                existing.max_value = sig.max_value
                existing.source_file = sig.source_file
                updated += 1
            else:
                # 新增
                db.add(SignalLibrary(
                    id=str(uuid.uuid4()),
                    name=sig.name,
                    description=sig.description,
                    data_type=sig.data_type,
                    unit=sig.unit,
                    value_table=sig.value_table,
                    initial_value=sig.initial_value,
                    bus=sig.bus,
                    storage_class=sig.storage_class,
                    dimension=sig.dimension,
                    factor=sig.factor,
                    offset=sig.offset,
                    min_value=sig.min_value,
                    max_value=sig.max_value,
                    source_file=sig.source_file,
                ))
                added += 1

        await db.commit()

        return {
            'success': True,
            'data': {
                'added': added,
                'updated': updated,
                'total': added + updated
            }
        }

    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post('/upload-batch')
async def upload_signal_library_batch(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """批量上传多个接口表 Excel"""
    total_added = 0
    total_updated = 0

    for file in files:
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            continue

        # 保存临时文件
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f'{uuid.uuid4()}_{file.filename}')

        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        try:
            parsed_signals = parse_signal_library_excel(temp_path)

            for sig in parsed_signals:
                result = await db.execute(
                    select(SignalLibrary).where(SignalLibrary.name == sig.name)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.description = sig.description
                    existing.data_type = sig.data_type
                    existing.unit = sig.unit
                    existing.value_table = sig.value_table
                    existing.initial_value = sig.initial_value
                    existing.bus = sig.bus
                    existing.storage_class = sig.storage_class
                    existing.dimension = sig.dimension
                    existing.factor = sig.factor
                    existing.offset = sig.offset
                    existing.min_value = sig.min_value
                    existing.max_value = sig.max_value
                    existing.source_file = sig.source_file
                    total_updated += 1
                else:
                    db.add(SignalLibrary(
                        id=str(uuid.uuid4()),
                        name=sig.name,
                        description=sig.description,
                        data_type=sig.data_type,
                        unit=sig.unit,
                        value_table=sig.value_table,
                        initial_value=sig.initial_value,
                        bus=sig.bus,
                        storage_class=sig.storage_class,
                        dimension=sig.dimension,
                        factor=sig.factor,
                        offset=sig.offset,
                        min_value=sig.min_value,
                        max_value=sig.max_value,
                        source_file=sig.source_file,
                    ))
                    total_added += 1

        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    await db.commit()

    return {
        'success': True,
        'data': {
            'added': total_added,
            'updated': total_updated,
            'total': total_added + total_updated
        }
    }


# ---------- 查询信号库 ----------

@router.get('')
async def get_signal_library(
    search: Optional[str] = Query(None, description='搜索信号名或描述'),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """获取信号库列表，支持搜索和分页"""
    query = select(SignalLibrary)

    if search:
        search_pattern = f'%{search}%'
        query = query.where(
            or_(
                SignalLibrary.name.ilike(search_pattern),
                SignalLibrary.description.ilike(search_pattern)
            )
        )

    # 获取总数
    count_query = select(SignalLibrary.id)
    if search:
        count_query = count_query.where(
            or_(
                SignalLibrary.name.ilike(f'%{search}%'),
                SignalLibrary.description.ilike(f'%{search}%')
            )
        )
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    signals = result.scalars().all()

    return {
        'success': True,
        'data': {
            'items': [_signal_to_dict(s) for s in signals],
            'total': total,
            'page': page,
            'pageSize': page_size
        }
    }


@router.get('/names')
async def get_signal_names(
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取信号名列表（用于自动补全）"""
    query = select(SignalLibrary.name)

    if search:
        query = query.where(SignalLibrary.name.ilike(f'%{search}%'))

    query = query.limit(limit)
    result = await db.execute(query)
    names = result.scalars().all()

    return {'success': True, 'data': list(names)}


@router.get('/{signal_name}')
async def get_signal_by_name(
    signal_name: str,
    db: AsyncSession = Depends(get_db)
):
    """按名称查询信号详情"""
    result = await db.execute(
        select(SignalLibrary).where(SignalLibrary.name == signal_name)
    )
    signal = result.scalar_one_or_none()

    if not signal:
        return {'success': False, 'error': '信号不存在'}

    return {'success': True, 'data': _signal_to_dict(signal)}


def _signal_to_dict(signal: SignalLibrary) -> dict:
    """转换为字典"""
    return {
        'id': signal.id,
        'name': signal.name,
        'description': signal.description,
        'dataType': signal.data_type,
        'unit': signal.unit,
        'valueTable': signal.value_table,
        'initialValue': signal.initial_value,
        'bus': signal.bus,
        'storageClass': signal.storage_class,
        'dimension': signal.dimension,
        'factor': signal.factor,
        'offset': signal.offset,
        'minValue': signal.min_value,
        'maxValue': signal.max_value,
        'sourceFile': signal.source_file,
    }
