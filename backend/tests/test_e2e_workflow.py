"""
端到端功能测试 - 验证整体工作流

测试场景:
1. 上传文档生成需求
2. 导入接口信息
3. 导入信号库
4. 生成测试用例
5. 导出测试用例

运行方式:
    pytest backend/tests/test_e2e_workflow.py -v
    pytest backend/tests/test_e2e_workflow.py -v -k "test_workflow"  # 只运行完整流程测试
"""

import sys
import os
import pytest
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import AsyncClient, ASGITransport
from main import app
from database import init_db, engine
from sqlalchemy import text


# 测试数据路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/tests -> backend -> project root
DOC_PATH = os.path.join(PROJECT_ROOT, '..', 'docs', '用户需求', '模块需求.docx')
INTERFACE_PATH = os.path.join(PROJECT_ROOT, '..', 'docs', '用户需求', 'CbnSpc_TestHarness.xlsx')
SIGNAL_LIB_DIR = os.path.join(PROJECT_ROOT, '..', 'docs', '用户需求', '相关接口表')


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """初始化测试数据库"""
    await init_db()
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test', timeout=120.0) as c:
        yield c


@pytest.fixture(autouse=True)
async def clear_test_data():
    """每个测试前清理数据"""
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM requirements"))
        await conn.execute(text("DELETE FROM test_cases"))
        await conn.execute(text("DELETE FROM signals"))
        await conn.execute(text("DELETE FROM signal_library"))
    yield


