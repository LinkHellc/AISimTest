import React, { useState } from 'react';
import { Typography, Card, Button, Space, Divider, message } from 'antd';
import { ThunderboltOutlined, FileExcelOutlined, FileWordOutlined } from '@ant-design/icons';
import TestCaseList from '../components/TestCase/TestCaseList';
import TestCaseEditModal from '../components/TestCase/TestCaseEditModal';
import { testCaseApi } from '../services/api';
import { useAppStore } from '../stores/appStore';
import type { TestCase } from '../types';

const { Title, Paragraph } = Typography;

const TestCaseGen: React.FC = () => {
  const selectedRequirementIds = useAppStore((s) => s.selectedRequirementIds);
  const testCases = useAppStore((s) => s.testCases);
  const setTestCases = useAppStore((s) => s.setTestCases);
  const updateTestCase = useAppStore((s) => s.updateTestCase);
  const removeTestCase = useAppStore((s) => s.removeTestCase);
  const [generating, setGenerating] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);

  const handleGenerate = async () => {
    if (selectedRequirementIds.length === 0) {
      message.warning('请先在需求导入页选择需求条目');
      return;
    }
    setGenerating(true);
    try {
      const res = await testCaseApi.generate(selectedRequirementIds);
      if (res.data.success && res.data.data) {
        setTestCases(res.data.data);
        message.success(`成功生成 ${res.data.data.length} 条测试用例`);
      } else {
        message.error(res.data.error || '生成失败');
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail || error.message || '生成失败';
      message.error(detail);
    } finally {
      setGenerating(false);
    }
  };

  const handleEdit = (testCase: TestCase) => {
    setEditingCase(testCase);
    setEditModalVisible(true);
  };

  const handleSaveEdit = async (id: string, data: Partial<TestCase>) => {
    try {
      await testCaseApi.updateTestCase(id, data);
      updateTestCase(id, data);
      setEditModalVisible(false);
      message.success('用例已更新');
    } catch {
      message.error('更新失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await testCaseApi.deleteTestCase(id);
      removeTestCase(id);
      message.success('用例已删除');
    } catch {
      message.error('删除失败');
    }
  };

  const handleExportExcel = async () => {
    try {
      const ids = testCases.length > 0 ? testCases.map(tc => tc.id) : undefined;
      const res = await testCaseApi.exportExcel(ids);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '测试用例.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      message.error('导出失败');
    }
  };

  const handleExportWord = async () => {
    try {
      const ids = testCases.length > 0 ? testCases.map(tc => tc.id) : undefined;
      const res = await testCaseApi.exportWord(ids);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '测试用例.docx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      message.error('导出失败');
    }
  };

  return (
    <div>
      <Title level={4}>测试用例生成</Title>
      <Paragraph type="secondary">
        选择需求条目，调用大模型智能生成功能测试用例。
      </Paragraph>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={generating}
            onClick={handleGenerate}
          >
            生成测试用例
          </Button>
          <Button
            icon={<FileExcelOutlined />}
            onClick={handleExportExcel}
            disabled={testCases.length === 0}
          >
            导出 Excel
          </Button>
          <Button
            icon={<FileWordOutlined />}
            onClick={handleExportWord}
            disabled={testCases.length === 0}
          >
            导出 Word
          </Button>
          <span>已选择 {selectedRequirementIds.length} 条需求</span>
        </Space>
      </Card>

      {testCases.length > 0 && (
        <>
          <Divider />
          <Card title={`测试用例 (${testCases.length} 条)`} size="small">
            <TestCaseList onEdit={handleEdit} onDelete={handleDelete} />
          </Card>
        </>
      )}

      <TestCaseEditModal
        visible={editModalVisible}
        testCase={editingCase}
        onSave={handleSaveEdit}
        onCancel={() => setEditModalVisible(false)}
      />
    </div>
  );
};

export default TestCaseGen;
