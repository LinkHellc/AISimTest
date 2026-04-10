# 汽车空调热管理测试用例生成器 - Phase 2: 文档解析

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Word 需求文档导入解析和 Excel 信号矩阵导入，以树形结构展示需求条目，以表格展示信号列表，支持需求-信号手动关联。

**Architecture:** 后端使用 python-docx 解析 Word 文档标题层级和表格内容，使用 openpyxl/pandas 解析 Excel 信号矩阵。解析结果存入 SQLite。前端使用 Ant Design Tree 和 Table 组件展示。

**Tech Stack:** python-docx, openpyxl, pandas, Ant Design Tree/Table, react-router-dom

**Depends on:** Phase 1 完成

---

## File Structure (本阶段新增/修改)

```
AISimTest/
├── frontend/src/
│   ├── components/
│   │   └── Document/
│   │       ├── WordImporter.tsx        # Word 上传组件
│   │       ├── RequirementTree.tsx     # 需求树形展示
│   │       └── RequirementDetail.tsx   # 需求详情编辑
│   ├── components/
│   │   └── Signal/
│   │       ├── SignalImporter.tsx      # Excel 信号上传
│   │       ├── SignalTable.tsx         # 信号列表表格
│   │       └── SignalLinker.tsx        # 需求-信号关联
│   ├── pages/
│   │   ├── RequirementImport.tsx       # 重写为完整功能
│   │   └── SignalMatrix.tsx           # 重写为完整功能
│   └── services/
│       └── api.ts                      # 已有，无需修改
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── doc_parser.py              # Word 解析核心
│   │   └── signal_parser.py           # Excel 信号解析
│   └── api/
│       ├── requirements.py            # 需求 CRUD API
│       ├── signals.py                 # 信号 CRUD API
│       └── links.py                   # 需求-信号关联 API
```

---

### Task 1: Word 文档解析后端

**Files:**
- Create: `backend/core/__init__.py`
- Create: `backend/core/doc_parser.py`
- Create: `backend/api/requirements.py`

- [ ] **Step 1: 创建 Word 解析模块**

Create `backend/core/doc_parser.py`:
```python
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


# 需求 ID 正则模式
REQ_ID_PATTERNS = [
    re.compile(r'(REQ-\d+)', re.IGNORECASE),
    re.compile(r'(SRS-\d+)', re.IGNORECASE),
    re.compile(r'(FR-\d+)', re.IGNORECASE),
    re.compile(r'(\d+\.\d+(?:\.\d+)?)'),  # 1.1, 1.1.1 等
]


def extract_requirement_id(text: str) -> Optional[str]:
    """从文本中提取需求 ID"""
    for pattern in REQ_ID_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def parse_docx(file_path: str) -> List[ParsedRequirement]:
    """解析 Word 文档，提取结构化需求"""
    doc = Document(file_path)
    requirements: List[ParsedRequirement] = []
    heading_stack: List[ParsedRequirement] = []

    for element in doc.element.body:
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

        # 处理标题
        if tag == 'p':
            for para in doc.paragraphs:
                if para._element is element and para.style and para.style.name:
                    style_name = para.style.name
                    if style_name.startswith('Heading'):
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

                        # 确定 parent_id
                        parent_id = None
                        while heading_stack and heading_stack[-1].level >= level:
                            heading_stack.pop()
                        if heading_stack:
                            parent_id = heading_stack[-1].id

                        req = ParsedRequirement(
                            id=req_id,
                            title=text,
                            description='',
                            acceptance_criteria=[],
                            parent_id=parent_id,
                            source_location=f"段落: {para.text[:50]}...",
                            level=level,
                        )
                        requirements.append(req)
                        heading_stack.append(req)
                        break

        # 处理表格
        elif tag == 'tbl':
            for table in doc.tables:
                if table._element is element:
                    _parse_table(table, requirements, heading_stack)
                    break

    return _merge_descriptions(requirements)


def _parse_table(table, requirements: List[ParsedRequirement], heading_stack: List[ParsedRequirement]):
    """解析表格内容为需求条目"""
    rows = table.rows
    if len(rows) < 2:
        return

    # 获取表头
    headers = [cell.text.strip().lower() for cell in rows[0].cells]

    # 识别关键列
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
        req_id = cells[id_col].text.strip() if id_col is not None and id_col < len(cells) else None
        title = cells[title_col].text.strip() if title_col is not None and title_col < len(cells) else ''
        desc = cells[desc_col].text.strip() if desc_col is not None and desc_col < len(cells) else ''
        criteria = cells[criteria_col].text.strip() if criteria_col is not None and criteria_col < len(cells) else ''

        if not req_id:
            req_id = extract_requirement_id(title) or f"REQ-{len(requirements) + 1:03d}"

        if not title:
            title = req_id

        req = ParsedRequirement(
            id=req_id,
            title=title,
            description=desc,
            acceptance_criteria=[c.strip() for c in criteria.split('\n') if c.strip()] if criteria else [],
            parent_id=parent_id,
            source_location=f"表格行",
            level=level,
        )
        requirements.append(req)


def _find_column(headers: List[str], keywords: List[str]) -> Optional[int]:
    """在表头中查找匹配的列索引"""
    for i, header in enumerate(headers):
        for keyword in keywords:
            if keyword in header:
                return i
    return None


def _merge_descriptions(requirements: List[ParsedRequirement]) -> List[ParsedRequirement]:
    """合并相邻段落为父需求的描述"""
    return requirements
```

