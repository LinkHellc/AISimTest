import React from 'react';
import { Descriptions, Tag, Typography } from 'antd';
import { useAppStore } from '../../stores/appStore';

const { Paragraph } = Typography;

interface Props {
  requirementId: string;
}

const RequirementDetail: React.FC<Props> = ({ requirementId }) => {
  const requirements = useAppStore((s) => s.requirements);
  const req = requirements.find((r) => r.id === requirementId);

  if (!req) {
    return <div>未找到需求信息</div>;
  }

  return (
    <Descriptions bordered column={1} size="small">
      <Descriptions.Item label="需求ID">{req.id}</Descriptions.Item>
      <Descriptions.Item label="标题">{req.title}</Descriptions.Item>
      <Descriptions.Item label="描述">
        <Paragraph>{req.description || '无描述'}</Paragraph>
      </Descriptions.Item>
      <Descriptions.Item label="层级">
        <Tag>Level {req.level}</Tag>
      </Descriptions.Item>
      <Descriptions.Item label="来源">{req.sourceLocation}</Descriptions.Item>
      {req.acceptanceCriteria && req.acceptanceCriteria.length > 0 && (
        <Descriptions.Item label="验收标准">
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {req.acceptanceCriteria.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Descriptions.Item>
      )}
    </Descriptions>
  );
};

export default RequirementDetail;
