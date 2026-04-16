import React, { useEffect, useState } from 'react';
import { Form, Input, Select, Slider, InputNumber, Button, message, Space, Alert } from 'antd';
import { configApi } from '../../services/api';

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'glm', label: '智谱 GLM' },
  { value: 'minimax', label: 'MiniMax' },
  { value: 'kimi', label: 'Kimi (Moonshot)' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'qianwen', label: '通义千问' },
  { value: 'wenxin', label: '文心一言' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'custom', label: '自定义' },
];

const providerUrls: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com/v1',
  glm: 'https://open.bigmodel.cn/api/paas/v4',
  minimax: 'https://api.minimaxi.com',
  kimi: 'https://api.moonshot.cn/v1',
  gemini: 'https://generativelanguage.googleapis.com/v1beta/openai/',
  qianwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  wenxin: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop',
  azure: '',
};

// 每个 provider 可选的模型列表
const providerModels: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-4.1', label: 'GPT-4.1' },
    { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini' },
    { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano' },
  ],
  deepseek: [
    { value: 'deepseek-chat', label: 'DeepSeek Chat (V3)' },
    { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner (R1)' },
  ],
  glm: [
    { value: 'glm-4-flash', label: 'GLM-4-Flash (免费)' },
    { value: 'glm-4-flash-250414', label: 'GLM-4-Flash-250414 (免费)' },
    { value: 'glm-4.5-flash', label: 'GLM-4.5-Flash (免费)' },
    { value: 'glm-4.7-flash', label: 'GLM-4.7-Flash (免费, 200K)' },
    { value: 'glm-4-plus', label: 'GLM-4-Plus (付费旗舰)' },
    { value: 'glm-4', label: 'GLM-4' },
  ],
  minimax: [
    { value: 'MiniMax-Text-01', label: 'MiniMax-Text-01' },
    { value: 'MiniMax-M2', label: 'MiniMax-M2' },
    { value: 'MiniMax-M2.5', label: 'MiniMax-M2.5' },
    { value: 'MiniMax-M2.7', label: 'MiniMax-M2.7 (最新)' },
  ],
  kimi: [
    { value: 'moonshot-v1-8k', label: 'Moonshot V1 8K' },
    { value: 'moonshot-v1-32k', label: 'Moonshot V1 32K' },
    { value: 'moonshot-v1-128k', label: 'Moonshot V1 128K' },
  ],
  gemini: [
    { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
    { value: 'gemini-2.0-flash-lite', label: 'Gemini 2.0 Flash-Lite' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
  ],
  qianwen: [
    { value: 'qwen-plus', label: 'Qwen-Plus' },
    { value: 'qwen-turbo', label: 'Qwen-Turbo' },
    { value: 'qwen-max', label: 'Qwen-Max' },
    { value: 'qwen-long', label: 'Qwen-Long' },
  ],
  wenxin: [
    { value: 'ernie-4.0-8k', label: 'ERNIE 4.0 8K' },
    { value: 'ernie-3.5-8k', label: 'ERNIE 3.5 8K' },
    { value: 'ernie-speed-128k', label: 'ERNIE Speed 128K' },
  ],
  azure: [],
  custom: [],
};

const LLMConfigForm: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [currentProvider, setCurrentProvider] = useState('openai');

  const modelOptions = providerModels[currentProvider] || [];

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await configApi.getLLMConfig();
        if (res.data.success && res.data.data) {
          form.setFieldsValue(res.data.data);
          if (res.data.data.provider) {
            setCurrentProvider(res.data.data.provider);
          }
        }
      } catch { /* ignore */ }
    };
    loadConfig();
  }, [form]);

  const handleProviderChange = (val: string) => {
    setCurrentProvider(val);
    const updates: Record<string, string> = {};
    if (providerUrls[val]) updates.baseUrl = providerUrls[val];
    // 自动选择第一个模型
    const models = providerModels[val];
    if (models && models.length > 0) updates.model = models[0].value;
    if (Object.keys(updates).length > 0) form.setFieldsValue(updates);
  };

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
        <Select options={providerOptions} onChange={handleProviderChange} />
      </Form.Item>
      <Form.Item name="apiKey" label="API Key" rules={[{ required: true, message: '请输入 API Key' }]}>
        <Input.Password placeholder="sk-..." />
      </Form.Item>
      {currentProvider === 'minimax' && (
        <Form.Item name="groupId" label="Group ID (MiniMax)">
          <Input.Password placeholder="请输入 MiniMax Group ID" />
        </Form.Item>
      )}
      <Form.Item name="baseUrl" label="Base URL">
        <Input placeholder="https://api.openai.com/v1" />
      </Form.Item>
      <Form.Item name="model" label="模型名称" rules={[{ required: true }]}>
        {modelOptions.length > 0 ? (
          <Select
            options={modelOptions}
            placeholder="选择模型"
            showSearch
            allowClear={false}
          />
        ) : (
          <Input placeholder="输入模型名称" />
        )}
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
