import React from 'react';
import { Typography, Empty } from 'antd';

const { Title, Paragraph } = Typography;

const TestCaseGen: React.FC = () => {
  return (
    <div>
      <Title level={4}>测试用例生成</Title>
      <Paragraph type="secondary">
        选择需求条目，调用大模型智能生成功能测试用例。
      </Paragraph>
      <Empty description="测试用例生成功能将在下一阶段实现" />
    </div>
  );
};

export default TestCaseGen;
