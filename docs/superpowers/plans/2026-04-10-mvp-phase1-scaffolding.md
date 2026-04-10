# 汽车空调热管理测试用例生成器 - Phase 1: 项目脚手架

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 React + FastAPI 全栈项目骨架，包含前后端基础通信、主界面布局、导航系统，产出一个可运行的空壳应用。

**Architecture:** 前端使用 React + Vite + TypeScript + Ant Design，后端使用 Python FastAPI + SQLAlchemy + SQLite。前后端通过 HTTP API 通信。开发时前端 Vite dev server 和后端 uvicorn 分别运行，通过 Vite proxy 解决跨域。生产部署时 FastAPI 同时托管前端构建产物和 API。

**Tech Stack:** React 18, Vite, TypeScript, Ant Design 5, Zustand, Axios, FastAPI, SQLAlchemy, SQLite, python-docx, openpyxl

---

## File Structure (本阶段产出)

```
AISimTest/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── App.css
│       ├── vite-env.d.ts
│       ├── types/
│       │   └── index.ts              # 共享类型定义
│       ├── stores/
│       │   └── appStore.ts           # 全局状态
│       ├── services/
│       │   └── api.ts                # API 调用封装
│       ├── components/
│       │   └── Layout/
│       │       ├── AppLayout.tsx     # 主布局（侧边栏+顶栏）
│       │       └── AppLayout.css
│       └── pages/
│           ├── RequirementImport.tsx  # 需求导入页（空壳）
│           ├── SignalMatrix.tsx       # 信号矩阵页（空壳）
│           ├── TestCaseGen.tsx        # 用例生成页（空壳）
│           └── Settings.tsx           # 设置页（空壳）
├── backend/
│   ├── requirements.txt
│   ├── main.py                       # FastAPI 入口 + CORS
│   ├── database.py                   # SQLAlchemy 数据库配置
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py                   # SQLAlchemy 基础模型
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py                 # 健康检查 API
│   └── tests/
│       ├── __init__.py
│       └── test_health.py            # 健康检查测试
└── data/                             # 本地数据目录（运行时创建）
```

---

### Task 1: 初始化前端项目

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/App.css`
- Create: `frontend/src/vite-env.d.ts`

- [ ] **Step 1: 使用 Vite 创建 React + TypeScript 项目**

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest"
npm create vite@latest frontend -- --template react-ts
```

- [ ] **Step 2: 安装前端依赖**

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/frontend"
npm install antd @ant-design/icons zustand axios react-router-dom
```

- [ ] **Step 3: 配置 Vite proxy（开发时代理后端 API）**

Modify `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: 验证前端项目可以启动**

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/frontend"
npm run dev
```
Expected: Vite dev server 在 http://localhost:5173 启动，浏览器可看到默认 React 页面

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: initialize React + Vite + TypeScript frontend"
```

---

### Task 2: 定义共享类型

**Files:**
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建类型定义文件**

Create `frontend/src/types/index.ts`:
```typescript
// 需求条目
export interface Requirement {
  id: string;
  title: string;
  description: string;
  acceptanceCriteria: string[];
  parentId: string | null;
  sourceLocation: string;
  level: number; // 标题层级 1-6
  children?: Requirement[];
  selected?: boolean;
}

// 信号定义
export interface Signal {
  id: string;
  name: string;
  messageId: string | null;
  startBit: number;
  length: number;
  factor: number;
  offset: number;
  minValue: number;
  maxValue: number;
  unit: string;
  busType: 'CAN' | 'LIN';
}

// 需求-信号关联
export interface RequirementSignalLink {
  requirementId: string;
  signalIds: string[];
}

// 测试用例
export interface TestCase {
  id: string;
  name: string;
  requirementId: string;
  precondition: string;
  steps: string[];
  expectedResult: string;
  category: 'positive' | 'negative';
  signals: Signal[];
}

// LLM 配置
export interface LLMConfig {
  provider: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

// 生成参数
export interface GenerationParams {
  requirements: Requirement[];
  signals: Signal[];
  includeNegative: boolean;
}

// API 响应
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// 文件上传状态
export type UploadStatus = 'idle' | 'uploading' | 'parsing' | 'success' | 'error';

// 生成进度
export interface GenerationProgress {
  current: number;
  total: number;
  status: 'idle' | 'generating' | 'completed' | 'error';
  currentRequirement: string;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/types/
git commit -m "feat: add shared TypeScript type definitions"
```

---

### Task 3: 创建 API 服务层

**Files:**
- Create: `frontend/src/services/api.ts`

- [ ] **Step 1: 创建 API 封装**

