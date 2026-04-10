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


COLUMN_MAP = {
    'name': ['信号名称', 'signal name', 'name', '信号名', 'signal_name'],
    'message_id': ['消息id', 'message id', 'msg id', 'can id', 'message_id', 'frame id'],
    'start_bit': ['起始位', 'start bit', 'start_bit', '起始字节'],
    'length': ['长度', 'length', '位长', 'bit length', 'signal length'],
    'factor': ['精度', 'factor', '比例因子', 'scale'],
    'offset': ['偏移量', 'offset', '偏移'],
    'min_value': ['最小值', 'min', 'minimum', 'min value', 'min_value'],
    'max_value': ['最大值', 'max', 'maximum', 'max value', 'max_value'],
    'unit': ['单位', 'unit', 'units'],
    'bus_type': ['总线类型', 'bus type', 'bus_type', 'bus'],
}


def _find_column_index(columns: List[str], keywords: List[str]) -> Optional[int]:
    for i, col in enumerate(columns):
        col_lower = str(col).strip().lower()
        for keyword in keywords:
            if keyword in col_lower:
                return i
    return None


def parse_signal_excel(file_path: str) -> List[ParsedSignal]:
    df = pd.read_excel(file_path)
    columns = list(df.columns)

    col_indices = {}
    for field, keywords in COLUMN_MAP.items():
        idx = _find_column_index(columns, keywords)
        if idx is not None:
            col_indices[field] = idx

    if 'name' not in col_indices:
        raise ValueError('未找到信号名称列，请确保 Excel 包含"信号名称"或"Signal Name"列')

    signals = []
    for _, row in df.iterrows():
        name_val = row.iloc[col_indices['name']]
        name = str(name_val).strip() if pd.notna(name_val) else ''
        if not name or name == 'nan':
            continue

        def safe_int(idx, default=0):
            if idx in col_indices:
                val = row.iloc[idx]
                return int(val) if pd.notna(val) else default
            return default

        def safe_float(idx, default=0.0):
            if idx in col_indices:
                val = row.iloc[idx]
                return float(val) if pd.notna(val) else default
            return default

        def safe_str(idx, default=''):
            if idx in col_indices:
                val = row.iloc[idx]
                return str(val).strip() if pd.notna(val) else default
            return default

        signal = ParsedSignal(
            id=f"SIG-{uuid.uuid4().hex[:8]}",
            name=name,
            message_id=safe_str('message_id') or None,
            start_bit=safe_int('start_bit'),
            length=safe_int('length'),
            factor=safe_float('factor', 1.0),
            offset=safe_float('offset'),
            min_value=safe_float('min_value'),
            max_value=safe_float('max_value'),
            unit=safe_str('unit'),
            bus_type=safe_str('bus_type', 'CAN').upper(),
        )
        signals.append(signal)

    return signals
