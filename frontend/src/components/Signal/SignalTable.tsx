import React, { useState } from 'react';
import { Table, Input, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useAppStore } from '../../stores/appStore';
import type { Signal } from '../../types';

const SignalTable: React.FC = () => {
  const signals = useAppStore((s) => s.signals);
  const [searchText, setSearchText] = useState('');

  const filteredSignals = signals.filter((s) =>
    s.name.toLowerCase().includes(searchText.toLowerCase()) ||
    (s.description && s.description.toLowerCase().includes(searchText.toLowerCase()))
  );

  const columns: ColumnsType<Signal> = [
    {
      title: '方向',
      dataIndex: 'classType',
      key: 'classType',
      width: 80,
      render: (val: string) => {
        if (val === 'Input') return <Tag color="blue">输入</Tag>;
        if (val === 'Output') return <Tag color="green">输出</Tag>;
        if (val === 'Parameter') return <Tag color="orange">参数</Tag>;
        return <Tag>{val}</Tag>;
      },
    },
    {
      title: '信号名称',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      ellipsis: true,
    },
    {
      title: '数据类型',
      dataIndex: 'dataType',
      key: 'dataType',
      width: 100,
    },
    {
      title: 'Min',
      dataIndex: 'minValue',
      key: 'minValue',
      width: 70,
    },
    {
      title: 'Max',
      dataIndex: 'maxValue',
      key: 'maxValue',
      width: 70,
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 60,
    },
    {
      title: 'Offset',
      dataIndex: 'offset',
      key: 'offset',
      width: 70,
    },
    {
      title: 'Slope',
      dataIndex: 'factor',
      key: 'factor',
      width: 70,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
    },
  ];

  return (
    <div>
      <Input.Search
        placeholder="搜索信号名称或描述"
        allowClear
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 16, width: 300 }}
      />
      <Table
        columns={columns}
        dataSource={filteredSignals}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 个信号` }}
      />
    </div>
  );
};

export default SignalTable;
