import React from 'react';
import { Typography, Card, Divider } from 'antd';
import LLMConfigForm from '../components/LLM/LLMConfigForm';

const { Title, Paragraph } = Typography;

const Settings: React.FC = () => {
  return (
    <div>
      <Title level={4}>系统设置</Title>
      <Paragraph type="secondary">
        配置大模型 API 参数。支持 OpenAI、通义千问、文心一言、DeepSeek 等兼容 OpenAI 接口的服务商。
      </Paragraph>
      <Divider />
      <Card title="大模型 API 配置" size="small" style={{ maxWidth: 600 }}>
        <LLMConfigForm />
      </Card>
    </div>
  );
};

export default Settings;