- [ ] **Step 2: 创建需求 API 路由**

Create `backend/api/requirements.py`:
```python
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import Requirement as RequirementModel
from core.doc_parser import parse_docx, ParsedRequirement

router = APIRouter(prefix='/api/requirements', tags=['requirements'])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/upload')
async def upload_requirements(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """上传并解析 Word 需求文档"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail='仅支持 .docx 格式文件')

    # 保存上传文件
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f'{file_id}.docx')
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # 解析文档
    try:
        parsed = parse_docx(file_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f'文档解析失败: {str(e)}')

    # 清空旧数据并写入新数据
    await db.execute(delete(RequirementModel))
    for req in parsed:
        db_req = RequirementModel(
            id=req.id,
            title=req.title,
            description=req.description,
            acceptance_criteria=req.acceptance_criteria,
            parent_id=req.parent_id,
            source_location=req.source_location,
            level=req.level,
        )
        db.add(db_req)
    await db.commit()

    return {'success': True, 'data': [r.model_dump() for r in parsed]}


@router.get('')
async def get_requirements(db: AsyncSession = Depends(get_db)):
    """获取所有需求条目"""
    result = await db.execute(select(RequirementModel))
    requirements = result.scalars().all()
    return {
        'success': True,
        'data': [
            {
                'id': r.id,
                'title': r.title,
                'description': r.description,
                'acceptanceCriteria': r.acceptance_criteria or [],
                'parentId': r.parent_id,
                'sourceLocation': r.source_location,
                'level': r.level,
            }
            for r in requirements
        ],
    }


@router.put('/{req_id}')
async def update_requirement(req_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """更新需求条目"""
    result = await db.execute(select(RequirementModel).where(RequirementModel.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail='需求不存在')

    for key, value in data.items():
        column_map = {
            'title': 'title',
            'description': 'description',
            'acceptanceCriteria': 'acceptance_criteria',
            'parentId': 'parent_id',
            'sourceLocation': 'source_location',
            'level': 'level',
        }
        if key in column_map:
            setattr(req, column_map[key], value)

    await db.commit()
    return {'success': True}
```

- [ ] **Step 3: 注册路由到 main.py**

在 `backend/main.py` 中添加:
```python
from api.requirements import router as requirements_router
app.include_router(requirements_router)
```

- [ ] **Step 4: 运行测试验证解析逻辑**

