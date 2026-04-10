import uuid
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import TestCase as TestCaseModel, Requirement as RequirementModel, Signal as SignalModel
from core.llm_adapter import generate_test_cases_for_requirement
from core.exporter import export_to_excel, export_to_word

router = APIRouter(prefix='/api/testcases', tags=['testcases'])


@router.post('/generate')
async def generate_test_cases(data: dict, db: AsyncSession = Depends(get_db)):
    requirement_ids = data.get('requirementIds', [])
    if not requirement_ids:
        raise HTTPException(status_code=400, detail='请选择至少一条需求')

    result = await db.execute(
        select(RequirementModel).where(RequirementModel.id.in_(requirement_ids))
    )
    requirements = result.scalars().all()
    if not requirements:
        raise HTTPException(status_code=404, detail='未找到选中的需求')

    sig_result = await db.execute(select(SignalModel))
    all_signals = sig_result.scalars().all()

    all_test_cases = []
    for req in requirements:
        req_dict = {
            'id': req.id,
            'title': req.title,
            'description': req.description,
            'acceptance_criteria': req.acceptance_criteria or [],
        }
        signals_dict = [
            {'name': s.name, 'min_value': s.min_value, 'max_value': s.max_value,
             'factor': s.factor, 'offset': s.offset, 'unit': s.unit}
            for s in all_signals
        ]
        try:
            cases = await generate_test_cases_for_requirement(req_dict, signals_dict or None)
            all_test_cases.extend(cases)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'生成失败 (需求 {req.id}): {str(e)}')

    for case in all_test_cases:
        db_case = TestCaseModel(
            id=case['id'],
            name=case['name'],
            requirement_id=case['requirementId'],
            precondition=case['precondition'],
            steps=case['steps'],
            expected_result=case['expectedResult'],
            category=case['category'],
            signal_refs=case.get('signals', []),
        )
        db.add(db_case)
    await db.commit()

    return {'success': True, 'data': all_test_cases}


@router.get('')
async def get_test_cases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestCaseModel))
    test_cases = result.scalars().all()
    return {
        'success': True,
        'data': [
            {
                'id': tc.id,
                'name': tc.name,
                'requirementId': tc.requirement_id,
                'precondition': tc.precondition,
                'steps': tc.steps or [],
                'expectedResult': tc.expected_result,
                'category': tc.category,
                'signals': tc.signal_refs or [],
            }
            for tc in test_cases
        ],
    }


@router.put('/{tc_id}')
async def update_test_case(tc_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestCaseModel).where(TestCaseModel.id == tc_id))
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail='测试用例不存在')

    field_map = {
        'name': 'name',
        'precondition': 'precondition',
        'steps': 'steps',
        'expectedResult': 'expected_result',
        'category': 'category',
    }
    for key, column in field_map.items():
        if key in data:
            setattr(tc, column, data[key])

    await db.commit()
    return {'success': True}


@router.delete('/{tc_id}')
async def delete_test_case(tc_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(TestCaseModel).where(TestCaseModel.id == tc_id))
    await db.commit()
    return {'success': True}


@router.post('/export/excel')
async def export_test_cases_excel(data: dict, db: AsyncSession = Depends(get_db)):
    ids = data.get('ids')
    query = select(TestCaseModel)
    if ids:
        query = query.where(TestCaseModel.id.in_(ids))
    result = await db.execute(query)
    test_cases = result.scalars().all()
    if not test_cases:
        raise HTTPException(status_code=404, detail='没有可导出的测试用例')

    cases_data = [
        {
            'id': tc.id, 'name': tc.name, 'requirementId': tc.requirement_id,
            'precondition': tc.precondition, 'steps': tc.steps or [],
            'expectedResult': tc.expected_result, 'category': tc.category,
            'signals': tc.signal_refs or [],
        }
        for tc in test_cases
    ]

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        export_to_excel(cases_data, tmp.name)
        return FileResponse(
            tmp.name,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename='测试用例.xlsx',
        )


@router.post('/export/word')
async def export_test_cases_word(data: dict, db: AsyncSession = Depends(get_db)):
    ids = data.get('ids')
    query = select(TestCaseModel)
    if ids:
        query = query.where(TestCaseModel.id.in_(ids))
    result = await db.execute(query)
    test_cases = result.scalars().all()
    if not test_cases:
        raise HTTPException(status_code=404, detail='没有可导出的测试用例')

    cases_data = [
        {
            'id': tc.id, 'name': tc.name, 'requirementId': tc.requirement_id,
            'precondition': tc.precondition, 'steps': tc.steps or [],
            'expectedResult': tc.expected_result, 'category': tc.category,
            'signals': tc.signal_refs or [],
        }
        for tc in test_cases
    ]

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        export_to_word(cases_data, tmp.name)
        return FileResponse(
            tmp.name,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename='测试用例.docx',
        )