Create `frontend/src/services/api.ts`:
```typescript
import axios from 'axios';
import type { ApiResponse, Requirement, Signal, TestCase, LLMConfig } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

// 需求相关 API
export const requirementApi = {
  uploadWord: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<Requirement[]>>('/requirements/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getRequirements: () =>
    api.get<ApiResponse<Requirement[]>>('/requirements'),
  updateRequirement: (id: string, data: Partial<Requirement>) =>
    api.put<ApiResponse<Requirement>>(`/requirements/${id}`, data),
};

// 信号相关 API
export const signalApi = {
  uploadExcel: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<Signal[]>>('/signals/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getSignals: () =>
    api.get<ApiResponse<Signal[]>>('/signals'),
};

// 测试用例相关 API
export const testCaseApi = {
  generate: (requirementIds: string[]) =>
    api.post<ApiResponse<TestCase[]>>('/testcases/generate', { requirementIds }),
  getTestCases: () =>
    api.get<ApiResponse<TestCase[]>>('/testcases'),
  updateTestCase: (id: string, data: Partial<TestCase>) =>
    api.put<ApiResponse<TestCase>>(`/testcases/${id}`, data),
  deleteTestCase: (id: string) =>
    api.delete<ApiResponse<void>>(`/testcases/${id}`),
  exportExcel: (testCaseIds?: string[]) =>
    api.post('/testcases/export/excel', { ids: testCaseIds }, { responseType: 'blob' }),
  exportWord: (testCaseIds?: string[]) =>
    api.post('/testcases/export/word', { ids: testCaseIds }, { responseType: 'blob' }),
};

// LLM 配置相关 API
export const configApi = {
  getLLMConfig: () =>
    api.get<ApiResponse<LLMConfig>>('/config/llm'),
  updateLLMConfig: (config: LLMConfig) =>
    api.put<ApiResponse<void>>('/config/llm', config),
  testConnection: (config: LLMConfig) =>
    api.post<ApiResponse<{ success: boolean; message: string }>>('/config/llm/test', config),
};

// 健康检查
export const healthApi = {
  check: () => api.get('/health'),
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/
git commit -m "feat: add API service layer with axios"
```

---

### Task 4: 创建 Zustand 全局状态

**Files:**
- Create: `frontend/src/stores/appStore.ts`

- [ ] **Step 1: 创建应用状态 store**

Create `frontend/src/stores/appStore.ts`:
```typescript
import { create } from 'zustand';
import type { Requirement, Signal, TestCase, GenerationProgress } from '../types';

interface AppState {
  // 需求相关
  requirements: Requirement[];
  selectedRequirementIds: string[];
  setRequirements: (requirements: Requirement[]) => void;
  toggleRequirementSelection: (id: string) => void;
  selectAllRequirements: () => void;
  clearRequirementSelection: () => void;

  // 信号相关
  signals: Signal[];
  setSignals: (signals: Signal[]) => void;

  // 测试用例相关
  testCases: TestCase[];
  setTestCases: (testCases: TestCase[]) => void;
  updateTestCase: (id: string, data: Partial<TestCase>) => void;
  removeTestCase: (id: string) => void;

  // 生成进度
  generationProgress: GenerationProgress;
  setGenerationProgress: (progress: Partial<GenerationProgress>) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // 需求相关
  requirements: [],
  selectedRequirementIds: [],
  setRequirements: (requirements) => set({ requirements }),
  toggleRequirementSelection: (id) =>
    set((state) => ({
      selectedRequirementIds: state.selectedRequirementIds.includes(id)
        ? state.selectedRequirementIds.filter((rid) => rid !== id)
        : [...state.selectedRequirementIds, id],
    })),
  selectAllRequirements: () =>
    set((state) => ({
      selectedRequirementIds: state.requirements.map((r) => r.id),
    })),
  clearRequirementSelection: () => set({ selectedRequirementIds: [] }),

  // 信号相关
  signals: [],
  setSignals: (signals) => set({ signals }),

  // 测试用例相关
  testCases: [],
  setTestCases: (testCases) => set({ testCases }),
  updateTestCase: (id, data) =>
    set((state) => ({
      testCases: state.testCases.map((tc) =>
        tc.id === id ? { ...tc, ...data } : tc
      ),
    })),
  removeTestCase: (id) =>
    set((state) => ({
      testCases: state.testCases.filter((tc) => tc.id !== id),
    })),

  // 生成进度
  generationProgress: {
    current: 0,
    total: 0,
    status: 'idle',
    currentRequirement: '',
  },
  setGenerationProgress: (progress) =>
    set((state) => ({
      generationProgress: { ...state.generationProgress, ...progress },
    })),
}));
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/
git commit -m "feat: add Zustand global state store"
```

---

### Task 5: 创建主布局组件