Create `backend/tests/test_doc_parser.py`:
```python
import pytest
from core.doc_parser import extract_requirement_id


def test_extract_req_id():
    assert extract_requirement_id('REQ-001 需求标题') == 'REQ-001'
    assert extract_requirement_id('SRS-123 测试') == 'SRS-123'
    assert extract_requirement_id('FR-005 功能') == 'FR-005'
    assert extract_requirement_id('1.1 子需求') == '1.1'
    assert extract_requirement_id('普通文本') is None


def test_extract_req_id_case_insensitive():
    assert extract_requirement_id('req-001 小写') == 'req-001'
```

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/backend"
python -m pytest tests/test_doc_parser.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/core/ backend/api/requirements.py backend/tests/test_doc_parser.py
git commit -m "feat: add Word document parsing with requirement extraction API"
```

---

### Task 2: Excel 信号矩阵解析后端

**Files:**
- Create: `backend/core/signal_parser.py`
- Create: `backend/api/signals.py`

- [ ] **Step 1: 创建 Excel 信号解析模块**

Create `backend/core/signal_parser.py`:
```python
import uuid
from typing import List, Optional
import pandas as pd
from pydantic import BaseModel


class ParsedSignal(BaseModel):
    id: str
    name: str
    message_id: Optional[str] = None
    start_bit: int = 0
    length: int = 0
    factor: float = 1.0
    offset: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    unit: str = ''
    bus_type: str = 'CAN'


# Excel 列名映射（支持多种常见命名）
COLUMN_MAP = {
    'name': ['信号名称', 'signal name', 'name', '信号名', 'signal_name'],
    'message_id': ['消息id', 'message id', 'msg id', '消息id', 'can id', 'message_id', 'frame id'],
    'start_bit': ['起始位', 'start bit', 'start_bit', '起始字节', 'start byte'],
    'length': ['长度', 'length', '位长', 'bit length', 'bit_length', 'signal length'],
    'factor': ['精度', 'factor', '比例因子', 'scale', 'gain'],
    'offset': ['偏移量', 'offset', '偏移', 'bias'],
    'min_value': ['最小值', 'min', 'minimum', '最小', 'min value', 'min_value'],
    'max_value': ['最大值', 'max', 'maximum', '最大', 'max value', 'max_value'],
    'unit': ['单位', 'unit', 'units'],
    'bus_type': ['总线类型', 'bus type', 'bus_type', 'bus'],
}


def _find_column_index(columns: List[str], keywords: List[str]) -> Optional[int]:
    """在列名中查找匹配的索引"""
    for i, col in enumerate(columns):
        col_lower = str(col).strip().lower()
        for keyword in keywords:
            if keyword in col_lower:
                return i
    return None


def parse_signal_excel(file_path: str) -> List[ParsedSignal]:
    """解析 Excel 信号矩阵文件"""
    df = pd.read_excel(file_path)
    columns = list(df.columns)

    # 映射列索引
    col_indices = {}
    for field, keywords in COLUMN_MAP.items():
        idx = _find_column_index(columns, keywords)
        if idx is not None:
            col_indices[field] = idx

    if 'name' not in col_indices:
        raise ValueError('未找到信号名称列，请确保 Excel 包含"信号名称"或"Signal Name"列')

    signals = []
    for _, row in df.iterrows():
        name = str(row.iloc[col_indices['name']]).strip() if pd.notna(row.iloc[col_indices['name']]) else ''
        if not name or name == 'nan':
            continue

        signal = ParsedSignal(
            id=f"SIG-{uuid.uuid4().hex[:8]}",
            name=name,
            message_id=str(row.iloc[col_indices['message_id']]).strip() if 'message_id' in col_indices and pd.notna(row.iloc[col_indices['message_id']]) else None,
            start_bit=int(row.iloc[col_indices['start_bit']]) if 'start_bit' in col_indices and pd.notna(row.iloc[col_indices['start_bit']]) else 0,
            length=int(row.iloc[col_indices['length']]) if 'length' in col_indices and pd.notna(row.iloc[col_indices['length']]) else 0,
            factor=float(row.iloc[col_indices['factor']]) if 'factor' in col_indices and pd.notna(row.iloc[col_indices['factor']]) else 1.0,
            offset=float(row.iloc[col_indices['offset']]) if 'offset' in col_indices and pd.notna(row.iloc[col_indices['offset']]) else 0.0,
            min_value=float(row.iloc[col_indices['min_value']]) if 'min_value' in col_indices and pd.notna(row.iloc[col_indices['min_value']]) else 0.0,
            max_value=float(row.iloc[col_indices['max_value']]) if 'max_value' in col_indices and pd.notna(row.iloc[col_indices['max_value']]) else 0.0,
            unit=str(row.iloc[col_indices['unit']]).strip() if 'unit' in col_indices and pd.notna(row.iloc[col_indices['unit']]) else '',
            bus_type=str(row.iloc[col_indices['bus_type']]).strip().upper() if 'bus_type' in col_indices and pd.notna(row.iloc[col_indices['bus_type']]) else 'CAN',
        )
        signals.append(signal)

    return signals
