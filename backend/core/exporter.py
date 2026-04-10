from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH

HEADER_FONT = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
HEADER_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
HEADER_ALIGNMENT = Alignment(horizontal='center', vertical='center', wrap_text=True)
CELL_ALIGNMENT = Alignment(vertical='top', wrap_text=True)
THIN_BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin'),
)


def export_to_excel(test_cases: List[dict], output_path: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = '测试用例'

    headers = ['用例ID', '用例名称', '关联需求', '类型', '前提条件', '测试步骤', '预期结果', '关联信号']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGNMENT
        cell.border = THIN_BORDER

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

    column_widths = [15, 30, 15, 8, 30, 50, 30, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.freeze_panes = 'A2'

    wb.save(output_path)
    return output_path


def export_to_word(test_cases: List[dict], output_path: str) -> str:
    doc = Document()
    title = doc.add_heading('测试用例报告', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f'共 {len(test_cases)} 条测试用例')
    positive_count = sum(1 for tc in test_cases if tc.get('category') == 'positive')
    doc.add_paragraph(f'正例: {positive_count} 条, 反例: {len(test_cases) - positive_count} 条')

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
            for paragraph in table.cell(row_idx, 0).paragraphs:
                for run in paragraph.runs:
                    run.bold = True
        doc.add_paragraph()

    doc.save(output_path)
    return output_path
