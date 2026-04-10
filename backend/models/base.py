from sqlalchemy import Column, String, Text, Float, Integer, JSON
from database import Base


class Requirement(Base):
    __tablename__ = 'requirements'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, default='')
    acceptance_criteria = Column(JSON, default=list)
    parent_id = Column(String, nullable=True)
    source_location = Column(String, default='')
    level = Column(Integer, default=1)


class Signal(Base):
    __tablename__ = 'signals'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    message_id = Column(String, nullable=True)
    start_bit = Column(Integer, default=0)
    length = Column(Integer, default=0)
    factor = Column(Float, default=1.0)
    offset = Column(Float, default=0.0)
    min_value = Column(Float, default=0.0)
    max_value = Column(Float, default=0.0)
    unit = Column(String, default='')
    bus_type = Column(String, default='CAN')
    class_type = Column(String, default='')      # Input / Output / Parameter
    data_type = Column(String, default='')       # 数据类型
    description = Column(Text, default='')       # 描述


class TestCase(Base):
    __tablename__ = 'test_cases'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    requirement_id = Column(String, nullable=False)
    precondition = Column(Text, default='')
    steps = Column(JSON, default=list)
    expected_result = Column(Text, default='')
    category = Column(String, default='positive')
    signal_refs = Column(JSON, default=list)


class LLMConfig(Base):
    __tablename__ = 'llm_config'

    id = Column(String, primary_key=True, default='default')
    provider = Column(String, default='openai')
    api_key = Column(Text, default='')
    base_url = Column(String, default='')
    model = Column(String, default='gpt-4')
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)


class RequirementSignalLink(Base):
    __tablename__ = 'requirement_signal_links'

    id = Column(String, primary_key=True)
    requirement_id = Column(String, nullable=False)
    signal_id = Column(String, nullable=False)