```

- [ ] **Step 2: 创建信号 API 路由**

Create `backend/api/signals.py`:
```python
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import Signal as SignalModel
from core.signal_parser import parse_signal_excel

router = APIRouter(prefix='/api/signals', tags=['signals'])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/upload')
async def upload_signals(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """上传并解析 Excel 信号矩阵"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail='仅支持 .xlsx/.xls 格式文件')

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f'{file_id}.xlsx')
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    try:
        parsed = parse_signal_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f'信号矩阵解析失败: {str(e)}')

    # 清空旧数据并写入新数据
    await db.execute(delete(SignalModel))
    for sig in parsed:
        db_sig = SignalModel(
            id=sig.id,
            name=sig.name,
            message_id=sig.message_id,
            start_bit=sig.start_bit,
            length=sig.length,
            factor=sig.factor,
            offset=sig.offset,
            min_value=sig.min_value,
            max_value=sig.max_value,
            unit=sig.unit,
            bus_type=sig.bus_type,
        )
        db.add(db_sig)
    await db.commit()

    return {'success': True, 'data': [s.model_dump() for s in parsed]}


@router.get('')
async def get_signals(db: AsyncSession = Depends(get_db)):
    """获取所有信号"""
    result = await db.execute(select(SignalModel))
    signals = result.scalars().all()
    return {
        'success': True,
        'data': [
            {
                'id': s.id,
                'name': s.name,
                'messageId': s.message_id,
                'startBit': s.start_bit,
                'length': s.length,
                'factor': s.factor,
                'offset': s.offset,
                'minValue': s.min_value,
                'maxValue': s.max_value,
                'unit': s.unit,
                'busType': s.bus_type,
            }
            for s in signals
        ],
    }
```

- [ ] **Step 3: 注册路由到 main.py 并测试**

在 `backend/main.py` 添加:
```python
from api.signals import router as signals_router
app.include_router(signals_router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/core/signal_parser.py backend/api/signals.py
git commit -m "feat: add Excel signal matrix parsing with upload API"
```

---

### Task 3: 需求-信号关联 API

**Files:**
- Create: `backend/api/links.py`
- Create: `backend/models/base.py` (追加 Link 模型)

- [ ] **Step 1: 在 models/base.py 追加关联模型**

在 `backend/models/base.py` 末尾追加:
```python
class RequirementSignalLink(Base):
    __tablename__ = 'requirement_signal_links'

    id = Column(String, primary_key=True)
    requirement_id = Column(String, ForeignKey('requirements.id'), nullable=False)
    signal_id = Column(String, ForeignKey('signals.id'), nullable=False)
```

- [ ] **Step 2: 创建关联 API**

Create `backend/api/links.py`:
```python
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models.base import RequirementSignalLink

router = APIRouter(prefix='/api/links', tags=['links'])


@router.post('')
async def create_links(data: dict, db: AsyncSession = Depends(get_db)):
    """创建需求-信号关联"""
    requirement_id = data.get('requirementId')
    signal_ids = data.get('signalIds', [])

    if not requirement_id:
        raise HTTPException(status_code=400, detail='requirementId 必填')

    # 删除旧关联
    await db.execute(
        delete(RequirementSignalLink).where(
            RequirementSignalLink.requirement_id == requirement_id
        )
    )

    # 创建新关联
    for sig_id in signal_ids:
        link = RequirementSignalLink(
            id=str(uuid.uuid4()),
            requirement_id=requirement_id,
            signal_id=sig_id,
        )
        db.add(link)

    await db.commit()
    return {'success': True}


@router.get('/{requirement_id}')
async def get_links(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """获取需求关联的信号"""
    result = await db.execute(
        select(RequirementSignalLink).where(
            RequirementSignalLink.requirement_id == requirement_id
        )
    )
    links = result.scalars().all()
    return {
        'success': True,
        'data': [{'requirementId': l.requirement_id, 'signalId': l.signal_id} for l in links],
    }


@router.delete('/{requirement_id}/{signal_id}')
async def delete_link(requirement_id: str, signal_id: str, db: AsyncSession = Depends(get_db)):
    """解除关联"""
    await db.execute(
        delete(RequirementSignalLink).where(
            RequirementSignalLink.requirement_id == requirement_id,
            RequirementSignalLink.signal_id == signal_id,
        )
    )
    await db.commit()
    return {'success': True}
```

- [ ] **Step 3: 注册路由**

在 `backend/main.py` 添加:
```python
from api.links import router as links_router
app.include_router(links_router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/models/base.py backend/api/links.py
git commit -m "feat: add requirement-signal linking API"
```

---

### Task 4: 前端 - Word 需求导入页

**Files:**
- Create: `frontend/src/components/Document/WordImporter.tsx`
- Create: `frontend/src/components/Document/RequirementTree.tsx`
- Create: `frontend/src/components/Document/RequirementDetail.tsx`
- Modify: `frontend/src/pages/RequirementImport.tsx`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: 在 api.ts 追加关联 API 方法**

在 `frontend/src/services/api.ts` 的 `requirementApi` 后追加:
```typescript
// 需求-信号关联 API
export const linkApi = {
  createLinks: (requirementId: string, signalIds: string[]) =>
    api.post<ApiResponse<void>>('/links', { requirementId, signalIds }),
  getLinks: (requirementId: string) =>
    api.get<ApiResponse<{ requirementId: string; signalId: string }[]>>(`/links/${requirementId}`),
  deleteLink: (requirementId: string, signalId: string) =>
    api.delete<ApiResponse<void>>(`/links/${requirementId}/${signalId}`),
};
```

- [ ] **Step 2: 创建 WordImporter 组件**

Create `frontend/src/components/Document/WordImporter.tsx`:
```tsx
import React, { useState } from 'react';
import { Upload, Button, message, Space, Progress } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import { UploadFile } from 'antd/es/upload/interface';
import { requirementApi } from '../../services/api';
import { useAppStore } from '../../stores/appStore';

const { Dragger } = Upload;

const WordImporter: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const setRequirements = useAppStore((s) => s.setRequirements);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setProgress(30);
    try {
      const response = await requirementApi.uploadWord(file);
      setProgress(80);
      if (response.data.success && response.data.data) {
        setRequirements(response.data.data);
        setProgress(100);
        message.success(`成功解析 ${response.data.data.length} 条需求`);
      } else {
        message.error(response.data.error || '解析失败');
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail || error.message || '上传失败';
      message.error(detail);
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 1000);
    }
    return false; // 阻止默认上传行为
  };

  return (
    <div>
      <Dragger
        accept=".docx"
        showUploadList={false}
        beforeUpload={(file) => {
          handleUpload(file as unknown as File);
          return false;
        }}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽 Word 文档到此处上传</p>
        <p className="ant-upload-hint">支持 .docx 格式</p>
      </Dragger>
      {progress > 0 && (
        <Progress percent={progress} status={progress === 100 ? 'success' : 'active'} />
      )}
    </div>
  );
};

export default WordImporter;
```

- [ ] **Step 3: 创建 RequirementTree 组件**

Create `frontend/src/components/Document/RequirementTree.tsx`:
```tsx
import React, { useMemo } from 'react';
import { Tree, Checkbox, Space, Typography } from 'antd';
import type { TreeDataNode } from 'antd';
import { useAppStore } from '../../stores/appStore';

const { Text } = Typography;

const RequirementTree: React.FC = () => {
  const requirements = useAppStore((s) => s.requirements);
  const selectedRequirementIds = useAppStore((s) => s.selectedRequirementIds);
  const toggleRequirementSelection = useAppStore((s) => s.toggleRequirementSelection);
  const selectAllRequirements = useAppStore((s) => s.selectAllRequirements);
  const clearRequirementSelection = useAppStore((s) => s.clearRequirementSelection);

  const treeData = useMemo(() => {
    const map = new Map<string, TreeDataNode>();
    const roots: TreeDataNode[] = [];

    // 先创建所有节点
    requirements.forEach((req) => {
      map.set(req.id, {
        key: req.id,
        title: (
          <span>
            <Text type="secondary">[{req.id}]</Text> {req.title}
          </span>
        ),
        children: [],
      });
    });

    // 构建树形关系
    requirements.forEach((req) => {
      const node = map.get(req.id)!;
      if (req.parentId && map.has(req.parentId)) {
        map.get(req.parentId)!.children!.push(node);
      } else {
        roots.push(node);
      }
    });

    return roots;
  }, [requirements]);

  if (requirements.length === 0) {
    return null;
  }

  const allSelected = selectedRequirementIds.length === requirements.length;

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Space>
          <Checkbox
            checked={allSelected}
            indeterminate={selectedRequirementIds.length > 0 && !allSelected}
            onChange={(e) => e.target.checked ? selectAllRequirements() : clearRequirementSelection()}
          >
            全选 ({selectedRequirementIds.length}/{requirements.length})
          </Checkbox>
        </Space>
      </div>
      <Tree
        defaultExpandAll
        checkable
        checkedKeys={selectedRequirementIds}
        onCheck={(checked) => {
          // checked 可能是 Key[] 或 { checked: Key[], halfChecked: Key[] }
          const keys = Array.isArray(checked) ? checked : checked.checked;
          const set = useAppStore.getState();
          // 直接设置选中列表
          useAppStore.setState({ selectedRequirementIds: keys as string[] });
        }}
        treeData={treeData}
        style={{ marginTop: 8 }}
      />
    </div>
  );
};

export default RequirementTree;
```

- [ ] **Step 4: 创建 RequirementDetail 组件**

Create `frontend/src/components/Document/RequirementDetail.tsx`:
```tsx
import React from 'react';
import { Descriptions, Tag, Typography } from 'antd';
import { useAppStore } from '../../stores/appStore';

const { Paragraph } = Typography;

interface Props {
  requirementId: string;
}

const RequirementDetail: React.FC<Props> = ({ requirementId }) => {
  const requirements = useAppStore((s) => s.requirements);
  const req = requirements.find((r) => r.id === requirementId);

  if (!req) {
    return <div>未找到需求信息</div>;
  }

  return (
    <Descriptions bordered column={1} size="small">
      <Descriptions.Item label="需求ID">{req.id}</Descriptions.Item>
      <Descriptions.Item label="标题">{req.title}</Descriptions.Item>
      <Descriptions.Item label="描述">
        <Paragraph>{req.description || '无描述'}</Paragraph>
      </Descriptions.Item>
      <Descriptions.Item label="层级">
        <Tag>Level {req.level}</Tag>
      </Descriptions.Item>
      <Descriptions.Item label="来源">{req.sourceLocation}</Descriptions.Item>
      {req.acceptanceCriteria && req.acceptanceCriteria.length > 0 && (
        <Descriptions.Item label="验收标准">
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {req.acceptanceCriteria.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Descriptions.Item>
      )}
    </Descriptions>
  );
};

export default RequirementDetail;
```

- [ ] **Step 5: 重写 RequirementImport 页面**

Replace `frontend/src/pages/RequirementImport.tsx`:
```tsx
import React, { useState } from 'react';
import { Typography, Card, Row, Col, Divider } from 'antd';
import WordImporter from '../components/Document/WordImporter';
import RequirementTree from '../components/Document/RequirementTree';
import RequirementDetail from '../components/Document/RequirementDetail';
import { useAppStore } from '../stores/appStore';

const { Title, Paragraph } = Typography;

const RequirementImport: React.FC = () => {
  const requirements = useAppStore((s) => s.requirements);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div>
      <Title level={4}>需求导入</Title>
      <Paragraph type="secondary">
        上传 Word 格式的需求文档，系统将自动解析并条目化展示需求。
      </Paragraph>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="上传需求文档" size="small">
            <WordImporter />
          </Card>
        </Col>
      </Row>

      {requirements.length > 0 && (
        <>
          <Divider />
          <Row gutter={16}>
            <Col span={12}>
              <Card title={`需求列表 (${requirements.length} 条)`} size="small">
                <RequirementTree />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="需求详情" size="small">
                {selectedId ? (
                  <RequirementDetail requirementId={selectedId} />
                ) : (
                  <Paragraph type="secondary">点击左侧需求查看详情</Paragraph>
                )}
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default RequirementImport;
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/Document/ frontend/src/pages/RequirementImport.tsx frontend/src/services/api.ts
git commit -m "feat: add Word requirement import page with tree view and detail display"
```

---

### Task 5: 前端 - Excel 信号矩阵页

**Files:**
- Create: `frontend/src/components/Signal/SignalImporter.tsx`
- Create: `frontend/src/components/Signal/SignalTable.tsx`
- Create: `frontend/src/components/Signal/SignalLinker.tsx`
- Modify: `frontend/src/pages/SignalMatrix.tsx`

- [ ] **Step 1: 创建 SignalImporter 组件**

Create `frontend/src/components/Signal/SignalImporter.tsx`:
```tsx
import React, { useState } from 'react';
import { Upload, message, Progress } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { signalApi } from '../../services/api';
import { useAppStore } from '../../stores/appStore';

const { Dragger } = Upload;

const SignalImporter: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const setSignals = useAppStore((s) => s.setSignals);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setProgress(30);
    try {
      const response = await signalApi.uploadExcel(file);
      setProgress(80);
      if (response.data.success && response.data.data) {
        setSignals(response.data.data);
        setProgress(100);
        message.success(`成功导入 ${response.data.data.length} 个信号`);
      } else {
        message.error(response.data.error || '导入失败');
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail || error.message || '上传失败';
      message.error(detail);
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 1000);
    }
    return false;
  };

  return (
    <div>
      <Dragger
        accept=".xlsx,.xls"
        showUploadList={false}
        beforeUpload={(file) => {
          handleUpload(file as unknown as File);
          return false;
        }}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽 Excel 信号矩阵到此处</p>
        <p className="ant-upload-hint">支持 .xlsx / .xls 格式</p>
      </Dragger>
      {progress > 0 && (
        <Progress percent={progress} status={progress === 100 ? 'success' : 'active'} />
      )}
    </div>
  );
};

export default SignalImporter;
```

- [ ] **Step 2: 创建 SignalTable 组件**

Create `frontend/src/components/Signal/SignalTable.tsx`:
```tsx
import React, { useState } from 'react';
import { Table, Input, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useAppStore } from '../../stores/appStore';
import type { Signal } from '../../types';

const SignalTable: React.FC = () => {
  const signals = useAppStore((s) => s.signals);
  const [searchText, setSearchText] = useState('');

  const filteredSignals = signals.filter((s) =>
    s.name.toLowerCase().includes(searchText.toLowerCase()) ||
    (s.messageId && s.messageId.toLowerCase().includes(searchText.toLowerCase()))
  );

  const columns: ColumnsType<Signal> = [
    {
      title: '信号名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '消息ID',
      dataIndex: 'messageId',
      key: 'messageId',
      width: 120,
    },
    {
      title: '起始位',
      dataIndex: 'startBit',
      key: 'startBit',
      width: 80,
    },
    {
      title: '长度',
      dataIndex: 'length',
      key: 'length',
      width: 80,
    },
    {
      title: '精度',
      dataIndex: 'factor',
      key: 'factor',
      width: 80,
    },
    {
      title: '偏移',
      dataIndex: 'offset',
      key: 'offset',
      width: 80,
    },
    {
      title: '范围',
      key: 'range',
      width: 150,
      render: (_, record) => `${record.minValue} ~ ${record.maxValue}`,
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
    },
    {
      title: '总线',
      dataIndex: 'busType',
      key: 'busType',
      width: 80,
      render: (val: string) => <Tag color={val === 'CAN' ? 'blue' : 'green'}>{val}</Tag>,
    },
  ];

  return (
    <div>
      <Input.Search
        placeholder="搜索信号名称或消息ID"
        allowClear
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 16, width: 300 }}
      />
      <Table
        columns={columns}
        dataSource={filteredSignals}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 个信号` }}
      />
    </div>
  );
};

export default SignalTable;
```

- [ ] **Step 3: 创建 SignalLinker 组件**

Create `frontend/src/components/Signal/SignalLinker.tsx`:
```tsx
import React, { useState, useEffect } from 'react';
import { Select, Button, Tag, Space, message } from 'antd';
import { useAppStore } from '../../stores/appStore';
import { linkApi } from '../../services/api';

interface Props {
  requirementId: string;
}

const SignalLinker: React.FC<Props> = ({ requirementId }) => {
  const signals = useAppStore((s) => s.signals);
  const [linkedIds, setLinkedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchLinks = async () => {
      try {
        const res = await linkApi.getLinks(requirementId);
        if (res.data.success && res.data.data) {
          setLinkedIds(res.data.data.map((l: any) => l.signalId));
        }
      } catch {}
    };
    fetchLinks();
  }, [requirementId]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await linkApi.createLinks(requirementId, linkedIds);
      message.success('关联保存成功');
    } catch (error: any) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Select
        mode="multiple"
        style={{ width: '100%', minWidth: 300 }}
        placeholder="选择关联信号"
        value={linkedIds}
        onChange={setLinkedIds}
        options={signals.map((s) => ({ label: `${s.name} (${s.unit})`, value: s.id }))}
        optionFilterProp="label"
      />
      <Button
        type="primary"
        size="small"
        loading={loading}
        onClick={handleSave}
        style={{ marginTop: 8 }}
      >
        保存关联
      </Button>
      {linkedIds.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <Space wrap>
            {linkedIds.map((id) => {
              const sig = signals.find((s) => s.id === id);
              return sig ? <Tag key={id} closable onClose={() => setLinkedIds(linkedIds.filter((i) => i !== id))}>{sig.name}</Tag> : null;
            })}
          </Space>
        </div>
      )}
    </div>
  );
};

export default SignalLinker;
```

- [ ] **Step 4: 重写 SignalMatrix 页面**

Replace `frontend/src/pages/SignalMatrix.tsx`:
```tsx
import React from 'react';
import { Typography, Card, Row, Col, Divider } from 'antd';
import SignalImporter from '../components/Signal/SignalImporter';
import SignalTable from '../components/Signal/SignalTable';
import { useAppStore } from '../stores/appStore';

const { Title, Paragraph } = Typography;

const SignalMatrix: React.FC = () => {
  const signals = useAppStore((s) => s.signals);

  return (
    <div>
      <Title level={4}>信号管理</Title>
      <Paragraph type="secondary">
        导入 Excel 格式的 CAN/LIN 信号矩阵，关联信号与需求。
      </Paragraph>

      <Card title="上传信号矩阵" size="small">
        <SignalImporter />
      </Card>

      {signals.length > 0 && (
        <>
          <Divider />
          <Card title={`信号列表 (${signals.length} 个)`} size="small">
            <SignalTable />
          </Card>
        </>
      )}
    </div>
  );
};

export default SignalMatrix;
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Signal/ frontend/src/pages/SignalMatrix.tsx
git commit -m "feat: add Excel signal matrix import page with table display and search"
```

---

## 验收标准

- [ ] 可上传 .docx 文件并看到解析后的需求树形结构
- [ ] 需求树支持勾选、展开/折叠
- [ ] 可上传 .xlsx 信号矩阵文件并看到信号列表表格
- [ ] 信号列表支持搜索筛选
- [ ] 可为需求手动关联信号并保存
- [ ] 后端测试 test_doc_parser.py 通过
