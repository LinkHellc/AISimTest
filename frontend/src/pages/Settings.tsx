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
