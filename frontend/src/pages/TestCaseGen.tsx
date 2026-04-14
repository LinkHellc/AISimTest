import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Typography, Table, Button, Space, Card, message, Tag, Popconfirm, Input } from 'antd';
import { ThunderboltOutlined, FileExcelOutlined, FileWordOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import TestCaseEditModal from '../components/TestCase/TestCaseEditModal';
import { testCaseApi, requirementApi } from '../services/api';
import { useAppStore } from '../stores/appStore';
import type { Requirement, TestCase } from '../types';

const { Title, Paragraph, Text } = Typography;

const TestCaseGen: React.FC = () => {
  const requirements = useAppStore((s) => s.requirements);
  const setRequirements = useAppStore((s) => s.setRequirements);
  const testCases = useAppStore((s) => s.testCases);
  const setTestCases = useAppStore((s) => s.setTestCases);
  const updateTestCase = useAppStore((s) => s.updateTestCase);
  const removeTestCase = useAppStore((s) => s.removeTestCase);
  const [generating, setGenerating] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);

  const loadRequirements = useCallback(async () => {
    try {
      const res = await requirementApi.getRequirements();
      if (res.data.success && res.data.data) {
        setRequirements(res.data.data);
      }
    } catch { /* ignore */ }
  }, [setRequirements]);

  const loadTestCases = useCallback(async () => {
    try {
      const res = await testCaseApi.getTestCases();
      if (res.data.success && res.data.data) {
        setTestCases(res.data.data);
      }
    } catch { /* ignore */ }
  }, [setTestCases]);

  useEffect(() => { loadRequirements(); }, [loadRequirements]);
  useEffect(() => { loadTestCases(); }, [loadTestCases]);

  // 按需求ID分组测试用例
  const testCasesByReq = useMemo(() => {
    const map: Record<string, TestCase[]> = {};
    testCases.forEach(tc => {
      if (!map[tc.requirementId]) map[tc.requirementId] = [];
      map[tc.requirementId].push(tc);
    });
    return map;
  }, [testCases]);

  const handleGenerate = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择需求条目');
      return;
    }
    setGenerating(true);
    try {
      const res = await testCaseApi.generate(selectedRowKeys);
      if (res.data.success && res.data.data) {
        setTestCases(res.data.data);
        message.success(`成功生成 ${res.data.data.length} 条测试用例`);
        setSelectedRowKeys([]);
      } else {
        message.error(res.data.error || '生成失败');
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || error.message || '生成失败');
    } finally {
      setGenerating(false);
    }
  };

  const handleEdit = (tc: TestCase) => {
    setEditingCase(tc);
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

  const handleDeleteTestCase = async (id: string) => {
    try {
      await testCaseApi.deleteTestCase(id);
      removeTestCase(id);
      message.success('删除成功');
    } catch {
      message.error('删除失败');
    }
  };

  const handleExportExcel = async () => {
    try {
      const ids = testCases.length > 0 ? testCases.map(tc => tc.id) : undefined;
      const res = await testCaseApi.exportExcel(ids);
      // 从 Content-Disposition 解析文件名
      const cd = res.headers['content-disposition'];
      let filename = '测试用例.xlsx';
      if (cd) {
        const match = cd.match(/filename[^;=\n]*=(?:(\\?['"])(.*?)\1|([^;\n]*))/i);
        if (match) filename = decodeURIComponent(match[2] || match[3] || '测试用例.xlsx');
      }
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
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

  // 需求列 - 直接用 Requirement 对象，record 就是 Requirement
  const reqColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 90,
      render: (id: string) => <Text type="secondary" style={{ fontFamily: 'monospace', fontSize: 12 }}>{id}</Text>,
    },
    {
      title: '功能需求名称',
      dataIndex: 'title',
      key: 'title',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'TestModel',
      dataIndex: 'testModel',
      key: 'testModel',
      width: 120,
      render: (val: string, record: Requirement) => (
        <div onClick={e => e.stopPropagation()}>
          <Input
            size="small"
            placeholder="模型名称"
            defaultValue={val || ''}
            onBlur={e => requirementApi.updateRequirement(record.id, { testModel: e.target.value })}
          />
        </div>
      ),
    },
    {
      title: 'TestUnitModel',
      dataIndex: 'testUnitModel',
      key: 'testUnitModel',
      width: 120,
      render: (val: string, record: Requirement) => (
        <div onClick={e => e.stopPropagation()}>
          <Input
            size="small"
            placeholder="单元名称"
            defaultValue={val || ''}
            onBlur={e => requirementApi.updateRequirement(record.id, { testUnitModel: e.target.value })}
          />
        </div>
      ),
    },
    {
      title: '信号接口',
      dataIndex: 'signalInterfaces',
      key: 'signalInterfaces',
      width: 280,
      render: (sigs: { name: string; type: 'Input' | 'Output' }[]) => {
        if (!sigs || sigs.length === 0) return <Text type="secondary">-</Text>;
        const inputs = sigs.filter(s => s.type === 'Input');
        const outputs = sigs.filter(s => s.type === 'Output');
        return (
          <span style={{ display: 'flex', gap: 4 }}>
            {inputs.length > 0 && <Tag color="green">入{inputs.length}</Tag>}
            {outputs.length > 0 && <Tag color="blue">出{outputs.length}</Tag>}
          </span>
        );
      },
    },
    {
      title: '测试用例',
      key: 'testcase_count',
      width: 100,
      render: (_: unknown, record: Requirement) => {
        const count = testCasesByReq[record.id]?.length || 0;
        return count > 0 ? (
          <span
            style={{ color: '#1677ff', cursor: 'pointer' }}
            onClick={() => setExpandedRowKeys(prev =>
              prev.includes(record.id) ? prev.filter(k => k !== record.id) : [...prev, record.id]
            )}
          >
            {count} 条 {expandedRowKeys.includes(record.id) ? '收起' : '查看'}
          </span>
        ) : <Text type="secondary">无</Text>;
      },
    },
  ];

  const reqRowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => {
      setSelectedRowKeys(keys as string[]);
    },
  };

  const expandedRowRender = (record: Requirement) => {
    const tcs = testCasesByReq[record.id] || [];
    if (tcs.length === 0) return <div style={{ padding: '8px 12px', color: '#999' }}>暂无测试用例</div>;
    return (
      <div style={{ padding: '4px 0' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#fafafa' }}>
              <th style={{ padding: '4px 12px', width: 130, fontSize: 12, color: '#666' }}>用例ID</th>
              <th style={{ padding: '4px 12px', width: 200, fontSize: 12, color: '#666' }}>名称</th>
              <th style={{ padding: '4px 12px', width: 70, fontSize: 12, color: '#666' }}>类型</th>
              <th style={{ padding: '4px 12px', fontSize: 12, color: '#666' }}>前提条件</th>
              <th style={{ padding: '4px 12px', width: 100, fontSize: 12, color: '#666' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {tcs.map(tc => (
              <tr key={tc.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ padding: '6px 12px', fontFamily: 'monospace', fontSize: 12, color: '#666' }}>{tc.id}</td>
                <td style={{ padding: '6px 12px', fontSize: 13 }}>{tc.name}</td>
                <td style={{ padding: '6px 12px' }}>
                  <Tag color={tc.category === 'positive' ? 'green' : 'red'} style={{ margin: 0 }}>
                    {tc.category === 'positive' ? '正例' : '反例'}
                  </Tag>
                </td>
                <td style={{ padding: '6px 12px', fontSize: 12, color: '#666', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={tc.precondition}>{tc.precondition || '-'}</td>
                <td style={{ padding: '6px 12px' }}>
                  <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(tc)} />
                  <Popconfirm title="确认删除?" onConfirm={() => handleDeleteTestCase(tc.id)} okText="删除" cancelText="取消">
                    <Button size="small" danger icon={<DeleteOutlined />} style={{ marginLeft: 4 }} />
                  </Popconfirm>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div>
      <Title level={4}>测试用例生成</Title>
      <Paragraph type="secondary">
        选择需求条目，调用大模型智能生成功能测试用例。
      </Paragraph>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" icon={<ThunderboltOutlined />} loading={generating} onClick={handleGenerate}>
            生成测试用例
          </Button>
          <Button icon={<FileExcelOutlined />} onClick={handleExportExcel} disabled={testCases.length === 0}>
            导出 Excel
          </Button>
          <Button icon={<FileWordOutlined />} onClick={handleExportWord} disabled={testCases.length === 0}>
            导出 Word
          </Button>
          {selectedRowKeys.length > 0 && (
            <span style={{ color: '#1677ff', fontWeight: 500 }}>已选 {selectedRowKeys.length} 条需求</span>
          )}
        </Space>
      </Card>

      <Table
        rowKey="id"
        columns={reqColumns}
        dataSource={requirements}
        rowSelection={reqRowSelection}
        expandable={{
          expandedRowKeys,
          expandedRowRender,
          onExpand: (expanded, record) => {
            setExpandedRowKeys(prev =>
              expanded ? [...prev, record.id] : prev.filter(k => k !== record.id)
            );
          },
          showExpandColumn: false,
        }}
        size="small"
        pagination={{ pageSize: 10 }}
        bordered
      />

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
