import json
import re
import uuid
import asyncio
from typing import List, Optional
from openai import OpenAI

from database import get_db_session
from models.base import LLMConfig as LLMConfigModel
from api.config import decrypt_value
from core.prompt_templates import build_test_case_prompt


async def _get_llm_config() -> dict:
    async with get_db_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(LLMConfigModel).where(LLMConfigModel.id == 'default')
        )
        config = result.scalar_one_or_none()
        if not config:
            raise ValueError('LLM 配置未设置，请先在设置页面配置')

        api_key = ''
        if config.api_key:
            try:
                api_key = decrypt_value(config.api_key)
            except Exception:
                raise ValueError('API Key 解密失败，请重新配置')

        group_id = ''
        if config.group_id:
            try:
                group_id = decrypt_value(config.group_id)
            except Exception:
                pass

        return {
            'provider': config.provider,
            'api_key': api_key,
            'base_url': config.base_url or 'https://api.openai.com/v1',
            'model': config.model,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
            'group_id': group_id,
        }


def _parse_json_response(content: str) -> list[dict]:
    # Strip thinking blocks first (e.g., <think>...</think>)
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)

    # Try direct parse
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try from markdown code block
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Find the last [ ... ] block that parses as a list
    for match in re.finditer(r'\[.*\]', content, re.DOTALL):
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            continue

    raise ValueError(f'无法解析 LLM 响应为 JSON，原始内容: {content[:300]}')


# 支持的测试类型
VALID_TEST_TYPES = ['边界测试', '等价测试', '状态转换测试', '功能测试', '组合测试', '异常测试']

# HVAC常见信号关键词（用于推断测试类型）
TEST_TYPE_KEYWORDS = {
    '边界测试': ['边界', '最大', '最小', '临界', '极限', '最大最小', 'max', 'min', 'limit'],
    '等价测试': ['等价', '典型', '正常', '标准', '常规', '一般'],
    '状态转换测试': ['状态', '转换', '切换', 'ON', 'OFF', '开启', '关闭', '上电', '下电'],
    '功能测试': ['功能', '验证', '检查', '确认'],
    '组合测试': ['组合', '多', '同时', '复合'],
    '异常测试': ['异常', '错误', '非法', '无效', '故障', '异常'],
}


def _infer_test_type(name: str, description: str = '') -> str:
    """根据用例名称或描述推断测试类型"""
    text = (name + ' ' + description).lower()
    for test_type, keywords in TEST_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return test_type
    return '功能测试'  # 默认


def _validate_and_fix_test_case(case: dict, index: int) -> dict:
    """
    验证并修复单个测试用例的缺失字段。
    返回修复后的用例。
    检查项：
    1. testType 是否为空或无效
    2. TestStepAction 是否为空（未设置信号值）
    3. steps 字段是否完整
    """
    fixed = dict(case)

    # 1. 修复 testType
    test_type = case.get('testType', '')
    if not test_type or test_type not in VALID_TEST_TYPES:
        inferred = _infer_test_type(case.get('name', ''), case.get('precondition', ''))
        fixed['testType'] = inferred
        print(f"  [警告] 用例 #{index+1} testType 缺失/无效，已自动补充: {inferred}")

    # 2. 验证并修复 steps
    steps = case.get('steps', [])
    if not isinstance(steps, list):
        steps = []
        fixed['steps'] = steps

    fixed_steps = []
    for step_idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        fixed_step = dict(step)

        # 检查 TestStepAction 是否为空
        action = step.get('TestStepAction', step.get('TestAction', ''))
        if not action or not action.strip():
            # 尝试从 step 描述推断需要的信号设置
            step_name = step.get('TestStepName', f'TS{step_idx+1}')
            desc = step.get('TestDescription', '')
            # 如果动作空但有描述，给出警告
            print(f"  [警告] 步骤 {step_name} 的 TestStepAction 为空，请检查是否设置了信号值")
            # 不自动填充，留空会导出时暴露问题

        # 确保所有必要字段存在（使用默认值填充）
        if 'TestStepName' not in step or not step['TestStepName']:
            fixed_step['TestStepName'] = f'TS{step_idx + 1}'
        if 'TestTransition' not in step or not step['TestTransition']:
            fixed_step['TestTransition'] = 'after(1,sec)'
        if 'TestNextStepName' not in step:
            # 根据是否是最后一个步骤决定
            if step_idx == len(steps) - 1:
                fixed_step['TestNextStepName'] = 'Init'
            else:
                fixed_step['TestNextStepName'] = f'TS{step_idx + 2}'
        if 'TestVerifyName' not in step or not step['TestVerifyName']:
            fixed_step['TestVerifyName'] = f'TV{step_idx + 1}'
        if 'WhenCondition' not in step or not step['WhenCondition']:
            fixed_step['WhenCondition'] = 't>0.5 && t<4.5'
        if 'TestVerify' not in step or not step['TestVerify']:
            fixed_step['TestVerify'] = ''
        if 'TestDescription' not in step or not step['TestDescription']:
            fixed_step['TestDescription'] = f'步骤{step_idx + 1}'

        fixed_steps.append(fixed_step)

    fixed['steps'] = fixed_steps
    return fixed


