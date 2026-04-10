import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet

from database import get_db, DATA_DIR
from models.base import LLMConfig as LLMConfigModel

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

    return {
        'success': True,
        'data': {
            'provider': config.provider,
            'apiKey': masked_key,
            'baseUrl': config.base_url,
            'model': config.model,
            'temperature': config.temperature,
            'maxTokens': config.max_tokens,
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

    await db.commit()
    return {'success': True}


@router.post('/llm/test')
async def test_llm_connection(data: dict, db: AsyncSession = Depends(get_db)):
    import httpx

    api_key = data.get('apiKey', '')
    base_url = data.get('baseUrl', 'https://api.openai.com/v1')
    model = data.get('model', 'gpt-4')

    if not api_key or '***' in api_key:
        result = await db.execute(select(LLMConfigModel).where(LLMConfigModel.id == 'default'))
        config = result.scalar_one_or_none()
        if config and config.api_key:
            try:
                api_key = decrypt_value(config.api_key)
            except Exception:
                pass

    if not api_key:
        return {'success': True, 'data': {'success': False, 'message': 'API Key 未配置'}}

    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
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
