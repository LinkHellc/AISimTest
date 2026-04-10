TEST_CASE_SYSTEM_PROMPT = """你是一名汽车空调热管理系统的资深测试工程师。你的任务是根据需求文档生成功能测试用例。

输出要求：
1. 每条测试用例必须包含：用例名称、前提条件、测试步骤、预期结果
2. 测试步骤要详细、可执行
3. 预期结果要明确、可验证
4. 生成正例（正常流程）和反例（异常流程）测试用例
5. 如果提供了信号信息，在测试步骤中体现信号的具体值和范围约束

输出格式为 JSON 数组，每个元素结构如下：
{
  "name": "测试用例名称",
  "precondition": "前提条件",
  "steps": ["步骤1", "步骤2", ...],
  "expectedResult": "预期结果",
  "category": "positive 或 negative"
}
"""

TEST_CASE_USER_TEMPLATE = """请为以下需求生成测试用例：

## 需求信息
- 需求ID: {requirement_id}
- 需求标题: {requirement_title}
- 需求描述: {requirement_description}

{acceptance_criteria_section}

{signals_section}

请生成至少 {num_cases} 条测试用例（包含正例和反例）。只输出 JSON 数组，不要输出其他内容。"""


def build_test_case_prompt(
    requirement_id: str,
    requirement_title: str,
    requirement_description: str,
    acceptance_criteria: list | None = None,
    signals: list[dict] | None = None,
    num_cases: int = 5,
) -> tuple[str, str]:
    criteria_section = ''
    if acceptance_criteria:
        criteria_items = '\n'.join(f'- {c}' for c in acceptance_criteria)
        criteria_section = f'## 验收标准\n{criteria_items}'

    signals_section = ''
    if signals:
        signal_items = '\n'.join(
            f'- {s["name"]}: 范围[{s["min_value"]}~{s["max_value"]}], 精度={s["factor"]}, 偏移={s["offset"]}, 单位={s["unit"]}'
            for s in signals
        )
        signals_section = f'## 关联信号\n{signal_items}'

    user_prompt = TEST_CASE_USER_TEMPLATE.format(
        requirement_id=requirement_id,
        requirement_title=requirement_title,
        requirement_description=requirement_description or '无详细描述',
        acceptance_criteria_section=criteria_section,
        signals_section=signals_section,
        num_cases=num_cases,
    )

    return TEST_CASE_SYSTEM_PROMPT, user_prompt