import re


def validate_test_cases(test_cases: list[dict], signals: list[dict] | None) -> list[dict]:
    """
    验证测试用例是否使用了有效的信号
    返回验证警告列表，每个警告包含 case_id, step_name, invalid_signals, invalid_verify_signals
    """
    # 收集所有有效的信号名（支持带前缀和不带前缀）
    valid_signals = set()
    if signals:
        for s in signals:
            valid_signals.add(s['name'])
            # 如果信号名以 gCbnSys_ 或 gCAN_ 开头，也注册不带前缀的简称
            name = s['name']
            for prefix in ['gCbnSys_', 'gCAN_', 'gCbnHMI_', 'gCbnSpc_', 'gCbnBAT_', 'gCbnAC_', 'lCCU_', 'lVCCU_']:
                if name.startswith(prefix):
                    short_name = name[len(prefix):]
                    valid_signals.add(short_name)
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
            invalid_action_signals = []
            for sig in assigned_signals:
                # 检查是否是有效信号（完整匹配或简称匹配）
                is_valid = False
                if sig in common_vars:
                    is_valid = True
                else:
                    for valid in valid_signals:
                        if sig == valid or sig.endswith('.' + valid) or sig.endswith('_' + valid):
                            is_valid = True
                            break
                if not is_valid:
                    invalid_action_signals.append(sig)

            # 检查 TestVerify 中的信号（verify(...) 括号内的内容）
            verify_signals = re.findall(r'verify\s*\(\s*([\w.]+)', verify)
            invalid_verify_signals = []
            for sig in verify_signals:
                is_valid = False
                if sig in common_vars:
                    is_valid = True
                else:
                    for valid in valid_signals:
                        if sig == valid or sig.endswith('.' + valid) or sig.endswith('_' + valid):
                            is_valid = True
                            break
                if not is_valid:
                    invalid_verify_signals.append(sig)

            if invalid_action_signals or invalid_verify_signals:
                warnings.append({
                    'case_name': case_name,
                    'step_name': step_name,
                    'invalid_signals': list(set(invalid_action_signals)),
                    'invalid_verify_signals': list(set(invalid_verify_signals)),
                })
    return warnings


