import React, { useEffect, useState } from 'react';
import { Typography, Card, Divider, Collapse, Input, Button, message, Space, Tag, Popconfirm } from 'antd';
import { EditOutlined, SaveOutlined, CloseOutlined, ReloadOutlined } from '@ant-design/icons';
import LLMConfigForm from '../components/LLM/LLMConfigForm';
import { configApi } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;
const { Panel } = Collapse;

interface PromptTemplate {
  id: string;
  name: string;
  content: string;
  description: string;
  updated_at: string;
}

const Settings: React.FC = () => {
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [loading, setLoading] = useState(false);

  const loadTemplates = async () => {
    try {
      const res = await configApi.getPromptTemplates();
      setTemplates(res.data?.data || []);
    } catch (err) {
      message.error('加载提示词模板失败');
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const handleEdit = (template: PromptTemplate) => {
    setEditingId(template.id);
    setEditContent(template.content);
  };

  const handleSave = async (id: string) => {
    setLoading(true);
    try {
      await configApi.updatePromptTemplate(id, { content: editContent });
      message.success('保存成功');
      setEditingId(null);
      loadTemplates();
    } catch (err) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditContent('');
  };

  const handleReset = async (id: string) => {
    try {
      await configApi.resetPromptTemplate(id);
      message.success('重置成功');
      loadTemplates();
    } catch (err) {
      message.error('重置失败');
    }
  };

  const renderTemplatePanel = (template: PromptTemplate) => {
    if (editingId === template.id) {
      return (
        <div>
          <TextArea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={20}
            style={{ fontFamily: 'monospace', fontSize: 12 }}
          />
          <Space style={{ marginTop: 8 }}>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={() => handleSave(template.id)}
              loading={loading}
              size="small"
            >
              保存
            </Button>
            <Button
              icon={<CloseOutlined />}
              onClick={handleCancel}
              size="small"
            >
              取消
            </Button>
          </Space>
        </div>
      );
    }

    return (
      <div>
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">{template.description}</Text>
        </div>
        <Card size="small" style={{ background: '#f5f5f5' }}>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 12, fontFamily: 'monospace' }}>
            {template.content}
          </pre>
        </Card>
        <Space style={{ marginTop: 8 }}>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(template)}
            size="small"
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要重置此模板吗？"
            onConfirm={() => handleReset(template.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" icon={<ReloadOutlined />} size="small">
              重置
            </Button>
          </Popconfirm>
        </Space>
      </div>
    );
  };

  return (
    <div>
      <Title level={4}>系统设置</Title>
      <Paragraph type="secondary">
        配置大模型 API 参数和支持编辑提示词模板。
      </Paragraph>
      <Divider />
      <Card title="大模型 API 配置" size="small" style={{ maxWidth: 600, marginBottom: 16 }}>
        <LLMConfigForm />
      </Card>

      <Divider>提示词模板</Divider>
      <Collapse defaultActiveKey={[]}>
        {templates.map((template) => (
          <Panel
            header={
              <Space>
                <Text strong>{template.name}</Text>
                {template.updated_at && (
                  <Tag color="blue">{new Date(template.updated_at).toLocaleString()}</Tag>
                )}
              </Space>
            }
            key={template.id}
          >
            {renderTemplatePanel(template)}
          </Panel>
        ))}
      </Collapse>
    </div>
  );
};

export default Settings;
