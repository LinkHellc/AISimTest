import React, { useState } from 'react';
import { Typography, Card } from 'antd';
import SignalLibraryImporter from '../components/Signal/SignalLibraryImporter';
import SignalLibraryTable from '../components/Signal/SignalLibraryTable';

const { Title, Paragraph } = Typography;

const SignalMatrix: React.FC = () => {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div>
      <Title level={4}>信号管理</Title>
      <Paragraph type="secondary">
        从接口表 Excel（Input/Mea/Output sheets）导入信号详细定义，智能合并更新。
      </Paragraph>
      <Card title="导入信号库" size="small" style={{ marginBottom: 16 }}>
        <SignalLibraryImporter onSuccess={() => setRefreshKey(k => k + 1)} />
      </Card>
      <Card title="信号库列表" size="small">
        <SignalLibraryTable key={refreshKey} />
      </Card>
    </div>
  );
};

export default SignalMatrix;
