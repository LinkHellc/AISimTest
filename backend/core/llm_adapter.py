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

        return {
            'provider': config.provider,
            'api_key': api_key,
            'base_url': config.base_url or 'https://api.openai.com/v1',
            'model': config.model,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
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


async def generate_test_cases_for_requirement(
    requirement: dict,
    signals: list[dict] | None = None,
    num_cases: int = 5,
) -> list[dict]:
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
        raise RuntimeError(f'LLM 调用失败（已重试3次）: {last_error}')
    parsed_cases = _parse_json_response(content)

    test_cases = []
    for case in parsed_cases:
        test_cases.append({
            'id': f'TC-{uuid.uuid4().hex[:8]}',
            'name': case.get('name', '未命名用例'),
            'requirementId': requirement['id'],
            'precondition': case.get('precondition', ''),
            'testTime': case.get('testTime', 4),
            'steps': case.get('steps', []),
            'category': case.get('category', 'positive'),
            'signals': signals or [],
        })

    return test_cases
