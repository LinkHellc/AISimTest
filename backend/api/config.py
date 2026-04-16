import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet

from database import get_db, DATA_DIR
from models.base import LLMConfig as LLMConfigModel, PromptTemplate as PromptTemplateModel
from datetime import datetime

router = APIRouter(prefix='/api/config', tags=['config'])

KEY_FILE = os.path.join(DATA_DIR, '.secret.key')


def _get_cipher():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
    return Fernet(key)


def encrypt_value(value: str) -> str:
    return _get_cipher().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    return _get_cipher().decrypt(value.encode()).decode()


@router.get('/llm')
async def get_llm_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMConfigModel).where(LLMConfigModel.id == 'default'))
    config = result.scalar_one_or_none()

    if not config:
        return {
            'success': True,
            'data': {
                'provider': 'openai',
                'apiKey': '',
                'baseUrl': '',
                'model': 'gpt-4',
                'temperature': 0.7,
                'maxTokens': 2000,
            },
        }

    masked_key = ''
    if config.api_key:
        try:
            real_key = decrypt_value(config.api_key)
            masked_key = real_key[:8] + '***' + real_key[-4:] if len(real_key) > 12 else '***'
        except Exception:
            masked_key = '***'

    masked_group_id = ''
    if config.group_id:
        try:
            real_gid = decrypt_value(config.group_id)
            masked_group_id = real_gid[:6] + '***' if len(real_gid) > 8 else '***'
        except Exception:
            masked_group_id = '***'

    return {
        'success': True,
        'data': {
            'provider': config.provider,
            'apiKey': masked_key,
            'baseUrl': config.base_url,
            'model': config.model,
            'temperature': config.temperature,
            'maxTokens': config.max_tokens,
            'groupId': masked_group_id,
        },
    }


@router.put('/llm')
async def update_llm_config(data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMConfigModel).where(LLMConfigModel.id == 'default'))
    config = result.scalar_one_or_none()

    if not config:
        config = LLMConfigModel(id='default')
        db.add(config)

    if 'provider' in data:
        config.provider = data['provider']
    if 'baseUrl' in data:
        config.base_url = data['baseUrl']
    if 'model' in data:
        config.model = data['model']
    if 'temperature' in data:
        config.temperature = float(data['temperature'])
    if 'maxTokens' in data:
        config.max_tokens = int(data['maxTokens'])
    if 'apiKey' in data and data['apiKey'] and '***' not in data['apiKey']:
        config.api_key = encrypt_value(data['apiKey'])
    if 'groupId' in data and data['groupId'] and '***' not in data['groupId']:
        config.group_id = encrypt_value(data['groupId'])

    await db.commit()
    return {'success': True}


@router.post('/llm/test')
async def test_llm_connection(data: dict, db: AsyncSession = Depends(get_db)):
    import httpx

    api_key = data.get('apiKey', '')
    base_url = data.get('baseUrl', 'https://api.openai.com/v1')
    model = data.get('model', 'gpt-4')
    group_id = data.get('groupId', '')

    if not api_key or '***' in api_key:
        result = await db.execute(select(LLMConfigModel).where(LLMConfigModel.id == 'default'))
        config = result.scalar_one_or_none()
        if config and config.api_key:
            try:
                api_key = decrypt_value(config.api_key)
            except Exception:
                pass
        if config and getattr(config, 'group_id', None):
            group_id = decrypt_value(config.group_id) if config.group_id else group_id

    if not api_key:
        return {'success': True, 'data': {'success': False, 'message': 'API Key 未配置'}}

    try:
        # MiniMax M2 系列使用不同的端点
        is_minimax = 'minimax' in base_url.lower() and model and 'MiniMax-M2' in model
        if is_minimax:
            # MiniMax API 需要 /v1 前缀
            url = f"{base_url.rstrip('/')}/v1/text/chatcompletion_v2"
        else:
            url = f"{base_url.rstrip('/')}/chat/completions"

        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        if group_id:
            headers['GroupId'] = group_id

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': 'Hi, reply with "OK".'}],
                    'max_tokens': 10,
                },
            )
        if response.status_code == 200:
            return {'success': True, 'data': {'success': True, 'message': '连接成功'}}
        else:
            error_msg = response.json().get('error', {}).get('message', f'HTTP {response.status_code}')
            return {'success': True, 'data': {'success': False, 'message': error_msg}}
    except Exception as e:
        return {'success': True, 'data': {'success': False, 'message': str(e)}}


# ========== 提示词模板 API ==========

@router.get('/prompts')
async def get_prompt_templates(db: AsyncSession = Depends(get_db)):
    """获取所有提示词模板"""
    from core.prompt_templates import TEST_CASE_SYSTEM_PROMPT, TEST_CASE_USER_TEMPLATE

    defaults = {
        'test_case_system': (TEST_CASE_SYSTEM_PROMPT, '测试用例生成 - System Prompt'),
        'test_case_user': (TEST_CASE_USER_TEMPLATE, '测试用例生成 - User Prompt'),
    }

    # Initialize default templates if not exist
    for template_id, (content, description) in defaults.items():
        result = await db.execute(select(PromptTemplateModel).where(PromptTemplateModel.id == template_id))
        template = result.scalar_one_or_none()
        if not template:
            template = PromptTemplateModel(
                id=template_id,
                content=content,
                description=description,
                updated_at=datetime.now().isoformat(),
            )
            db.add(template)
    await db.commit()

    result = await db.execute(select(PromptTemplateModel))
    templates = result.scalars().all()
    return {
        'success': True,
        'data': [
            {
                'id': t.id,
                'name': t.description or t.id.replace('_', ' ').title(),
                'content': t.content,
                'description': t.description,
                'updated_at': t.updated_at,
            }
            for t in templates
        ],
    }


@router.put('/prompts/{template_id}')
async def update_prompt_template(template_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """更新提示词模板"""
    result = await db.execute(select(PromptTemplateModel).where(PromptTemplateModel.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        template = PromptTemplateModel(id=template_id)
        db.add(template)

    if 'content' in data:
        template.content = data['content']
    if 'description' in data:
        template.description = data['description']
    template.updated_at = datetime.now().isoformat()

    await db.commit()
    return {'success': True}


@router.post('/prompts/{template_id}/reset')
async def reset_prompt_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """重置提示词模板到默认值"""
    from core.prompt_templates import TEST_CASE_SYSTEM_PROMPT, TEST_CASE_USER_TEMPLATE

    defaults = {
        'test_case_system': (TEST_CASE_SYSTEM_PROMPT, '测试用例生成 - System Prompt'),
        'test_case_user': (TEST_CASE_USER_TEMPLATE, '测试用例生成 - User Prompt'),
    }

    if template_id not in defaults:
        raise HTTPException(status_code=404, detail='未知模板')

    content, description = defaults[template_id]
    result = await db.execute(select(PromptTemplateModel).where(PromptTemplateModel.id == template_id))
    template = result.scalar_one_or_none()

    if template:
        template.content = content
        template.description = description
        template.updated_at = datetime.now().isoformat()
    else:
        template = PromptTemplateModel(
            id=template_id,
            content=content,
            description=description,
            updated_at=datetime.now().isoformat(),
        )
        db.add(template)

    await db.commit()
    return {'success': True}
