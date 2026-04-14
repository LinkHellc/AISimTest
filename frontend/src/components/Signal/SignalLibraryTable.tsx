import React, { useEffect, useState, useCallback } from 'react';
import { Table, Input, Space, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { signalLibraryApi } from '../../services/api';
import type { SignalLibraryItem } from '../../stores/appStore';

const { Text } = Typography;

interface SignalLibraryTableProps {
  onSignalSelect?: (signalName: string) => void;
}

const SignalLibraryTable: React.FC<SignalLibraryTableProps> = ({ onSignalSelect }) => {
  const [data, setData] = useState<SignalLibraryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await signalLibraryApi.getList({ search, page, pageSize });
      if (response.data.success && response.data.data) {
        setData(response.data.data.items);
        setTotal(response.data.data.total);
      }
    } catch (error) {
      console.error('Failed to load signal library:', error);
    } finally {
      setLoading(false);
    }
  }, [search, page, pageSize]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const columns: ColumnsType<SignalLibraryItem> = [
    {
      title: '信号名',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      fixed: 'left',
      render: (name: string) => (
        <Text strong copyable={{ text: name }}>
          {name}
        </Text>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 150,
      ellipsis: true,
    },
    {
      title: '数据类型',
      dataIndex: 'dataType',
      key: 'dataType',
      width: 100,
      render: (type: string) => <Tag color="blue">{type || '-'}</Tag>,
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
    },
    {
      title: '初始值',
      dataIndex: 'initialValue',
      key: 'initialValue',
      width: 100,
    },
    {
      title: '值域',
      key: 'range',
      width: 120,
      render: (_, record) => {
        const min = record.minValue ?? '-';
        const max = record.maxValue ?? '-';
        return `${min} ~ ${max}`;
      },
    },
    {
      title: 'Factor',
      dataIndex: 'factor',
      key: 'factor',
      width: 80,
      render: (v: number) => v?.toFixed(2) || '-',
    },
    {
      title: 'Offset',
      dataIndex: 'offset',
      key: 'offset',
      width: 80,
      render: (v: number) => v?.toFixed(2) || '-',
    },
    {
      title: 'Bus',
      dataIndex: 'bus',
      key: 'bus',
      width: 100,
    },
    {
      title: '存储类型',
      dataIndex: 'storageClass',
      key: 'storageClass',
      width: 120,
    },
    {
      title: '来源',
      dataIndex: 'sourceFile',
      key: 'sourceFile',
      width: 120,
      ellipsis: true,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索信号名或描述"
          onSearch={handleSearch}
          style={{ width: 300 }}
          allowClear
        />
        <Text type="secondary">共 {total} 个信号</Text>
      </Space>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        size="small"
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => {
            setPage(p);
            setPageSize(ps);
          },
        }}
        onRow={(record) => ({
          onClick: () => onSignalSelect?.(record.name),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  );
};

export default SignalLibraryTable;
