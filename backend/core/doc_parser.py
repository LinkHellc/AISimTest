import re
from typing import List, Optional
from docx import Document
from pydantic import BaseModel


class ParsedRequirement(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    parent_id: Optional[str] = None
    source_location: str
    level: int


REQ_ID_PATTERNS = [
    re.compile(r'(REQ-\d+)', re.IGNORECASE),
    re.compile(r'(SRS-\d+)', re.IGNORECASE),
    re.compile(r'(FR-\d+)', re.IGNORECASE),
    re.compile(r'(\d+\.\d+(?:\.\d+)?)'),
]


def extract_requirement_id(text: str) -> Optional[str]:
    for pattern in REQ_ID_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def parse_docx(file_path: str) -> List[ParsedRequirement]:
    doc = Document(file_path)
    requirements: List[ParsedRequirement] = []
    heading_stack: List[ParsedRequirement] = []
    seen_ids = set()

    # Process paragraphs for headings
    for para in doc.paragraphs:
        style_name = para.style.name if para.style else ''
        if not style_name.startswith('Heading'):
            continue

        try:
            level = int(style_name.replace('Heading ', '').replace('Heading', '1').strip())
        except ValueError:
            level = 1
        level = min(max(level, 1), 6)

        text = para.text.strip()
        if not text:
            continue

        req_id = extract_requirement_id(text)
        if not req_id:
            req_id = f"REQ-{len(requirements) + 1:03d}"

        # Deduplicate IDs
        original_id = req_id
        counter = 1
        while req_id in seen_ids:
            req_id = f"{original_id}-{counter}"
            counter += 1
        seen_ids.add(req_id)

        # Determine parent
        while heading_stack and heading_stack[-1].level >= level:
            heading_stack.pop()
        parent_id = heading_stack[-1].id if heading_stack else None

        req = ParsedRequirement(
            id=req_id,
            title=text,
            description='',
            acceptance_criteria=[],
            parent_id=parent_id,
            source_location=f"段落: {text[:80]}",
            level=level,
        )
        requirements.append(req)
        heading_stack.append(req)

    # Process tables
    for table in doc.tables:
        _parse_table(table, requirements, heading_stack, seen_ids)

    return requirements


def _parse_table(table, requirements: List[ParsedRequirement], heading_stack: List[ParsedRequirement], seen_ids: set):
    rows = table.rows
    if len(rows) < 2:
        return

    headers = [cell.text.strip().lower() for cell in rows[0].cells]
    id_col = _find_column(headers, ['id', '编号', '需求id', '需求编号'])
    title_col = _find_column(headers, ['title', '标题', '名称', '需求名称', '需求标题'])
    desc_col = _find_column(headers, ['description', '描述', '内容', '需求描述', '需求内容'])
    criteria_col = _find_column(headers, ['criteria', '验收标准', '验收条件', '接受标准'])

    if title_col is None and desc_col is None:
        return

    parent_id = heading_stack[-1].id if heading_stack else None
    level = heading_stack[-1].level + 1 if heading_stack else 2

    for row in rows[1:]:
        cells = row.cells
        cell_texts = [cell.text.strip() for cell in cells]

        req_id = cell_texts[id_col] if id_col is not None and id_col < len(cell_texts) else None
        title = cell_texts[title_col] if title_col is not None and title_col < len(cell_texts) else ''
        desc = cell_texts[desc_col] if desc_col is not None and desc_col < len(cell_texts) else ''
        criteria = cell_texts[criteria_col] if criteria_col is not None and criteria_col < len(cell_texts) else ''

        if not req_id:
            req_id = extract_requirement_id(title) or f"REQ-{len(requirements) + 1:03d}"
        if not title:
            title = req_id

        # Deduplicate
        original_id = req_id
        counter = 1
        while req_id in seen_ids:
            req_id = f"{original_id}-{counter}"
            counter += 1
        seen_ids.add(req_id)

        req = ParsedRequirement(
            id=req_id,
            title=title,
            description=desc,
            acceptance_criteria=[c.strip() for c in criteria.split('\n') if c.strip()] if criteria else [],
            parent_id=parent_id,
            source_location='表格行',
            level=level,
        )
        requirements.append(req)


def _find_column(headers: List[str], keywords: List[str]) -> Optional[int]:
    for i, header in enumerate(headers):
        for keyword in keywords:
            if keyword in header:
                return i
    return None
