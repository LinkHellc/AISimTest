import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.doc_parser import extract_requirement_id


def test_extract_req_id():
    assert extract_requirement_id('REQ-001 需求标题') == 'REQ-001'
    assert extract_requirement_id('SRS-123 测试') == 'SRS-123'
    assert extract_requirement_id('FR-005 功能') == 'FR-005'
    assert extract_requirement_id('1.1 子需求') == '1.1'
    assert extract_requirement_id('普通文本') is None


def test_extract_req_id_case_insensitive():
    assert extract_requirement_id('req-001 小写') == 'req-001'
