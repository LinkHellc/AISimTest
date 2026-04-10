import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import Signal as SignalModel
from core.signal_parser import parse_signal_excel

router = APIRouter(prefix='/api/signals', tags=['signals'])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/upload')
async def upload_signals(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail='仅支持 .xlsx/.xls 格式文件')

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f'{file_id}.xlsx')
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    try:
        parsed = parse_signal_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f'信号矩阵解析失败: {str(e)}')

    await db.execute(delete(SignalModel))
    for sig in parsed:
        db_sig = SignalModel(
            id=sig.id,
            name=sig.name,
            message_id=sig.message_id,
            start_bit=sig.start_bit,
            length=sig.length,
            factor=sig.factor,
            offset=sig.offset,
            min_value=sig.min_value,
            max_value=sig.max_value,
            unit=sig.unit,
            bus_type=sig.bus_type,
            class_type=sig.class_type,
            data_type=sig.data_type,
            description=sig.description,
        )
        db.add(db_sig)
    await db.commit()

    return {'success': True, 'data': [s.model_dump() for s in parsed]}


@router.get('')
async def get_signals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SignalModel))
    signals = result.scalars().all()
    return {
        'success': True,
        'data': [
            {
                'id': s.id,
                'name': s.name,
                'messageId': s.message_id,
                'startBit': s.start_bit,
                'length': s.length,
                'factor': s.factor,
                'offset': s.offset,
                'minValue': s.min_value,
                'maxValue': s.max_value,
                'unit': s.unit,
                'busType': s.bus_type,
                'classType': s.class_type,
                'dataType': s.data_type,
                'description': s.description,
            }
            for s in signals
        ],
    }
