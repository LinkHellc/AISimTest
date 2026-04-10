import re
import json
import asyncio
import uuid
from typing import List, Optional
from docx import Document
from pydantic import BaseModel
from openai import OpenAI


class ParsedRequirement(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    parent_id: Optional[str] = None
    source_location: str
    level: int


# ---------- 文档文本提取 ----------

def extract_docx_text(file_path: str) -> str:
    """提取 Word 文档的全部文本内容（段落 + 表格），保留结构"""
    doc = Document(file_path)
    parts: List[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            line = ' | '.join(cells)
            if line.strip('| '):
                parts.append(line)

    return '\n'.join(parts)


# ---------- LLM 需求解析 Prompt ----------

DOC_PARSE_SYSTEM_PROMPT = """你是一名汽车空调热管理系统的需求分析专家。你的任务是阅读用户提供的需求文档原始文本，将其条目化为结构化的需求列表。

解析原则：
1. 识别文档中的章节标题、功能模块名、信号接口、场景描述等，作为独立的需求条目
2. 每条需求必须有明确的标题和完整的描述内容
3. 识别父子层级关系（如"5.9.2"是"5.9.2.3"的父级）
4. 将触发条件、执行逻辑、退出条件等归类到对应需求的描述中
5. 如果文档中有信号名称（如 gCbnSys_xxx、gCAN_xxx），在描述中保留这些信号名
6. 如果文档中引用了具体参数值（如 BltCallSts=0x1），也完整保留
7. 尽可能保留文档中的所有信息，不要遗漏

输出格式为 JSON 数组，每个元素结构如下：
{
  "id": "需求编号，如文档中的 5.9.2.1 或自动生成的 REQ-001",
  "title": "需求标题，简明扼要",
  "description": "需求的完整描述，包含所有条件、逻辑、信号引用等详细信息",
  "acceptanceCriteria": ["验收标准1", "验收标准2"],
  "parentId": "父级需求ID，顶级需求为 null",
  "level": 层级数字，顶级为1
}"""


DOC_PARSE_USER_TEMPLATE = """请解析以下需求文档原始文本，将其条目化为结构化需求列表：

---
{doc_text}
---

请仔细阅读以上文档内容，将其分解为结构化的需求条目。只输出 JSON 数组，不要输出其他内容。"""


# ---------- JSON 解析 ----------

def _parse_json_response(content: str) -> list[dict]:
    """从 LLM 响应中提取 JSON 数组"""
    # 直接解析
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # markdown code block
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if m:
        try:
            result = json.loads(m.group(1))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # 找 [ ] 包裹内容
    m = re.search(r'\[.*\]', content, re.DOTALL)
    if m:
        try:
            result = json.loads(m.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(f'无法解析 LLM 响应为 JSON，原始内容: {content[:300]}')


# ---------- LLM 需求解析 ----------

async def parse_docx_with_llm(file_path: str, llm_config: dict) -> List[ParsedRequirement]:
    """使用 LLM 解析 Word 文档"""
    doc_text = extract_docx_text(file_path)

    if not doc_text.strip():
        raise ValueError('文档内容为空')

    user_prompt = DOC_PARSE_USER_TEMPLATE.format(doc_text=doc_text)

    def _call_llm():
        client = OpenAI(
            api_key=llm_config['api_key'],
            base_url=llm_config['base_url'],
        )
        response = client.chat.completions.create(
            model=llm_config['model'],
            messages=[
                {'role': 'system', 'content': DOC_PARSE_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ''

    content = await asyncio.to_thread(_call_llm)
    parsed_raw = _parse_json_response(content)

    # 转换为 ParsedRequirement，确保必填字段
    requirements: List[ParsedRequirement] = []
    seen_ids: set = set()

    for item in parsed_raw:
        req_id = str(item.get('id', '')).strip()
        if not req_id:
            req_id = f"REQ-{len(requirements) + 1:03d}"

        # 去重
        original_id = req_id
        counter = 1
        while req_id in seen_ids:
            req_id = f"{original_id}-{counter}"
            counter += 1
        seen_ids.add(req_id)

        title = str(item.get('title', '')).strip()
        description = str(item.get('description', '')).strip()
        criteria = item.get('acceptanceCriteria', item.get('acceptance_criteria', []))
        if isinstance(criteria, str):
            criteria = [c.strip() for c in criteria.split('\n') if c.strip()]
        parent_id = item.get('parentId', item.get('parent_id'))
        level = int(item.get('level', 1))

        req = ParsedRequirement(
            id=req_id,
            title=title or req_id,
            description=description,
            acceptance_criteria=criteria or [],
            parent_id=str(parent_id) if parent_id and str(parent_id) != 'None' and str(parent_id).strip() else None,
            source_location=f"LLM解析: {title[:50]}" if title else 'LLM解析',
            level=max(1, min(level, 6)),
        )
        requirements.append(req)

    return requirements
