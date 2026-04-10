import React from 'react';
import { Typography, Empty } from 'antd';

const { Title, Paragraph } = Typography;

const RequirementImport: React.FC = () => {
  return (
    <div>
      <Title level={4}>需求导入</Title>
      <Paragraph type="secondary">
        上传 Word 格式的需求文档，系统将自动解析并条目化展示需求。
      </Paragraph>
      <Empty description="Word 文档上传功能将在下一阶段实现" />
    </div>
  );
};

export default RequirementImport;
