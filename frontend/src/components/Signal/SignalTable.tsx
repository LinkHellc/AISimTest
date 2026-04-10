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
    (s.messageId && s.messageId.toLowerCase().includes(searchText.toLowerCase()))
  );

  const columns: ColumnsType<Signal> = [
    { title: '信号名称', dataIndex: 'name', key: 'name', width: 200, ellipsis: true },
    { title: '消息ID', dataIndex: 'messageId', key: 'messageId', width: 120 },
    { title: '起始位', dataIndex: 'startBit', key: 'startBit', width: 80 },
    { title: '长度', dataIndex: 'length', key: 'length', width: 80 },
    { title: '精度', dataIndex: 'factor', key: 'factor', width: 80 },
    { title: '偏移', dataIndex: 'offset', key: 'offset', width: 80 },
    { title: '范围', key: 'range', width: 150, render: (_, record) => `${record.minValue} ~ ${record.maxValue}` },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 80 },
    { title: '总线', dataIndex: 'busType', key: 'busType', width: 80, render: (val: string) => <Tag color={val === 'CAN' ? 'blue' : 'green'}>{val}</Tag> },
  ];

  return (
    <div>
      <Input.Search
        placeholder="搜索信号名称或消息ID"
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
