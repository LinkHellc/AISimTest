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
    signal_interfaces: List[str] = []   # 信号接口名称列表
    scene_description: str = ''          # 场景描述
    function_description: str = ''       # 功能描述
    entry_condition: str = ''            # 功能触发条件
    execution_body: str = ''             # 功能进入后执行
    exit_condition: str = ''            # 功能退出条件
    post_exit_behavior: str = ''        # 功能退出后执行


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

DOC_PARSE_SYSTEM_PROMPT = """你是一名汽车空调热管理系统的需求分析专家。你的任务是将需求文档原始文本解析为结构化的功能需求条目。

**一个完整需求的格式必须包含以下8个字段：**

1. **title** - 功能需求名称（如"蓝牙通话降风速"）
2. **signalInterfaces** - 信号接口列表，从文档中提取相关的输入/输出信号变量名（如 gCAN_BltCallSts、gCbnSys_xxx），支持后续 Excel 导入更新信息；若文档未提及则为空数组
3. **sceneDescription** - 场景描述，描述功能在什么工况下被触发
4. **functionDescription** - 功能描述，概括功能的整体行为
5. **entryCondition** - 功能触发条件，满足哪些条件时功能激活（如信号值、阈值、状态组合）
6. **executionBody** - 功能进入后执行，功能激活后系统执行的具体动作
7. **exitCondition** - 功能退出条件，满足哪些条件时功能退出
8. **postExitBehavior** - 功能退出后执行，功能退出后系统如何恢复或切换状态

**解析原则：**
- 章节编号（如 5.9.2.3）作为需求 ID，一个章节 = 一个需求节点
- 章节标题（"5.9.2.3 蓝牙通话降风速"）提取为 title
- 功能描述/备注/注意等信息全部归入上述8个字段，不拆分为子需求
- 保留文档中的所有信号名称、参数值（BlCallSts=0x1、FRZCU_PowerMode=0x1、温度阈值等）
- 只输出真正包含功能逻辑的章节，概述性章节（如只有标题无实质内容的）不单独成节点

输出格式为 JSON 数组，每个元素结构如下：
{
  "id": "需求编号，如 REQ-001 或文档章节号 5.9.2.3",
  "title": "功能需求名称",
  "signalInterfaces": ["信号接口名称列表"],
  "sceneDescription": "场景描述",
  "functionDescription": "功能描述",
  "entryCondition": "功能触发条件",
  "executionBody": "功能进入后执行",
  "exitCondition": "功能退出条件",
  "postExitBehavior": "功能退出后执行"
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

        # 提取8个字段
        signal_interfaces = item.get('signalInterfaces', [])
        if isinstance(signal_interfaces, str):
            signal_interfaces = [s.strip() for s in signal_interfaces.split('\n') if s.strip()]

        req = ParsedRequirement(
            id=req_id,
            title=str(item.get('title', '')).strip() or req_id,
            signal_interfaces=signal_interfaces,
            scene_description=str(item.get('sceneDescription', '')).strip(),
            function_description=str(item.get('functionDescription', '')).strip(),
            entry_condition=str(item.get('entryCondition', '')).strip(),
            execution_body=str(item.get('executionBody', '')).strip(),
            exit_condition=str(item.get('exitCondition', '')).strip(),
            post_exit_behavior=str(item.get('postExitBehavior', '')).strip(),
        )
        requirements.append(req)

    return requirements
