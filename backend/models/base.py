from sqlalchemy import Column, String, Text, Float, Integer, JSON
from database import Base


class Requirement(Base):
    __tablename__ = 'requirements'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    # 信号接口列表 [{name: str, type: 'Input'|'Output'}]
    # 从文档提取时 type 默认为 'Input'，从 Excel 导入时保留真实类型
    signal_interfaces = Column(JSON, default=list)
    scene_description = Column(Text, default='')    # 场景描述
    function_description = Column(Text, default='') # 功能描述
    entry_condition = Column(Text, default='')       # 功能触发条件
    execution_body = Column(Text, default='')       # 功能进入后执行
    exit_condition = Column(Text, default='')       # 功能退出条件
    post_exit_behavior = Column(Text, default='')  # 功能退出后执行
    test_model = Column(String, default='')        # 测试模型名称（用户填写）
    test_unit_model = Column(String, default='')   # 测试单元模型名称（用户填写）


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
    test_time = Column(String, default='4')
    test_model = Column(String, default='')    # 测试模型名称（用户填写）
    test_unit_model = Column(String, default='') # 测试单元模型名称（用户填写）


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


class PromptTemplate(Base):
    """提示词模板配置"""
    __tablename__ = 'prompt_templates'

    id = Column(String, primary_key=True)  # 如 'test_case_system', 'test_case_user'
    content = Column(Text, default='')    # 模板内容
    description = Column(String, default='')  # 模板描述
    updated_at = Column(String, default='')  # 更新时间


class RequirementInterface(Base):
    """需求接口绑定表 - 记录需求与输入输出信号变量的关联"""
    __tablename__ = 'requirement_interfaces'

    id = Column(String, primary_key=True)
    requirement_id = Column(String, nullable=False)
    interface_name = Column(String, nullable=False)  # Input / Output
    signal_name = Column(String, nullable=False)      # 信号变量名
    description = Column(Text, default='')           # 接口描述
    source_doc = Column(String, default='')           # 来源文档


class SignalLibrary(Base):
    """信号库 - 全局信号定义表，存储信号详细属性"""
    __tablename__ = 'signal_library'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)  # 信号变量名，唯一索引
    description = Column(Text, default='')       # 中文描述
    data_type = Column(String, default='')       # 数据类型
    unit = Column(String, default='')            # 单位
    value_table = Column(Text, default='')       # 值表
    initial_value = Column(String, default='')   # 初始值
    bus = Column(String, default='')              # 总线
    storage_class = Column(String, default='')   # 存储类型
    dimension = Column(String, default='')       # 维度
    factor = Column(Float, default=1.0)          # 因子
    offset = Column(Float, default=0.0)          # 偏移
    min_value = Column(Float, nullable=True)     # 最小值
    max_value = Column(Float, nullable=True)     # 最大值
    source_file = Column(String, default='')     # 来源文件