**Files:**
- Create: `frontend/src/components/Layout/AppLayout.tsx`
- Create: `frontend/src/components/Layout/AppLayout.css`

- [ ] **Step 1: 创建主布局**

Create `frontend/src/components/Layout/AppLayout.tsx`:
```tsx
import React, { useState } from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  FileTextOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import './AppLayout.css';

const { Header, Sider, Content } = Layout;

const menuItems = [
  {
    key: '/requirements',
    icon: <FileTextOutlined />,
    label: '需求导入',
  },
  {
    key: '/signals',
    icon: <ApiOutlined />,
    label: '信号管理',
  },
  {
    key: '/testcases',
    icon: <ThunderboltOutlined />,
    label: '用例生成',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '设置',
  },
];

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();

  return (
    <Layout className="app-layout">
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        className="app-sider"
        theme="light"
      >
        <div className="app-logo">
          <ThunderboltOutlined style={{ fontSize: 24, color: token.colorPrimary }} />
          {!collapsed && <span className="app-logo-text">AISimTest</span>}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <span className="app-header-title">
            汽车空调热管理测试用例生成器
          </span>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
```

Create `frontend/src/components/Layout/AppLayout.css`:
```css
.app-layout {
  min-height: 100vh;
}

.app-sider {
  border-right: 1px solid #f0f0f0;
}

.app-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.app-logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1677ff;
}

.app-header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.app-header-title {
  font-size: 16px;
  font-weight: 500;
}

.app-content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  min-height: 280px;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add main layout component with sidebar navigation"
```

---

### Task 6: 创建页面空壳

**Files:**
- Create: `frontend/src/pages/RequirementImport.tsx`
- Create: `frontend/src/pages/SignalMatrix.tsx`
- Create: `frontend/src/pages/TestCaseGen.tsx`
- Create: `frontend/src/pages/Settings.tsx`

- [ ] **Step 1: 创建需求导入页空壳**

Create `frontend/src/pages/RequirementImport.tsx`:
```tsx
import React from 'react';
import { Typography, Empty } from 'antd';

const { Title, Paragraph } = Typography;

const RequirementImport: React.FC = () => {
  return (
    <div>
      <Title level={4}>需求导入</Title>
      <Paragraph type="secondary">
        上传 Word 格式的需求文档，系统将自动解析并条目化展示需求。
      </Paragraph>
      <Empty description="Word 文档上传功能将在下一阶段实现" />
    </div>
  );
};

export default RequirementImport;
```

Create `frontend/src/pages/SignalMatrix.tsx`:
```tsx
import React from 'react';
import { Typography, Empty } from 'antd';

const { Title, Paragraph } = Typography;

const SignalMatrix: React.FC = () => {
  return (
    <div>
      <Title level={4}>信号管理</Title>
      <Paragraph type="secondary">
        导入 Excel 格式的 CAN/LIN 信号矩阵，关联信号与需求。
      </Paragraph>
      <Empty description="信号矩阵导入功能将在下一阶段实现" />
    </div>
  );
};

export default SignalMatrix;
```

Create `frontend/src/pages/TestCaseGen.tsx`:
```tsx
import React from 'react';
import { Typography, Empty } from 'antd';

const { Title, Paragraph } = Typography;

const TestCaseGen: React.FC = () => {
  return (
    <div>
      <Title level={4}>测试用例生成</Title>
      <Paragraph type="secondary">
        选择需求条目，调用大模型智能生成功能测试用例。
      </Paragraph>
      <Empty description="测试用例生成功能将在下一阶段实现" />
    </div>
  );
};

export default TestCaseGen;
```

Create `frontend/src/pages/Settings.tsx`:
```tsx
import React from 'react';
import { Typography, Empty } from 'antd';

const { Title, Paragraph } = Typography;

const Settings: React.FC = () => {
  return (
    <div>
      <Title level={4}>系统设置</Title>
      <Paragraph type="secondary">
        配置大模型 API 参数，管理生成参数。
      </Paragraph>
      <Empty description="设置功能将在下一阶段实现" />
    </div>
  );
};

export default Settings;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: add placeholder pages for all routes"
```

---

### Task 7: 配置路由和 App 入口

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: 更新 App.tsx 配置路由**

Replace `frontend/src/App.tsx`:
```tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/Layout/AppLayout';
import RequirementImport from './pages/RequirementImport';
import SignalMatrix from './pages/SignalMatrix';
import TestCaseGen from './pages/TestCaseGen';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<RequirementImport />} />
            <Route path="requirements" element={<RequirementImport />} />
            <Route path="signals" element={<SignalMatrix />} />
            <Route path="testcases" element={<TestCaseGen />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
```

- [ ] **Step 2: 更新 main.tsx**

