import React from 'react';
import { Typography, Card, Divider } from 'antd';
import SignalImporter from '../components/Signal/SignalImporter';
import SignalTable from '../components/Signal/SignalTable';
import { useAppStore } from '../stores/appStore';

const { Title, Paragraph } = Typography;

const SignalMatrix: React.FC = () => {
  const signals = useAppStore((s) => s.signals);

  return (
    <div>
      <Title level={4}>信号管理</Title>
      <Paragraph type="secondary">
        导入 Excel 格式的 CAN/LIN 信号矩阵，关联信号与需求。
      </Paragraph>

      <Card title="上传信号矩阵" size="small">
        <SignalImporter />
      </Card>

      {signals.length > 0 && (
        <>
          <Divider />
          <Card title={`信号列表 (${signals.length} 个)`} size="small">
            <SignalTable />
          </Card>
        </>
      )}
    </div>
  );
};

export default SignalMatrix;
