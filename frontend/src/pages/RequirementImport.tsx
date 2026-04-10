import React, { useState } from 'react';
import { Typography, Card, Row, Col, Divider } from 'antd';
import WordImporter from '../components/Document/WordImporter';
import RequirementTree from '../components/Document/RequirementTree';
import RequirementDetail from '../components/Document/RequirementDetail';
import { useAppStore } from '../stores/appStore';

const { Title, Paragraph } = Typography;

const RequirementImport: React.FC = () => {
  const requirements = useAppStore((s) => s.requirements);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div>
      <Title level={4}>需求导入</Title>
      <Paragraph type="secondary">
        上传 Word 格式的需求文档，系统将自动解析并条目化展示需求。
      </Paragraph>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="上传需求文档" size="small">
            <WordImporter />
          </Card>
        </Col>
      </Row>

      {requirements.length > 0 && (
        <>
          <Divider />
          <Row gutter={16}>
            <Col span={12}>
              <Card title={`需求列表 (${requirements.length} 条)`} size="small">
                <RequirementTree onSelect={(id) => setSelectedId(id)} />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="需求详情" size="small">
                {selectedId ? (
                  <RequirementDetail requirementId={selectedId} />
                ) : (
                  <Paragraph type="secondary">点击左侧需求查看详情</Paragraph>
                )}
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default RequirementImport;