async def generate_test_cases_for_requirement(
    requirement: dict,
    signals: list[dict] | None = None,
    num_cases: int = 5,
) -> tuple[list[dict], str]:
    config = await _get_llm_config()

    # 构建完整的需求描述（8个字段）
    parts = []
    if requirement.get('scene_description'):
        parts.append(f"场景描述: {requirement['scene_description']}")
    if requirement.get('function_description'):
        parts.append(f"功能描述: {requirement['function_description']}")
    if requirement.get('entry_condition'):
        parts.append(f"功能触发条件: {requirement['entry_condition']}")
    if requirement.get('execution_body'):
        parts.append(f"功能进入后执行: {requirement['execution_body']}")
    if requirement.get('exit_condition'):
        parts.append(f"功能退出条件: {requirement['exit_condition']}")
    if requirement.get('post_exit_behavior'):
        parts.append(f"功能退出后执行: {requirement['post_exit_behavior']}")
    full_description = '\n'.join(parts) if parts else '无详细描述'

    system_prompt, user_prompt = build_test_case_prompt(
        requirement_id=requirement['id'],
        requirement_title=requirement['title'],
        requirement_description=full_description,
        acceptance_criteria=[],
        signals=signals,
        num_cases=num_cases,
    )

    # Use synchronous OpenAI client in thread pool to avoid blocking
    def _call_llm():
        # MiniMax M2 系列需要特殊处理
        is_minimax = 'minimax' in config['base_url'].lower() and 'MiniMax-M2' in config['model']
        if is_minimax:
            import httpx
            url = f"{config['base_url'].rstrip('/')}/v1/text/chatcompletion_v2"
            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json',
            }
            if config.get('group_id'):
                headers['GroupId'] = config['group_id']
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    url,
                    headers=headers,
                    json={
                        'model': config['model'],
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt},
                        ],
                        'temperature': config['temperature'],
                        'max_tokens': max(16000, config['max_tokens']),
                    },
                )
            if response.status_code != 200:
                raise RuntimeError(f'MiniMax API error: {response.status_code} - {response.text}')
            resp_data = response.json()
            return resp_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            client = OpenAI(
                api_key=config['api_key'],
                base_url=config['base_url'],
            )
            response = client.chat.completions.create(
                model=config['model'],
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=config['temperature'],
                max_tokens=max(16000, config['max_tokens']),
            )
            return response.choices[0].message.content or ''

    # 重试机制：失败后等待1秒，最多重试3次
    content = None
    last_error = None
    for attempt in range(3):
        try:
            content = await asyncio.to_thread(_call_llm)
            break
        except Exception as e:
            last_error = e
            if attempt < 2:
                import time
                time.sleep(1)
    if content is None:
        log_id = f'log-{uuid.uuid4().hex[:8]}'
        err_msg = f'LLM 调用失败（已重试3次）: {last_error}'
        # 记录失败日志
        log = GenerationLog(
            id=log_id,
            requirement_id=requirement['id'],
            requirement_title=requirement.get('title', ''),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            raw_response='',
            generated_at=datetime.now().isoformat(),
            success=False,
            error=err_msg,
        )
        generation_log_store.add(log)
        raise RuntimeError(err_msg)

    parsed_cases = _parse_json_response(content)

    # 验证并修复测试用例
    fixed_cases = []
    for i, case in enumerate(parsed_cases):
        fixed_case = _validate_and_fix_test_case(case, i)
        fixed_cases.append(fixed_case)

    test_cases = []
    for case in fixed_cases:
        test_cases.append({
            'id': f'TC-{uuid.uuid4().hex[:8]}',
            'name': case.get('name', '未命名用例'),
            'requirementId': requirement['id'],
            'precondition': case.get('precondition', ''),
            'testTime': case.get('testTime', 4),
            'steps': case.get('steps', []),
            'category': case.get('category', 'positive'),
            'testType': case.get('testType', ''),
            'signals': signals or [],
        })

    # 验证测试用例中的信号使用是否有效
    warnings = validate_test_cases(test_cases, signals)

    # 记录成功日志
    log_id = f'log-{uuid.uuid4().hex[:8]}'
    log = GenerationLog(
        id=log_id,
        requirement_id=requirement['id'],
        requirement_title=requirement.get('title', ''),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        raw_response=content,
        generated_at=datetime.now().isoformat(),
        success=True,
        warnings=warnings,
    )
    generation_log_store.add(log)

    return test_cases, log_id, warnings


# ========== 日志存储 ==========
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import threading


@dataclass
class GenerationLog:
    """单次生成的日志记录"""
    id: str
    requirement_id: str
    requirement_title: str
    system_prompt: str
    user_prompt: str
    raw_response: str
    generated_at: str
    success: bool
    error: str = ''
    warnings: list = field(default_factory=list)


class LogStore:
    """线程安全的内存日志存储，最多保留100条"""
    def __init__(self, max_size: int = 100):
        self._logs: list[GenerationLog] = []
        self._lock = threading.Lock()
        self._max_size = max_size

    def add(self, log: GenerationLog):
        with self._lock:
            self._logs.append(log)
            if len(self._logs) > self._max_size:
                self._logs.pop(0)

    def get_all(self) -> list[GenerationLog]:
        with self._lock:
            return list(reversed(self._logs))  # 最新在前

    def get_by_requirement(self, req_id: str) -> list[GenerationLog]:
        with self._lock:
            return [l for l in reversed(self._logs) if l.requirement_id == req_id]

    def clear(self):
        with self._lock:
            self._logs.clear()


# 全局日志存储实例
generation_log_store = LogStore(max_size=100)
