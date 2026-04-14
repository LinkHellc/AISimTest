import React from 'react';
import { Descriptions, Tag, Typography, Tabs, Alert } from 'antd';
import { useAppStore } from '../../stores/appStore';

const { Paragraph, Text } = Typography;

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
    <Tabs
      defaultActiveKey="detail"
      items={[
        {
          key: 'detail',
          label: '需求详情',
          children: (
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="需求ID">
                <Text code>{req.id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="功能需求名称">
                <Text strong>{req.title}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="场景描述">
                <Paragraph>{req.sceneDescription || '无'}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="功能描述">
                <Paragraph>{req.functionDescription || '无'}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="功能触发条件">
                <Paragraph>{req.entryCondition || '无'}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="功能进入后执行">
                <Paragraph>{req.executionBody || '无'}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="功能退出条件">
                <Paragraph>{req.exitCondition || '无'}</Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="功能退出后执行">
                <Paragraph>{req.postExitBehavior || '无'}</Paragraph>
              </Descriptions.Item>
            </Descriptions>
          ),
        },
        {
          key: 'interfaces',
          label: `接口列表 (${(req.signalInterfaces || []).length})`,
          children: (
            (req.signalInterfaces && req.signalInterfaces.length > 0) ? (
              <div>
                <Text type="secondary" style={{ marginBottom: 8, display: 'block' }}>
                  以下信号接口名称由 LLM 从文档中自动提取，可通过导入 Excel 信号库进行信息更新
                </Text>
                <div style={{ marginTop: 8 }}>
                  {(req.signalInterfaces || []).map((sig, i) => (
                    <Tag key={i} style={{ marginBottom: 4 }}>{sig}</Tag>
                  ))}
                </div>
              </div>
            ) : (
              <Alert
                type="info"
                message="暂无接口信息"
                description="从文档中未提取到信号接口，可通过 Excel 信号库导入更新接口详细信息。"
              />
            )
          ),
        },
      ]}
    />
  );
};

export default RequirementDetail;
