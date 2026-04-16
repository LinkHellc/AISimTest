import React, { useState, useEffect, useCallback } from 'react';
import { Typography, Table, Button, Space, Modal, Form, Input, message, Popconfirm, Select, Tag, Card, Alert, Upload, Progress } from 'antd';
import type { Key } from 'react';
import { PlusOutlined, EditOutlined, DeleteOutlined, UploadOutlined, InboxOutlined, ReloadOutlined } from '@ant-design/icons';
import { requirementApi } from '../services/api';
import { useAppStore } from '../stores/appStore';
import type { Requirement } from '../types';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;
const { Dragger } = Upload;

const Requirements: React.FC = () => {
  const requirements = useAppStore((s) => s.requirements);
  const setRequirements = useAppStore((s) => s.setRequirements);
  const [modal, setModal] = useState<{ open: boolean; editing?: Requirement }>({ open: false });
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<Key[]>([]);

  // 接口导入状态
  const [selectedReqId, setSelectedReqId] = useState<string | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importProgress, setImportProgress] = useState(0);

  const loadRequirements = useCallback(async () => {
    try {
      const res = await requirementApi.getRequirements();
      if (res.data.success && res.data.data) {
        setRequirements(res.data.data);
      }
    } catch { /* ignore */ }
  }, [setRequirements]);

  useEffect(() => { loadRequirements(); }, [loadRequirements]);

  const handleAdd = () => {
    form.resetFields();
    setModal({ open: true });
  };

  const handleEdit = (req: Requirement) => {
    form.setFieldsValue({
      title: req.title,
      signalInterfaces: (req.signalInterfaces || []).join(', '),
      sceneDescription: req.sceneDescription,
      functionDescription: req.functionDescription,
      entryCondition: req.entryCondition,
      executionBody: req.executionBody,
      exitCondition: req.exitCondition,
      postExitBehavior: req.postExitBehavior,
    });
    setModal({ open: true, editing: req });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const rawNames: string[] = values.signalInterfaces
        ? values.signalInterfaces.split(',').map((s: string) => s.trim()).filter(Boolean)
        : [];
      const signalInterfaces = rawNames.map(name => ({ name, type: 'Input' as const }));
      const payload = {
        title: values.title,
        signalInterfaces,
        sceneDescription: values.sceneDescription || '',
        functionDescription: values.functionDescription || '',
        entryCondition: values.entryCondition || '',
        executionBody: values.executionBody || '',
        exitCondition: values.exitCondition || '',
        postExitBehavior: values.postExitBehavior || '',
      };
      if (modal.editing) {
        await requirementApi.updateRequirement(modal.editing.id, payload);
        message.success('更新成功');
      }
      setModal({ open: false });
      await loadRequirements();
    } catch { /* validation error shown by form */ }
    finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await requirementApi.deleteRequirement(id);
      message.success('删除成功');
      await loadRequirements();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的需求');
      return;
    }
    try {
      await Promise.all(selectedRowKeys.map(id => requirementApi.deleteRequirement(id as string)));
      message.success(`成功删除 ${selectedRowKeys.length} 条需求`);
      setSelectedRowKeys([]);
      await loadRequirements();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '批量删除失败');
    }
  };

  const handleImportExcel = async (file: File) => {
    if (!selectedReqId) {
      message.warning('请先选择一个需求');
      return false;
    }
    setImportLoading(true);
    setImportProgress(20);
    try {
      setImportProgress(50);
      const res = await requirementApi.uploadInterfaces(selectedReqId, file);
      setImportProgress(100);
      if (res.data.success) {
        const d = res.data.data;
        message.success(`成功导入 ${d.added} 个信号（已共存 ${d.total} 个）`);
        await loadRequirements();
      } else {
        message.error(res.data.error || '导入失败');
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || '导入失败');
    } finally {
      setImportLoading(false);
      setTimeout(() => setImportProgress(0), 1500);
    }
    return false;
  };

  const columns = [
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
      width: 180,
      ellipsis: true,
    },
    {
      title: '信号接口',
      dataIndex: 'signalInterfaces',
      key: 'signalInterfaces',
      width: 380,
      render: (sigs: { name: string; type: 'Input' | 'Output' }[]) => {
        if (!sigs || sigs.length === 0) return <Text type="secondary">-</Text>;
        const inputs = sigs.filter(s => s.type === 'Input');
        const outputs = sigs.filter(s => s.type === 'Output');
        const maxRows = Math.max(inputs.length, outputs.length);
        const rows = Array.from({ length: maxRows }, (_, i) => ({
          input: inputs[i] ? inputs[i].name : '',
          output: outputs[i] ? outputs[i].name : '',
        }));
        return (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ width: '50%', padding: '3px 8px', textAlign: 'center', background: '#f6ffed', border: '1px solid #b7eb8f', color: '#52c41a', fontWeight: 600, fontSize: 12 }}>输入 ({inputs.length})</th>
                <th style={{ width: '50%', padding: '3px 8px', textAlign: 'center', background: '#e6f4ff', border: '1px solid #91caff', color: '#1677ff', fontWeight: 600, fontSize: 12 }}>输出 ({outputs.length})</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i}>
                  <td style={{ padding: '2px 8px', border: '1px solid #f0f0f0', fontFamily: 'Consola, monospace', fontSize: 11, color: row.input ? '#389e0d' : 'transparent' }}>{row.input || '-'}</td>
                  <td style={{ padding: '2px 8px', border: '1px solid #f0f0f0', fontFamily: 'Consola, monospace', fontSize: 11, color: row.output ? '#1677ff' : 'transparent' }}>{row.output || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        );
      },
    },
    {
      title: '功能触发条件',
      dataIndex: 'entryCondition',
      key: 'entryCondition',
      width: 200,
      ellipsis: true,
      render: (v: string) => <span title={v}>{v || '-'}</span>,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: unknown, record: Requirement) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)} okText="删除" cancelText="取消">
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>需求管理</Title>
      <Paragraph type="secondary">
        管理和编辑已导入的需求，支持通过 Word 文档导入或手动新增。
      </Paragraph>

      {/* 接口信号导入区域 */}
      <Card title="接口信号导入" size="small" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Alert
            message="为指定需求导入接口信号 Excel，以最新导入数据为准，覆盖已有数据。"
            type="info"
            showIcon
          />
          <Space>
            <Text>选择需求：</Text>
            <Select
              style={{ width: 300 }}
              placeholder="请选择要导入接口的需求"
              value={selectedReqId}
              onChange={setSelectedReqId}
              allowClear
              options={requirements.map(r => ({ label: `[${r.id}] ${r.title}`, value: r.id }))}
            />
          </Space>
          <Dragger
            accept=".xlsx,.xls"
            showUploadList={false}
            disabled={!selectedReqId || importLoading}
            beforeUpload={handleImportExcel}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">
              {selectedReqId ? '点击或拖拽 Excel 文件导入接口信号' : '请先选择需求'}
            </p>
            <p className="ant-upload-hint">支持 .xlsx/.xls 格式</p>
          </Dragger>
          {importProgress > 0 && (
            <Progress percent={importProgress} status={importProgress === 100 ? 'success' : 'active'} />
          )}
        </Space>
      </Card>

      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增需求</Button>
          <Button icon={<UploadOutlined />} onClick={loadRequirements}>刷新</Button>
        </Space>
        {selectedRowKeys.length > 0 && (
          <Button danger icon={<DeleteOutlined />} onClick={handleBatchDelete}>
            批量删除 ({selectedRowKeys.length})
          </Button>
        )}
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={requirements}
        size="small"
        pagination={{ pageSize: 10, current: 1, showSizeChanger: false }}
        bordered
        scroll={{ x: 'max-content' }}
        rowSelection={{
          selectedRowKeys,
          onChange: (keys) => setSelectedRowKeys(keys),
        }}
      />

      <Modal
        open={modal.open}
        title={modal.editing ? '编辑需求' : '新增需求'}
        onOk={handleSave}
        onCancel={() => setModal({ open: false })}
        confirmLoading={saving}
        width={700}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="功能需求名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="如：蓝牙通话降风速" />
          </Form.Item>
          <Form.Item name="signalInterfaces" label="信号接口（逗号分隔）">
            <Select
              mode="tags"
              placeholder="输入信号名，按回车确认"
              tokenSeparators={[',']}
            />
          </Form.Item>
          <Form.Item name="sceneDescription" label="场景描述">
            <TextArea rows={2} placeholder="描述功能在什么工况下被触发" />
          </Form.Item>
          <Form.Item name="functionDescription" label="功能描述">
            <TextArea rows={2} placeholder="概括功能的整体行为" />
          </Form.Item>
          <Form.Item name="entryCondition" label="功能触发条件">
            <TextArea rows={2} placeholder="满足哪些条件时功能激活" />
          </Form.Item>
          <Form.Item name="executionBody" label="功能进入后执行">
            <TextArea rows={2} placeholder="功能激活后系统执行的具体动作" />
          </Form.Item>
          <Form.Item name="exitCondition" label="功能退出条件">
            <TextArea rows={2} placeholder="满足哪些条件时功能退出" />
          </Form.Item>
          <Form.Item name="postExitBehavior" label="功能退出后执行">
            <TextArea rows={2} placeholder="功能退出后系统如何恢复或切换状态" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Requirements;
