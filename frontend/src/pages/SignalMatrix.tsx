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
