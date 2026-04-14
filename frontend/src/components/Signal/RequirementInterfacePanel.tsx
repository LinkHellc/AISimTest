import React from 'react';
import { Tag, Table, Typography, Space } from 'antd';
import type { RequirementInterface } from '../../stores/appStore';

const { Text } = Typography;

interface RequirementInterfacePanelProps {
  interfaces: RequirementInterface[];
}

const RequirementInterfacePanel: React.FC<RequirementInterfacePanelProps> = ({
  interfaces,
}) => {
  const inputSignals = interfaces.filter((i) => i.interfaceName === 'Input');
  const outputSignals = interfaces.filter((i) => i.interfaceName === 'Output');

  const columns = [
    {
      title: '信号名',
      dataIndex: 'signalName' as const,
      key: 'signalName',
      width: 200,
      render: (name: string) => <Text copyable={{ text: name }}>{name}</Text>,
    },
    {
      title: '描述',
      dataIndex: 'description' as const,
      key: 'description',
      ellipsis: true,
    },
    {
      title: '来源',
      dataIndex: 'sourceDoc' as const,
      key: 'sourceDoc',
      width: 150,
      render: (doc: string) => doc ? <Text type="secondary">{doc}</Text> : '-',
    },
  ];

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <div>
        <Tag color="green">输入 ({inputSignals.length})</Tag>
        {inputSignals.length > 0 ? (
          <Table
            columns={columns}
            dataSource={inputSignals}
            rowKey="id"
            size="small"
            pagination={false}
            style={{ marginTop: 8 }}
          />
        ) : (
          <Text type="secondary" style={{ marginTop: 8, display: 'block' }}>暂无输入接口</Text>
        )}
      </div>

      <div>
        <Tag color="blue">输出 ({outputSignals.length})</Tag>
        {outputSignals.length > 0 ? (
          <Table
            columns={columns}
            dataSource={outputSignals}
            rowKey="id"
            size="small"
            pagination={false}
            style={{ marginTop: 8 }}
          />
        ) : (
          <Text type="secondary" style={{ marginTop: 8, display: 'block' }}>暂无输出接口</Text>
        )}
      </div>
    </Space>
  );
};

export default RequirementInterfacePanel;
