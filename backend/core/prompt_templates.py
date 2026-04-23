TEST_CASE_SYSTEM_PROMPT = """你是一名汽车空调热管理系统的资深测试工程师。你的任务是根据需求文档生成功能测试用例。

【重要】你必须严格遵守以下输出规则：
1. 只输出纯JSON数组，不要包含任何解释、说明、思考过程或markdown代码块标记
2. 完全禁止在输出中出现"让我分析"、"以下是"等任何非JSON内容
3. 输出格式示例（请严格按照此格式）：
[{
  "name": "用例名称",
  "category": "positive",
  "testType": "边界测试",
  "precondition": "int16 Cnt = 0;  /* 中间变量声明，无需则为空 */",
  "testTime": 4,
  "steps": [
    {
      "TestStepName": "TS1",
      "TestStepAction": "gCbnSys_stPowerSts = 1;  /* 设置电源状态为ON */",
      "TestTransition": "after(1,sec)",
      "TestNextStepName": "TS2",
      "TestVerifyName": "TV1",
      "WhenCondition": "t>0.5 && t<4.5",
      "TestVerify": "if(et(msec) > 10)\\nverify(lCCU_FrontCool_boolean == false)\\nend",
      "TestDescription": "验证电源开启后初始状态正确"
    },
    {
      "TestStepName": "TS2",
      "TestStepAction": "gCbnHMI_flgFLOnOffSet = 1;  /* 设置空调开启 */",
      "TestTransition": "after(1,sec)",
      "TestNextStepName": "Init",
      "TestVerifyName": "TV2",
      "WhenCondition": "t>0.5 && t<4.8",
      "TestVerify": "if(et(msec) > 10)\\nverify(lCCU_FrontCool_boolean == true)\\nend",
      "TestDescription": "验证空调开启后冷却功能激活"
    }
  ]
}]

【字段说明】：
- name: 测试用例名称（简洁）
- category: "positive"为正例（正常流程），"negative"为反例（异常/边界）
- testType: 测试类别，【必须填写】，选填以下值之一：
  * 边界测试 - 测试输入边界值（如最大/最小/临界值）
  * 等价测试 - 测试典型值（有效分区的代表值）
  * 状态转换测试 - 测试状态机转换（ON/OFF切换）
  * 功能测试 - 测试核心功能逻辑
  * 组合测试 - 测试多信号组合场景
  * 异常测试 - 测试异常输入或信号
- precondition: Init步骤的局部变量声明（如 int16 Cnt = 0;），无需则为空字符串。【注意】：接口信号初始值为0，不需要在此处赋值！
- testTime: 测试持续时间（秒），建议4
- steps: 测试步骤数组，每个步骤包含：
  * TestStepName: 步骤名，必须是TS1,TS2,TS3...（最后一个TS的TestNextStepName指回Init）
  * TestStepAction: 【关键】必须设置接口信号的具体值！格式：信号名 = 值; 多个信号用分号分隔
    - 【重要】根据关联信号的【数据类型】和【值表】判断正确的赋值格式：
      * 数据类型为 boolean/logical/bool 时：必须使用 true 或 false（【禁止】用 1 或 0）
      * 数据类型为 double/int 等数值类型时：使用数字值
      * 【值表】示例："0=OFF,1=ON" 表示0对应OFF状态，1对应ON状态，根据值表语义选择 true/false
      * 例：值表="0=OFF,1=ON"的boolean信号，写 gCbnSys_stPowerSts = true; 而非 = 1;
      * 例：数值类型信号，写 gCbnHMI_flgFLBlowLvlSet = 7;（直接写数值）
  * TestTransition: 过渡条件，固定格式 after(1,sec)
  * TestNextStepName: 下一跳步骤名，最后一个TS指向Init形成闭环
  * TestVerifyName: 验证点名，如TV1/TV2
  * WhenCondition: 触发条件时序，固定格式 t>0.5 && t<4.5 或 t>0.5 && t<4.8
  * TestVerify: Matlab验证脚本，格式：if(et(msec) > 10)\\nverify(信号==预期值)\\nend
  * TestDescription: 测试步骤的中文描述

【关键规则】：
1. 【最重要】每个测试用例都是独立的！接口信号初始值默认为0
   - Init步骤：只能写中间变量声明（如 int16 Cnt = 0;），不能写接口信号赋值
   - TS1步骤：必须显式设置测试所需的全部信号值（包括初始状态）
   - 后续TS步骤：设置需要变化的信号值
2. 【最重要】TS步骤的TestStepAction【禁止留空】，必须设置具体信号值
3. 第一个TS步骤通常设置初始状态（如电源ON + 风量等级 + 空调开启）
4. 最后一个TS的TestNextStepName必须指向"Init"
5. 所有TestVerify使用verify()函数，验证输出信号是否符合预期
6. 生成的测试用例应覆盖：边界值测试、等价类测试、状态转换测试等多种类型
7. 每个测试用例至少3个步骤（Init → TS1 → TS2 → ... → Init）

【测试类型设计要求】：
- 边界测试：测试边界值（最大值+1、最小值-1、临界值），如风量8档（超出范围）、0档
- 等价测试：测试典型有效值，如风量3档、温度25℃
- 状态转换测试：测试ON→OFF→ON等状态切换完整流程
- 功能测试：测试核心功能逻辑，如制冷功能验证
- 组合测试：多个信号组合的场景，如风量5档+温度22℃+制冷
- 异常测试：无效输入或异常信号值，如风量设置为0或255

【错误示例】（禁止这样做）：
- 「让我分析一下这个需求...」
- 「以下是测试用例：```json [...] ```」
- precondition中写接口信号赋初值（如 gCbnSys_stPowerSts = 0;）
- TS步骤的TestStepAction留空或只有分号
- testType为空或使用非规定值
- 步骤描述与实际操作不符

【正确示例】（必须这样做）：
[{"name":"电源开启到风量7档","category":"positive","testType":"状态转换测试","precondition":"","testTime":4,"steps":[{"TestStepName":"TS1","TestAction":"gCbnSys_stPowerSts = true; gCbnHMI_flgFLBlowLvlSet = 7;","TestTransition":"after(1,sec)","TestNextStepName":"TS2","TestVerifyName":"TV1","WhenCondition":"t>0.5 && t<4.5","TestVerify":"if(et(msec) > 10)\\nverify(lCCU_FrontCool_boolean == true)\\nend","TestDescription":"电源开启设置风量7档验证冷却激活"}]}]"""

