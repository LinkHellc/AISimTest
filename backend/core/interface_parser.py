"""
接口表解析器 - 解析需求接口 Excel 和信号库 Excel
"""
import os
import uuid
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd


class ParsedRequirementInterface(BaseModel):
    """解析的需求接口"""
    requirement_id: str
    interface_name: str  # Input / Output
    signal_name: str
    description: str = ''
    source_doc: str = ''


class ParsedSignalLibrary(BaseModel):
    """解析的信号库条目"""
    name: str
    description: str = ''
    data_type: str = ''
    unit: str = ''
    value_table: str = ''
    initial_value: str = ''
    bus: str = ''
    storage_class: str = ''
    dimension: str = ''
    factor: float = 1.0
    offset: float = 0.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    source_file: str = ''


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数"""
    if val is None or (isinstance(val, str) and val.strip() in ('', '/', '-')):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_str(val) -> str:
    """安全转换为字符串，处理 pandas NaN"""
    if val is None:
        return ''
    if isinstance(val, float) and str(val) == 'nan':
        return ''
    s = str(val).strip()
    return s if s.lower() != 'nan' else ''


def _parse_value_table(val) -> str:
    """解析值表，处理换行"""
    if val is None:
        return ''
    return str(val).replace('\n', ' ').strip()


# ---------- 需求接口解析 ----------

def parse_requirement_interface_excel(file_path: str) -> List[ParsedRequirementInterface]:
    """
    解析需求接口 Excel 文件（如 模型接口信息.xlsx）
    返回接口列表（不绑定具体需求ID，由调用方关联）
    """
    df = pd.read_excel(file_path, sheet_name=None)
    interfaces = []

    for sheet_name, sheet_df in df.items():
        # 跳过空 sheet
        if sheet_df.empty:
            continue

        # 查找有效的列
        columns = [c for c in sheet_df.columns if not c.startswith('Unnamed')]

        for idx, row in sheet_df.iterrows():
            # 获取 Class (Input/Output) 和 Name (信号名)
            class_val = None
            name_val = None

            for col in columns:
                col_lower = str(col).lower()
                val = _safe_str(row.get(col, ''))

                if col_lower == 'class':
                    class_val = val
                elif col_lower == 'name' and val:
                    name_val = val

            # 如果有 Class 和 Name，提取接口
            if class_val and name_val:
                # Class 列可能包含多个值（逗号分隔）或单个值
                if ',' in class_val:
                    classes = [c.strip() for c in class_val.split(',')]
                else:
                    classes = [class_val]

                for cls in classes:
                    if cls.lower() in ('input', 'output', 'provided', 'required'):
                        interface_name = 'Input' if cls.lower() in ('input', 'required') else 'Output'

                        interfaces.append(ParsedRequirementInterface(
                            requirement_id='',  # 由调用方填充
                            interface_name=interface_name,
                            signal_name=name_val,
                            description=_safe_str(row.get('Description', '')),
                            source_doc=os.path.basename(file_path)
                        ))

    return interfaces


# ---------- 信号库解析 ----------

def parse_signal_library_excel(file_path: str) -> List[ParsedSignalLibrary]:
    """
    解析接口表 Excel 文件的 Input/Mea/Output sheets
    返回信号库条目列表
    """
    try:
        df_dict = pd.read_excel(file_path, sheet_name=['Input', 'Mea', 'Output'])
    except ValueError:
        # 部分 sheet 不存在时使用全部 sheet
        df_dict = pd.read_excel(file_path, sheet_name=None)

    signals = []
    source_file = os.path.basename(file_path)

    # 统一列名映射
    column_map = {
        'Name': 'name',
        'Description': 'description',
        'Data Type': 'data_type',
        'Initial Value': 'initial_value',
        'Unit': 'unit',
        'Value Table': 'value_table',
        'Bus': 'bus',
        'Storage Class': 'storage_class',
        'Dimension': 'dimension',
        'Factor': 'factor',
        'Offset': 'offset',
        'Min': 'min_value',
        'Max': 'max_value',
    }

    for sheet_name, sheet_df in df_dict.items():
        if sheet_df.empty:
            continue

        for idx, row in sheet_df.iterrows():
            name = _safe_str(row.get('Name', ''))
            if not name:
                continue

            # 跳过标题行
            if name.lower() in ('name', 'signal', 'signal name'):
                continue

            signals.append(ParsedSignalLibrary(
                name=name,
                description=_safe_str(row.get('Description', '')),
                data_type=_safe_str(row.get('Data Type', '')),
                initial_value=_safe_str(row.get('Initial Value', '')),
                unit=_safe_str(row.get('Unit', '')),
                value_table=_parse_value_table(row.get('Value Table', '')),
                bus=_safe_str(row.get('Bus', '')),
                storage_class=_safe_str(row.get('Storage Class', '')),
                dimension=_safe_str(row.get('Dimension', '1')),
                factor=_safe_float(row.get('Factor', 1.0)) or 1.0,
                offset=_safe_float(row.get('Offset', 0.0)) or 0.0,
                min_value=_safe_float(row.get('Min', None)),
                max_value=_safe_float(row.get('Max', None)),
                source_file=source_file
            ))

    return signals


def parse_signal_library_directory(dir_path: str) -> List[ParsedSignalLibrary]:
    """
    解析接口表目录下的所有 Excel 文件
    """
    all_signals = []
    excel_files = [f for f in os.listdir(dir_path)
                  if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]

    for filename in excel_files:
        file_path = os.path.join(dir_path, filename)
        try:
            signals = parse_signal_library_excel(file_path)
            all_signals.extend(signals)
        except Exception as e:
            print(f"Warning: Failed to parse {filename}: {e}")

    return all_signals
