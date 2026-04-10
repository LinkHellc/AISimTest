import React, { useEffect, useState } from 'react';
import { Form, Input, Select, Slider, InputNumber, Button, message, Space, Alert } from 'antd';
import { configApi } from '../../services/api';

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'qianwen', label: '通义千问' },
  { value: 'wenxin', label: '文心一言' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'custom', label: '自定义' },
];

const providerUrls: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  azure: '',
  qianwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  wenxin: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop',
  deepseek: 'https://api.deepseek.com/v1',
};

const LLMConfigForm: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await configApi.getLLMConfig();
        if (res.data.success && res.data.data) {
          form.setFieldsValue(res.data.data);
        }
      } catch { /* ignore */ }
    };
    loadConfig();
  }, [form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await configApi.updateLLMConfig(values);
      message.success('配置已保存');
    } catch (error: any) {
      if (error.errorFields) return;
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    try {
      const values = await form.validateFields();
      setTestLoading(true);
      setTestResult(null);
      const res = await configApi.testConnection(values);
      if (res.data.success && res.data.data) {
        setTestResult(res.data.data);
      }
    } catch {
      setTestResult({ success: false, message: '请求失败' });
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <Form form={form} layout="vertical" initialValues={{ provider: 'openai', temperature: 0.7, maxTokens: 2000 }}>
      <Form.Item name="provider" label="模型提供商" rules={[{ required: true }]}>
        <Select options={providerOptions} onChange={(val) => {
          if (providerUrls[val]) form.setFieldsValue({ baseUrl: providerUrls[val] });
        }} />
      </Form.Item>
      <Form.Item name="apiKey" label="API Key" rules={[{ required: true, message: '请输入 API Key' }]}>
        <Input.Password placeholder="sk-..." />
      </Form.Item>
      <Form.Item name="baseUrl" label="Base URL">
        <Input placeholder="https://api.openai.com/v1" />
      </Form.Item>
      <Form.Item name="model" label="模型名称" rules={[{ required: true }]}>
        <Input placeholder="gpt-4" />
      </Form.Item>
      <Form.Item name="temperature" label="Temperature">
        <Slider min={0} max={2} step={0.1} />
      </Form.Item>
      <Form.Item name="maxTokens" label="Max Tokens">
        <InputNumber min={100} max={8000} step={100} style={{ width: '100%' }} />
      </Form.Item>

      {testResult && (
        <Alert
          type={testResult.success ? 'success' : 'error'}
          message={testResult.message}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Space>
        <Button type="primary" loading={loading} onClick={handleSave}>保存配置</Button>
        <Button loading={testLoading} onClick={handleTest}>测试连接</Button>
      </Space>
    </Form>
  );
};

export default LLMConfigForm;