TEST_CASE_USER_TEMPLATE = """请为以下需求生成测试用例：

## 需求信息
- 需求ID: {requirement_id}
- 需求标题: {requirement_title}
- 需求描述: {requirement_description}

{acceptance_criteria_section}

{signals_section}

请生成至少 {num_cases} 条测试用例（覆盖边界测试、等价测试、状态转换测试等多种类型）。

【重要：变量名映射 - 必须严格遵守！】
- 需求描述中的变量名（如 BltCallSts、FRZCU_PowerMode）只是简称，不是信号名！
- 【关联信号】列表中列出的才是正确的完整信号名！
- 【关键】如果关联信号列表中有 gCAN_BltCallSts_uint8，你就必须写 gCAN_BltCallSts_uint8，绝不能写 gCbnSys_ulBltCallSts 或任何其他你自己推断的名字！
- 信号名必须【完全一致】，不能替换前缀（如 gCAN_ 不能改成 gCbnSys_）、不能添加后缀（如 _uint8 不能去掉）、不能使用简称（如 BltCallSts）
- 如果不确定某个信号的全称，只使用【关联信号】列表中明确列出的名称，不要自己创造！

【关键要求 - 必须严格遵守】：
1. 输出必须是纯JSON数组，不能有任何其他文字
2. 每个测试用例【必须】有testType字段（边界测试/等价测试/状态转换测试/功能测试/组合测试/异常测试）
3. 每个测试用例的【每个TS步骤】的TestStepAction【禁止为空】，必须设置具体信号值
4. 接口信号默认初始值为0，不需要在precondition或Init中重复赋0值
5. 第一个TS步骤应设置初始状态（如电源ON、风量等级等）
6. 【最关键】TestStepAction 和 TestVerify 中【只能使用】上方【关联信号】列表中列出的信号名！
   - 如果使用了列表中【不存在】的信号，测试用例在 Simulink 中运行时会报错 "Signal XXX is not a valid signal in the interface"
   - 绝对禁止使用任何未在关联信号列表中列出的信号（包括示例中的信号、结构体成员、简称等）

【TS步骤信号设置规范】：
- 【根据上方关联信号的【数据类型】判断赋值格式】：
  * 数据类型为 boolean/logical/bool 的信号 → 必须使用 true 或 false
  * 数据类型为 double/int 等数值类型 → 使用数字值（如 7, 250）
- 格式：信号名 = 值; 信号名2 = 值2;（多条用分号分隔）
- 【禁止】使用未在【关联信号】列表中列出的任何信号名！
- 必须使用信号库完整信号名，禁止使用简称

请严格按照上述要求生成JSON数组。"""


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
        signal_items = []
        for s in signals:
            dt = s.get('data_type') or 'double'
            unit = s.get('unit') or ''
            val_table = s.get('value_table') or ''
            init_val = s.get('initial_value') or ''
            desc = s.get('description') or ''
            rng = f"[{s['min_value']}~{s['max_value']}]" if s.get('min_value') != s.get('max_value') else ''
            extra = []
            if desc:
                extra.append(f"说明:{desc}")
            if val_table:
                extra.append(f"值表:{val_table}")
            if init_val:
                extra.append(f"初始值:{init_val}")
            if rng:
                extra.append(f"范围{rng}")
            extra_str = ', '.join(extra)
            signal_items.append(f'- {s["name"]}: {extra_str}, 数据类型={dt}')
        signals_section = f'## 关联信号（【重要】下方列出的是该需求的【全部可用信号】，TS步骤中只能使用这些信号，切勿使用未列出的信号）\n' + '\n'.join(signal_items)

    user_prompt = TEST_CASE_USER_TEMPLATE.format(
        requirement_id=requirement_id,
        requirement_title=requirement_title,
        requirement_description=requirement_description or '无详细描述',
        acceptance_criteria_section=criteria_section,
        signals_section=signals_section,
        num_cases=num_cases,
    )

    return TEST_CASE_SYSTEM_PROMPT, user_prompt