Replace `frontend/src/main.tsx`:
```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 3: 更新 App.css（重置样式）**

Replace `frontend/src/App.css`:
```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
```

- [ ] **Step 4: 验证前端可正常启动并导航**

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/frontend"
npm run dev
```
Expected: 浏览器打开 http://localhost:5173，可看到左侧导航栏和页面空壳，点击导航可切换页面

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx frontend/src/App.css
git commit -m "feat: configure React Router and Ant Design with all routes"
```

---

### Task 8: 初始化后端项目

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/database.py`
- Create: `backend/models/__init__.py`
- Create: `backend/models/base.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/health.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: 创建 requirements.txt**

Create `backend/requirements.txt`:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-docx==1.1.0
pandas==2.2.0
openpyxl==3.1.2
openai==1.10.0
python-multipart==0.0.6
sqlalchemy==2.0.25
aiosqlite==0.19.0
cryptography==42.0.0
httpx==0.26.0
pytest==7.4.4
pytest-asyncio==0.23.3
```

- [ ] **Step 2: 安装 Python 依赖**

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/backend"
pip install -r requirements.txt
```

- [ ] **Step 3: 创建数据库配置**

Create `backend/database.py`:
```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'aisimtest.db')}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 4: 创建基础模型**

Create `backend/models/__init__.py`:
```python
from .base import Requirement, Signal, TestCase, LLMConfig

__all__ = ['Requirement', 'Signal', 'TestCase', 'LLMConfig']
```

Create `backend/models/base.py`:
```python
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey, JSON
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


class TestCase(Base):
    __tablename__ = 'test_cases'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    requirement_id = Column(String, ForeignKey('requirements.id'), nullable=False)
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
```

- [ ] **Step 5: 创建健康检查 API**

Create `backend/api/__init__.py`:
```python
```
(empty file)

Create `backend/api/health.py`:
```python
from fastapi import APIRouter

router = APIRouter()


@router.get('/health')
async def health_check():
    return {'status': 'ok', 'version': '0.1.0'}
```

- [ ] **Step 6: 创建 FastAPI 主入口**

Create `backend/main.py`:
```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title='AISimTest API',
    description='汽车空调热管理测试用例生成器后端 API',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health_router, prefix='/api')

# 生产环境：托管前端构建产物
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist')
if os.path.isdir(frontend_dist):
    app.mount('/', StaticFiles(directory=frontend_dist, html=True), name='frontend')
```

- [ ] **Step 7: 创建后端测试**

Create `backend/tests/__init__.py`:
```python
```
(empty file)

Create `backend/tests/test_health.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/api/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
```

- [ ] **Step 8: 运行测试验证后端**

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/backend"
python -m pytest tests/test_health.py -v
```
Expected: 测试通过，输出 `PASSED`

- [ ] **Step 9: 启动后端验证可访问**

Run:
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/backend"
python -m uvicorn main:app --reload --port 8000
```
Expected: uvicorn 启动，访问 http://localhost:8000/api/health 返回 `{"status":"ok","version":"0.1.0"}`

- [ ] **Step 10: Commit**

```bash
git add backend/
git commit -m "feat: initialize FastAPI backend with SQLite, models, and health check"
```

---

### Task 9: 端到端联调验证

- [ ] **Step 1: 同时启动前后端**

Terminal 1 (后端):
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/backend"
python -m uvicorn main:app --reload --port 8000
```

Terminal 2 (前端):
```bash
cd "D:/BaiduSyncdisk/4-学习/100-项目/184-AISimTest/frontend"
npm run dev
```

- [ ] **Step 2: 验证 API 代理连通**

在浏览器打开 http://localhost:5173，打开浏览器开发者工具 Console，执行：
```javascript
fetch('/api/health').then(r => r.json()).then(console.log)
```
Expected: 控制台输出 `{status: 'ok', version: '0.1.0'}`

- [ ] **Step 3: 验证导航功能**

在浏览器中点击左侧导航菜单的每个选项，确认：
- 需求导入页面正常显示
- 信号管理页面正常显示
- 用例生成页面正常显示
- 设置页面正常显示

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete Phase 1 - project scaffolding with working frontend and backend"
```

---

## 验收标准

- [ ] 前端 Vite dev server 在 5173 端口正常启动
- [ ] 后端 FastAPI 在 8000 端口正常启动
- [ ] SQLite 数据库文件在 `data/` 目录下自动创建
- [ ] 浏览器访问 http://localhost:5173 可看到完整布局
- [ ] 四个导航菜单均可点击切换页面
- [ ] 前端可通过代理访问后端 `/api/health` 接口
- [ ] 后端测试 `test_health.py` 通过
