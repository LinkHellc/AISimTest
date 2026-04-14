# AISimTest - 需求管理与测试用例生成平台

AI 驱动的功能需求管理和测试用例生成系统，支持从 Word 文档导入需求、通过 LLM 智能生成测试用例，并导出符合 Matlab TestHarness 格式的 Excel 文件。

## 功能特性

### 需求管理
- **Word 文档导入**：上传 `.docx` 格式需求文档，通过 LLM 自动解析提取功能需求
- **需求编辑**：支持新增、编辑、删除需求条目
- **信号接口导入**：为每个需求导入 Excel 格式的接口信号表

### 测试用例生成
- **智能生成**：基于需求描述和信号接口，调用 LLM 自动生成功能测试用例
- **用例管理**：查看、编辑、删除已生成的测试用例
- **多格式导出**：支持 Excel（Matlab TestHarness 格式）和 Word 格式导出

### Matlab TestHarness 格式
导出的 Excel 文件符合 Matlab TestSequence 规范：
- 每条需求对应独立的 Worksheet（sheet 名称为需求标题）
- 15 列完整格式：`TestModel`, `TestUnitModel`, `TestHarnessName`, `FreshFlag`, `TestTime`, `TestStepName`, `TestStepAction`, `TestTransition`, `TestNextStepName`, `TestVerifyName`, `WhenCondition`, `TestVerify`, `TestDescription`, `优先级`, `测试项目`
- 每个测试用例结构：`Init` 行 → `TSn` 行 → `TVn` 行 → … → 最后 `TSn`（指向 `Init`）
- `FreshFlag` = 1（创建/更新标志）
- `TestModel` 列预留，供用户填写模型名称

### LLM 配置
- 支持多种 LLM 提供者（OpenAI、Azure OpenAI、SiliconFlow、MiniMax、GLM 等）
- 可配置 API Key、Base URL、模型名称、温度参数等
- 支持连接测试

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | React + TypeScript + Vite + Ant Design + Zustand |
| 后端 | Python FastAPI + SQLAlchemy (async) + SQLite |
| LLM | OpenAI GPT / Azure OpenAI / SiliconFlow / MiniMax / GLM |

## 项目结构

```
AISimTest/
├── backend/                     # FastAPI 后端
│   ├── api/                     # API 路由
│   │   ├── requirements.py      # 需求管理接口
│   │   ├── testcases.py         # 测试用例接口
│   │   ├── config.py            # LLM 配置接口
│   │   └── signal_library.py    # 信号库接口
│   ├── core/                    # 核心模块
│   │   ├── doc_parser.py        # Word 文档解析（LLM）
│   │   ├── llm_adapter.py       # LLM 适配器
│   │   ├── exporter.py          # Excel/Word 导出
│   │   ├── prompt_templates.py  # LLM prompt 模板
│   │   └── interface_parser.py  # 接口信号 Excel 解析
│   ├── models/                  # 数据库模型
│   │   └── base.py              # SQLAlchemy 模型定义
│   └── main.py                  # FastAPI 入口
├── frontend/                    # React 前端
│   └── src/
│       ├── pages/               # 页面组件
│       ├── components/           # 公共组件
│       ├── services/            # API 调用
│       ├── stores/              # Zustand 状态管理
│       └── types/               # TypeScript 类型定义
└── data/                        # 数据存储目录
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- pnpm（推荐）或 npm

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd frontend
pnpm install
pnpm dev
```

访问 `http://localhost:4210` 打开应用。

### LLM 配置
首次使用需在「设置」页面配置大模型 API：
1. 选择提供者（OpenAI / Azure / SiliconFlow / MiniMax / GLM）
2. 填写 API Key 和 Base URL（如需要）
3. 选择模型名称
4. 点击「测试连接」验证配置

## 使用流程

### 1. 导入需求
入口：「需求导入」页面 → 上传 Word 文档（.docx）→ 系统自动解析生成需求条目

### 2. 管理需求
入口：「需求管理」页面 → 查看、编辑需求 → 为需求导入接口信号 Excel

### 3. 生成测试用例
入口：「用例生成」页面 → 选择需求条目 → 点击「生成测试用例」→ LLM 智能生成

### 4. 导出测试用例
在「用例生成」页面点击「导出 Excel」或「导出 Word」

## 接口说明

### 需求接口
- `POST /api/requirements/upload` - 上传 Word 文档导入需求
- `GET /api/requirements` - 获取所有需求
- `PUT /api/requirements/{id}` - 更新需求
- `DELETE /api/requirements/{id}` - 删除需求
- `POST /api/requirements/{id}/interfaces` - 上传接口信号 Excel

### 测试用例接口
- `POST /api/testcases/generate` - 生成测试用例
- `GET /api/testcases` - 获取所有测试用例
- `PUT /api/testcases/{id}` - 更新测试用例
- `DELETE /api/testcases/{id}` - 删除测试用例
- `POST /api/testcases/export/excel` - 导出 Excel
- `POST /api/testcases/export/word` - 导出 Word

### 配置接口
- `GET /api/config/llm` - 获取 LLM 配置
- `PUT /api/config/llm` - 更新 LLM 配置
- `POST /api/config/llm/test` - 测试 LLM 连接

## License

MIT
