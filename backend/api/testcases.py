import uuid
import re
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import TestCase as TestCaseModel, Requirement as RequirementModel, SignalLibrary as SignalLibraryModel
from core.llm_adapter import generate_test_cases_for_requirement, generation_log_store
from core.exporter import export_to_excel, export_to_word

router = APIRouter(prefix='/api/testcases', tags=['testcases'])


def validate_test_cases_against_interface(test_cases: list[dict], signal_interfaces: list[dict]) -> list[dict]:
    """
    用需求的接口信号定义验证测试用例中的信号是否有效
    这是场景测试前的最终检查，确保测试用例只使用接口定义的信号

    返回警告列表，每个警告包含:
    - case_name: 测试用例名称
    - step_name: 步骤名称
    - invalid_signals: TestStepAction中使用的无效信号
    - invalid_verify_signals: TestVerify中使用的无效信号
    """
    # 收集接口定义中的所有有效信号名
    valid_signals = set()
    for si in signal_interfaces:
        name = si.get('name')
        if name:
            valid_signals.add(name)
            # 也注册不带前缀的简称
            for prefix in ['gCbnSys_', 'gCAN_', 'gCbnHMI_', 'gCbnSpc_', 'gCbnBAT_', 'gCbnAC_', 'lCCU_', 'lVCCU_']:
                if name.startswith(prefix):
                    valid_signals.add(name[len(prefix):])
                    break

    # 常见的中间变量名（不视为信号）
    common_vars = {'Cnt', 'i', 'j', 'k', 'temp', 'tmp', 'flag', 't', 'et', 'msec', 'sec'}

    warnings = []
    for case in test_cases:
        case_name = case.get('name', '未命名')
        steps = case.get('steps', [])
        for step in steps:
            step_name = step.get('TestStepName', '未知步骤')
            action = step.get('TestStepAction', '') or step.get('TestAction', '') or ''
            verify = step.get('TestVerify', '') or ''

            # 检查 TestStepAction 中的信号
            assigned_signals = re.findall(r'\b([\w.]+)\s*=', action)
            invalid_action = []
            for sig in assigned_signals:
                if sig in common_vars:
                    continue
                is_valid = any(sig == v or sig.endswith('.' + v) or sig.endswith('_' + v) for v in valid_signals)
                if not is_valid:
                    invalid_action.append(sig)

            # 检查 TestVerify 中的信号
            verify_signals = re.findall(r'verify\s*\(\s*([\w.]+)', verify)
            invalid_verify = []
            for sig in verify_signals:
                if sig in common_vars:
                    continue
                is_valid = any(sig == v or sig.endswith('.' + v) or sig.endswith('_' + v) for v in valid_signals)
                if not is_valid:
                    invalid_verify.append(sig)

            if invalid_action or invalid_verify:
                warnings.append({
                    'case_name': case_name,
                    'step_name': step_name,
                    'invalid_signals': list(set(invalid_action)),
                    'invalid_verify_signals': list(set(invalid_verify)),
                })
    return warnings


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

    sig_result = await db.execute(select(SignalLibraryModel))
    all_signals = {s.name: s for s in sig_result.scalars().all()}

    all_test_cases = []
    all_warnings = []
    for req in requirements:
        req_dict = {
            'id': req.id,
            'title': req.title,
            'scene_description': req.scene_description or '',
            'function_description': req.function_description or '',
            'entry_condition': req.entry_condition or '',
            'execution_body': req.execution_body or '',
            'exit_condition': req.exit_condition or '',
            'post_exit_behavior': req.post_exit_behavior or '',
        }
        # 获取该需求关联的信号，精确匹配信号库
        signals_dict = []
        for si in (req.signal_interfaces or []):
            name = si.get('name')
            if not name:
                continue
            # 精确匹配
            if name in all_signals:
                sig = all_signals[name]
                signals_dict.append({
                    'name': name,
                    'description': sig.description or '',  # 中文描述
                    'data_type': sig.data_type or '',
                    'unit': sig.unit or '',
                    'value_table': sig.value_table or '',  # 值表
                    'initial_value': sig.initial_value or '',
                    'factor': sig.factor or 1.0,
                    'offset': sig.offset or 0.0,
                    'min_value': sig.min_value if sig.min_value is not None else 0.0,
                    'max_value': sig.max_value if sig.max_value is not None else 0.0,
                })
            # 未匹配的接口信号（不在信号库中）也保留，让LLM知道有这些信号但无详细信息
            else:
                signals_dict.append({
                    'name': name,
                    'description': si.get('description', ''),
                    'data_type': 'unknown',
                    'unit': '',
                    'value_table': '',
                    'initial_value': '',
                    'factor': 1.0,
                    'offset': 0.0,
                    'min_value': 0,
                    'max_value': 0,
                })
        try:
            cases, _log_id, warnings = await generate_test_cases_for_requirement(req_dict, signals_dict or None)

            # 【关键检查】用需求的接口信号定义验证测试用例中的信号
            interface_warnings = validate_test_cases_against_interface(cases, req.signal_interfaces or [])
            if interface_warnings:
                for w in interface_warnings:
                    all_warnings.append({
                        'requirement_id': req.id,
                        'requirement_title': req.title,
                        **w
                    })

            all_test_cases.extend(cases)
            all_warnings.extend(warnings)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'生成失败 (需求 {req.id}): {str(e)}')

    # 替换模式：删除选中需求的旧测试用例，再插入新用例
    await db.execute(
        delete(TestCaseModel).where(TestCaseModel.requirement_id.in_(requirement_ids))
    )
    for case in all_test_cases:
        # 追加模式：同一需求的测试用例不删除，直接追加
        db_case = TestCaseModel(
            id=case['id'],
            name=case['name'],
            requirement_id=case['requirementId'],
            precondition=case['precondition'],
            test_time=str(case.get('testTime', 4)),
            steps=case['steps'],
            expected_result=case.get('expectedResult', ''),
            category=case['category'],
            signal_refs=case.get('signals', []),
            test_model=case.get('testModel', ''),
            test_unit_model=case.get('testUnitModel', ''),
        )
        db.add(db_case)
    await db.commit()

    return {'success': True, 'data': all_test_cases, 'warnings': all_warnings}


