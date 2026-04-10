# 汽车空调热管理测试用例生成器 - Phase 4: 导出功能

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 支持将测试用例导出为 Excel (.xlsx) 和 Word (.docx) 格式，支持选择导出范围。

**Architecture:** 后端使用 openpyxl 生成 Excel，使用 python-docx 生成 Word。前端通过 Blob 下载。

**Tech Stack:** openpyxl, python-docx

**Depends on:** Phase 3 完成

---

## File Structure (本阶段新增/修改)

```
AISimTest/
├── backend/
│   ├── core/
│   │   └── exporter.py               # 导出核心模块
│   └── api/
│       └── testcases.py              # 追加导出端点
```

---

### Task 1: Excel 导出后端

**Files:**
- Create: `backend/core/exporter.py`

- [ ] **Step 1: 创建导出模块**

Create `backend/core/exporter.py`:
```python
import os
import tempfile
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH


# 样式定义
HEADER_FONT = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
HEADER_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
HEADER_ALIGNMENT = Alignment(horizontal='center', vertical='center', wrap_text=True)
CELL_ALIGNMENT = Alignment(vertical='top', wrap_text=True)
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin'),
)


def export_to_excel(test_cases: List[dict], output_path: str) -> str:
    """将测试用例导出为 Excel 文件"""
    wb = Workbook()
    ws = wb.active
    ws.title = '测试用例'

    # 表头
    headers = ['用例ID', '用例名称', '关联需求', '类型', '前提条件', '测试步骤', '预期结果', '关联信号']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGNMENT
        cell.border = THIN_BORDER

    # 数据行
    for row_idx, tc in enumerate(test_cases, 2):
        values = [
            tc.get('id', ''),
            tc.get('name', ''),
            tc.get('requirementId', ''),
            '正例' if tc.get('category') == 'positive' else '反例',
            tc.get('precondition', ''),
            '\n'.join(tc.get('steps', [])),
            tc.get('expectedResult', ''),
            ', '.join(s.get('name', '') for s in tc.get('signals', [])),
        ]
        for col, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            cell.alignment = CELL_ALIGNMENT
            cell.border = THIN_BORDER

    # 设置列宽
    column_widths = [15, 30, 15, 8, 30, 50, 30, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # 冻结首行
    ws.freeze_panes = 'A2'

    wb.save(output_path)
    return output_path


def export_to_word(test_cases: List[dict], output_path: str) -> str:
    """将测试用例导出为 Word 文件"""
    doc = Document()

    # 标题
    title = doc.add_heading('测试用例报告', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 概述
    doc.add_paragraph(f'共 {len(test_cases)} 条测试用例')
    positive_count = sum(1 for tc in test_cases if tc.get('category') == 'positive')
    doc.add_paragraph(f'正例: {positive_count} 条, 反例: {len(test_cases) - positive_count} 条')

    # 每条用例一个表格
    for tc in test_cases:
        doc.add_heading(f'{tc.get("id", "")} - {tc.get("name", "")}', level=2)

        table = doc.add_table(rows=5, cols=2, style='Table Grid')
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        cells_data = [
            ('类型', '正例' if tc.get('category') == 'positive' else '反例'),
            ('关联需求', tc.get('requirementId', '')),
            ('前提条件', tc.get('precondition', '')),
            ('测试步骤', '\n'.join(f'{i+1}. {s}' for i, s in enumerate(tc.get('steps', [])))),
            ('预期结果', tc.get('expectedResult', '')),
        ]

        for row_idx, (label, value) in enumerate(cells_data):
            table.cell(row_idx, 0).text = label
            table.cell(row_idx, 1).text = value
            # 加粗标签列
            for paragraph in table.cell(row_idx, 0).paragraphs:
                for run in paragraph.runs:
                    run.bold = True

        doc.add_paragraph()  # 间距

    doc.save(output_path)
    return output_path
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/exporter.py
git commit -m "feat: add Excel and Word export modules"
```

---

### Task 2: 导出 API 端点

**Files:**
- Modify: `backend/api/testcases.py`

- [ ] **Step 1: 在 testcases.py 追加导出端点**

在 `backend/api/testcases.py` 末尾追加:
```python
import tempfile
from fastapi.responses import FileResponse
from core.exporter import export_to_excel, export_to_word


@router.post('/export/excel')
async def export_test_cases_excel(data: dict, db: AsyncSession = Depends(get_db)):
    """导出测试用例为 Excel"""
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
            'id': tc.id,
            'name': tc.name,
            'requirementId': tc.requirement_id,
            'precondition': tc.precondition,
            'steps': tc.steps or [],
            'expectedResult': tc.expected_result,
            'category': tc.category,
            'signals': tc.signal_refs or [],
        }
        for tc in test_cases
    ]

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        export_to_excel(cases_data, tmp.name)
        return FileResponse(
            tmp.name,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename='测试用例.xlsx',
        )


@router.post('/export/word')
async def export_test_cases_word(data: dict, db: AsyncSession = Depends(get_db)):
    """导出测试用例为 Word"""
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
            'id': tc.id,
            'name': tc.name,
            'requirementId': tc.requirement_id,
            'precondition': tc.precondition,
            'steps': tc.steps or [],
            'expectedResult': tc.expected_result,
            'category': tc.category,
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/testcases.py
git commit -m "feat: add Excel and Word export API endpoints"
```

---

### Task 3: 前端导出功能

**Files:**
- Modify: `frontend/src/pages/TestCaseGen.tsx`

- [ ] **Step 1: 在 TestCaseGen 页面添加导出按钮**

在 `TestCaseGen.tsx` 的 Card 区域追加导出按钮:
```tsx
// 在生成按钮同一 Space 中追加:
<Button
  onClick={async () => {
    try {
      const ids = testCases.length > 0 ? testCases.map(tc => tc.id) : undefined;
      const res = await testCaseApi.exportExcel(ids);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '测试用例.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch { message.error('导出失败'); }
  }}
  disabled={testCases.length === 0}
>
  导出 Excel
</Button>
<Button
  onClick={async () => {
    try {
      const ids = testCases.length > 0 ? testCases.map(tc => tc.id) : undefined;
      const res = await testCaseApi.exportWord(ids);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '测试用例.docx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch { message.error('导出失败'); }
  }}
  disabled={testCases.length === 0}
>
  导出 Word
</Button>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/TestCaseGen.tsx
git commit -m "feat: add Excel and Word export buttons to test case page"
```

---

## 验收标准

- [ ] 点击"导出 Excel"按钮可下载 .xlsx 文件
- [ ] 导出的 Excel 包含标准字段（ID、名称、前提条件、步骤、预期结果、关联需求）
- [ ] Excel 表头有样式，列宽合理
- [ ] 点击"导出 Word"按钮可下载 .docx 文件
- [ ] 导出的 Word 格式清晰，每条用例独立展示
- [ ] 无用例时导出按钮禁用
