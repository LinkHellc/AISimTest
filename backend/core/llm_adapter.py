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

    # Try to find [ ] wrapped content
    bracket_match = re.search(r'\[.*\]', content, re.DOTALL)
    if bracket_match:
        try:
            result = json.loads(bracket_match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(f'无法解析 LLM 响应为 JSON，原始内容: {content[:200]}')


async def generate_test_cases_for_requirement(
    requirement: dict,
    signals: list[dict] | None = None,
    num_cases: int = 5,
) -> list[dict]:
    config = await _get_llm_config()

    system_prompt, user_prompt = build_test_case_prompt(
        requirement_id=requirement['id'],
        requirement_title=requirement['title'],
        requirement_description=requirement.get('description', ''),
        acceptance_criteria=requirement.get('acceptance_criteria', []),
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
            max_tokens=config['max_tokens'],
        )
        return response.choices[0].message.content or ''

    content = await asyncio.to_thread(_call_llm)
    parsed_cases = _parse_json_response(content)

    test_cases = []
    for case in parsed_cases:
        test_cases.append({
            'id': f'TC-{uuid.uuid4().hex[:8]}',
            'name': case.get('name', '未命名用例'),
            'requirementId': requirement['id'],
            'precondition': case.get('precondition', ''),
            'steps': case.get('steps', []),
            'expectedResult': case.get('expectedResult', ''),
            'category': case.get('category', 'positive'),
            'signals': signals or [],
        })

    return test_cases