@router.get('/logs')
async def get_generation_logs():
    """获取所有生成日志"""
    logs = generation_log_store.get_all()
    return {
        'success': True,
        'data': [
            {
                'id': log.id,
                'requirement_id': log.requirement_id,
                'requirement_title': log.requirement_title,
                'raw_response': log.raw_response,
                'generated_at': log.generated_at,
                'success': log.success,
                'error': log.error,
                'warnings': log.warnings,
            }
            for log in logs
        ],
    }


@router.get('/logs/{log_id}')
async def get_generation_log(log_id: str):
    """获取指定日志详情（包含完整提示词）"""
    logs = generation_log_store.get_all()
    for log in logs:
        if log.id == log_id:
            return {
                'success': True,
                'data': {
                    'id': log.id,
                    'requirement_id': log.requirement_id,
                    'requirement_title': log.requirement_title,
                    'system_prompt': log.system_prompt,
                    'user_prompt': log.user_prompt,
                    'raw_response': log.raw_response,
                    'generated_at': log.generated_at,
                    'success': log.success,
                    'error': log.error,
                    'warnings': log.warnings,
                },
            }
    raise HTTPException(status_code=404, detail='日志不存在')


@router.delete('/logs')
async def clear_generation_logs():
    """清空所有生成日志"""
    generation_log_store.clear()
    return {'success': True}


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
                'testTime': int(tc.test_time) if tc.test_time else 4,
                'steps': tc.steps or [],
                'expectedResult': tc.expected_result,
                'category': tc.category,
                'signals': tc.signal_refs or [],
                'testModel': tc.test_model or '',
                'testUnitModel': tc.test_unit_model or '',
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
        'testModel': 'test_model',
        'testUnitModel': 'test_unit_model',
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

    # 查询需求信息（标题、test_model、test_unit_model）
    req_result = await db.execute(select(RequirementModel))
    req_map = {r.id: {'title': r.title, 'test_model': r.test_model or '', 'test_unit_model': r.test_unit_model or ''}
                for r in req_result.scalars().all()}

    cases_data = [
        {
            'id': tc.id, 'name': tc.name, 'requirementId': tc.requirement_id,
            'precondition': tc.precondition, 'testTime': int(tc.test_time) if tc.test_time else 4,
            'steps': tc.steps or [],
            'expectedResult': tc.expected_result, 'category': tc.category,
            'signals': tc.signal_refs or [],
            # 从需求级别读取 testModel/testUnitModel
            'testModel': req_map.get(tc.requirement_id, {}).get('test_model', ''),
            'testUnitModel': req_map.get(tc.requirement_id, {}).get('test_unit_model', ''),
        }
        for tc in test_cases
    ]

    # 生成文件名：优先用 testModel，其次需求标题
    first_req_id = test_cases[0].requirement_id if test_cases else None
    first_test_model = req_map.get(first_req_id, {}).get('test_model', '') if first_req_id else ''
    filename = f'{first_test_model}_TestHarness.xlsx' if first_test_model else '测试用例.xlsx'

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        export_to_excel(cases_data, tmp.name, req_titles={k: v['title'] for k, v in req_map.items()})
        return FileResponse(
            tmp.name,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename,
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