class TestHealthCheck:
    """前置检查: 验证服务健康状态"""

    @pytest.mark.asyncio
    async def test_health(self, client):
        """验证API服务正常"""
        response = await client.get('/api/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'


class TestLLMConfig:
    """步骤0: 验证LLM配置"""

    @pytest.mark.asyncio
    async def test_llm_config_exists(self, client):
        """验证LLM配置已保存"""
        response = await client.get('/api/config/llm')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        # 验证配置存在
        config = data['data']
        assert config['provider'] == 'minimax'
        assert 'MiniMax-M2' in config['model']
        print(f"LLM配置: provider={config['provider']}, model={config['model']}")


class TestDocumentUpload:
    """步骤1: 文档上传生成需求"""

    @pytest.mark.asyncio
    async def test_upload_doc_generates_requirements(self, client, clear_test_data):
        """上传文档后能正常生成需求"""
        assert os.path.exists(DOC_PATH), f"测试文档不存在: {DOC_PATH}"

        with open(DOC_PATH, 'rb') as f:
            files = {'file': ('模块需求.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = await client.post('/api/requirements/upload', files=files)

        # 验证响应
        assert response.status_code == 200, f"上传失败: {response.text}"
        data = response.json()
        assert data['success'] is True, f"解析失败: {data}"

        requirements = data['data']
        assert isinstance(requirements, list), "需求应该是列表"
        assert len(requirements) > 0, "应该生成至少一个需求"

        # 验证需求结构
        req = requirements[0]
        assert 'id' in req, "需求缺少id字段"
        assert 'title' in req, "需求缺少title字段"
        print(f"成功生成 {len(requirements)} 个需求")
        print(f"示例需求: {req['id']} - {req['title'][:50]}...")

        return requirements


class TestInterfaceImport:
    """步骤2: 导入接口信息"""

    @pytest.mark.asyncio
    async def test_import_interface_info(self, client, clear_test_data):
        """导入接口信息Excel功能正常"""
        assert os.path.exists(INTERFACE_PATH), f"接口文件不存在: {INTERFACE_PATH}"

        # 先创建一个测试需求
        from models.base import Requirement
        from database import async_session

        async with async_session() as session:
            req = Requirement(id='TEST-REQ-001', title='测试需求')
            session.add(req)
            await session.commit()

        # 上传接口文件
        with open(INTERFACE_PATH, 'rb') as f:
            files = {'file': ('CbnSpc_TestHarness.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = await client.post('/api/requirements/TEST-REQ-001/interfaces', files=files)

        assert response.status_code == 200, f"导入接口失败: {response.text}"
        data = response.json()
        assert data['success'] is True
        print(f"成功导入接口: {data['data']}")


class TestSignalLibraryImport:
    """步骤3: 导入信号库"""

    @pytest.mark.asyncio
    async def test_import_signal_library(self, client, clear_test_data):
        """导入信号库功能正常"""
        assert os.path.exists(SIGNAL_LIB_DIR), f"信号库目录不存在: {SIGNAL_LIB_DIR}"

        # 获取目录下所有xlsx文件
        xlsx_files = [f for f in os.listdir(SIGNAL_LIB_DIR) if f.endswith('.xlsx')]
        assert len(xlsx_files) > 0, "信号库目录没有xlsx文件"

        # 上传第一个文件测试
        file_path = os.path.join(SIGNAL_LIB_DIR, xlsx_files[0])
        with open(file_path, 'rb') as f:
            files = {'file': (xlsx_files[0], f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = await client.post('/api/signals/library/upload', files=files)

        assert response.status_code == 200, f"导入信号库失败: {response.text}"
        data = response.json()
        assert data['success'] is True
        result = data['data']
        assert 'total' in result
        print(f"成功导入信号库: {xlsx_files[0]}, 共 {result['total']} 个信号")


class TestTestCaseGeneration:
    """步骤4: 生成测试用例"""

    @pytest.mark.asyncio
    async def test_generate_test_cases(self, client, clear_test_data):
        """生成测试用例功能正常"""
        # 创建测试需求
        from models.base import Requirement
        from database import async_session

        async with async_session() as session:
            req = Requirement(
                id='TEST-REQ-002',
                title='测试需求',
                scene_description='测试场景',
                function_description='测试功能',
                entry_condition='条件A',
                execution_body='执行操作',
                exit_condition='退出条件',
                post_exit_behavior='退出行为'
            )
            session.add(req)
            await session.commit()

        # 调用生成接口
        response = await client.post('/api/testcases/generate',
                                     json={'requirementIds': ['TEST-REQ-002']})

        assert response.status_code == 200, f"生成失败: {response.text}"
        data = response.json()
        assert data['success'] is True

        test_cases = data['data']
        assert isinstance(test_cases, list), "测试用例应该是列表"
        assert len(test_cases) > 0, "应该生成至少一个测试用例"
        print(f"成功生成 {len(test_cases)} 个测试用例")

        # 验证测试用例结构
        tc = test_cases[0]
        assert 'id' in tc
        assert 'name' in tc
        assert 'steps' in tc
        print(f"示例测试用例: {tc['id']} - {tc['name']}")


class TestTestCaseExport:
    """步骤5: 导出测试用例"""

    @pytest.mark.asyncio
    async def test_export_test_cases_to_excel(self, client, clear_test_data):
        """导出测试用例Excel功能正常"""
        # 创建测试需求和测试用例
        from models.base import Requirement, TestCase
        from database import async_session
        import uuid

        async with async_session() as session:
            req = Requirement(id='TEST-REQ-003', title='导出测试')
            session.add(req)
            tc = TestCase(
                id=f'TC-{uuid.uuid4().hex[:8]}',
                name='测试用例1',
                requirement_id='TEST-REQ-003',
                steps=[
                    {
                        'TestStepName': 'TS1',
                        'TestStepAction': 'gCbnSpc_TstSttVal=1',
                        'TestTransition': 'after(1,sec)',
                        'TestNextStepName': 'Init',
                        'TestVerifyName': 'TV1',
                        'WhenCondition': 't>0.5 && t<4.5',
                        'TestVerify': '',
                        'TestDescription': '步骤1'
                    }
                ]
            )
            session.add(tc)
            await session.commit()

        # 导出Excel
        response = await client.post('/api/testcases/export/excel',
                                      json={'ids': []},
                                      timeout=30.0)

        assert response.status_code == 200, f"导出失败: {response.text}"
        assert response.headers['content-type'].startswith('application/vnd.openxmlformats'), \
            "应该返回Excel文件"
        print(f"成功导出Excel, 大小: {len(response.content)} bytes")


class TestFullWorkflow:
    """完整工作流测试 (TDD模式)"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """
        完整工作流测试:
        1. 上传文档生成需求
        2. 导入接口信息
        3. 导入信号库
        4. 生成测试用例
        5. 导出测试用例

        运行此测试验证所有修改后的功能正常工作
        """
        # 创建客户端
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test', timeout=120.0) as client:
            # 清理数据
            async with engine.begin() as conn:
                await conn.execute(text("DELETE FROM requirements"))
                await conn.execute(text("DELETE FROM test_cases"))
                await conn.execute(text("DELETE FROM signals"))
                await conn.execute(text("DELETE FROM signal_library"))

            print("\n=== 开始完整工作流测试 ===")

            # 1. 上传文档
            print("\n[1/5] 上传文档...")
            assert os.path.exists(DOC_PATH)
            with open(DOC_PATH, 'rb') as f:
                files = {'file': ('模块需求.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                response = await client.post('/api/requirements/upload', files=files)
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            requirements = data['data']
            assert len(requirements) > 0
            req_id = requirements[0]['id']
            print(f"    ✓ 成功生成需求: {req_id}")

            # 2. 导入接口信息
            print("\n[2/5] 导入接口信息...")
            assert os.path.exists(INTERFACE_PATH)
            with open(INTERFACE_PATH, 'rb') as f:
                files = {'file': ('CbnSpc_TestHarness.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = await client.post(f'/api/requirements/{req_id}/interfaces', files=files)
            assert response.status_code == 200
            print(f"    ✓ 接口导入成功")

            # 3. 导入信号库
            print("\n[3/5] 导入信号库...")
            xlsx_files = [f for f in os.listdir(SIGNAL_LIB_DIR) if f.endswith('.xlsx')]
            assert len(xlsx_files) > 0
            file_path = os.path.join(SIGNAL_LIB_DIR, xlsx_files[0])
            with open(file_path, 'rb') as f:
                files = {'file': (xlsx_files[0], f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = await client.post('/api/signals/library/upload', files=files)
            assert response.status_code == 200
            print(f"    ✓ 信号库导入成功")

            # 4. 生成测试用例
            print("\n[4/5] 生成测试用例...")
            response = await client.post('/api/testcases/generate',
                                         json={'requirementIds': [req_id]})
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            test_cases = data['data']
            assert len(test_cases) > 0
            print(f"    ✓ 生成 {len(test_cases)} 个测试用例")

            # 5. 导出测试用例
            print("\n[5/5] 导出测试用例...")
            response = await client.post('/api/testcases/export/excel',
                                        json={'ids': []},
                                        timeout=30.0)
            assert response.status_code == 200
            assert response.headers['content-type'].startswith('application/vnd.openxmlformats')
            print(f"    ✓ Excel导出成功 ({len(response.content)} bytes)")

            print("\n=== 完整工作流测试通过 ===")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
