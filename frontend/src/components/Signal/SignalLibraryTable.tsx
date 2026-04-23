import React, { useEffect, useState, useCallback } from 'react';
import { Table, Input, Space, Tag, Typography, Button, message, Popconfirm, Modal, Form, Select, InputNumber } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { signalLibraryApi } from '../../services/api';
import type { SignalLibraryItem } from '../../stores/appStore';

const { Text } = Typography;
const { confirm } = Modal;

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
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [allSelectedKeys, setAllSelectedKeys] = useState<React.Key[]>([]);
  const [editingSignal, setEditingSignal] = useState<SignalLibraryItem | null>(null);
  const [editForm] = Form.useForm();

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

  const handleEdit = (record: SignalLibraryItem) => {
    setEditingSignal(record);
    editForm.setFieldsValue({
      name: record.name,
      description: record.description,
      dataType: record.dataType,
      unit: record.unit,
      valueTable: record.valueTable,
      initialValue: record.initialValue,
      bus: record.bus,
      storageClass: record.storageClass,
      dimension: record.dimension,
      factor: record.factor,
      offset: record.offset,
      minValue: record.minValue,
      maxValue: record.maxValue,
    });
  };

  const handleEditSave = async () => {
    try {
      const values = await editForm.validateFields();
      await signalLibraryApi.update(editingSignal!.id, values);
      message.success('信号更新成功');
      setEditingSignal(null);
      editForm.resetFields();
      loadData();
    } catch (error) {
      message.error('信号更新失败');
    }
  };

  const handleEditCancel = () => {
    setEditingSignal(null);
    editForm.resetFields();
  };

  const handleDelete = async (id: string) => {
    try {
      await signalLibraryApi.delete(id);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSelectAll = async () => {
    try {
      setLoading(true);
      const response = await signalLibraryApi.selectAll(search || undefined);
      if (response.data.success && response.data.data) {
        setAllSelectedKeys(response.data.data.ids);
        message.success(`已选中全部 ${response.data.data.total} 个信号`);
      }
    } catch (error) {
      message.error('全选失败');
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    try {
      const response = await signalLibraryApi.deleteAll();
      if (response.data.success) {
        message.success(`已清空 ${response.data.data.deleted} 个信号`);
        setAllSelectedKeys([]);
        setSelectedRowKeys([]);
        loadData();
      }
    } catch (error) {
      message.error('清空失败');
    }
  };

  const handleBatchDelete = () => {
    if (allSelectedKeys.length === 0) {
      message.warning('请先选择要删除的信号');
      return;
    }

    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除选中的 ${allSelectedKeys.length} 个信号吗？此操作不可恢复。`,
      okText: '确认删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await signalLibraryApi.deleteBatch(allSelectedKeys as string[]);
          message.success(`成功删除 ${allSelectedKeys.length} 个信号`);
          setAllSelectedKeys([]);
          setSelectedRowKeys([]);
          loadData();
        } catch (error) {
          message.error('批量删除失败');
        }
      },
    });
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
      title: '因子',
      dataIndex: 'factor',
      key: 'factor',
      width: 80,
      render: (v: number) => v?.toFixed(2) || '-',
    },
    {
      title: '偏移量',
      dataIndex: 'offset',
      key: 'offset',
      width: 80,
      render: (v: number) => v?.toFixed(2) || '-',
    },
    {
      title: '总线',
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
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              handleEdit(record);
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此信号？"
            onConfirm={(e) => {
              e?.stopPropagation();
              handleDelete(record.id);
            }}
            okText="确认"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={(e) => e.stopPropagation()}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys: allSelectedKeys,
    onChange: (keys: React.Key[]) => {
      // 合并跨页选择：移除当前页已选但新选择中不再有的，加上新选择的
      const currentPageKeys = data.map((item) => item.id);
      const newKeys = keys as React.Key[];
      const toAdd = newKeys.filter((k) => !allSelectedKeys.includes(k));
      const toRemove = allSelectedKeys.filter((k) => currentPageKeys.includes(k) && !newKeys.includes(k));
      setAllSelectedKeys([...allSelectedKeys.filter((k) => !toRemove.includes(k)), ...toAdd]);
    },
    preserveSelectedRowKeys: true,
  };

  return (
    <div>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Space>
          <Input.Search
            placeholder="搜索信号名或描述"
            onSearch={handleSearch}
            style={{ width: 300 }}
            allowClear
          />
          <Text type="secondary">共 {total} 个信号</Text>
          <Button size="small" onClick={handleSelectAll}>
            全选
          </Button>
          {allSelectedKeys.length > 0 && (
            <Button size="small" onClick={() => setAllSelectedKeys([])}>
              取消全选
            </Button>
          )}
        </Space>
        <Space>
          {allSelectedKeys.length > 0 && (
            <Button danger icon={<DeleteOutlined />} onClick={handleBatchDelete}>
              批量删除 ({allSelectedKeys.length})
            </Button>
          )}
          <Popconfirm
            title="确认清空"
            description="确定要删除信号库中的所有信号吗？此操作不可恢复。"
            onConfirm={handleClearAll}
            okText="确认"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button danger type="text">
              清空全部
            </Button>
          </Popconfirm>
        </Space>
      </Space>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1400 }}
        size="small"
        rowSelection={rowSelection}
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

      <Modal
        title="编辑信号"
        open={!!editingSignal}
        onOk={handleEditSave}
        onCancel={handleEditCancel}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="信号名">
            <Input disabled />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input />
          </Form.Item>
          <Form.Item name="dataType" label="数据类型">
            <Select allowClear>
              <Select.Option value="boolean">boolean</Select.Option>
              <Select.Option value="double">double</Select.Option>
              <Select.Option value="int8">int8</Select.Option>
              <Select.Option value="uint8">uint8</Select.Option>
              <Select.Option value="int16">int16</Select.Option>
              <Select.Option value="uint16">uint16</Select.Option>
              <Select.Option value="int32">int32</Select.Option>
              <Select.Option value="uint32">uint32</Select.Option>
              <Select.Option value="single">single</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="unit" label="单位">
            <Input />
          </Form.Item>
          <Form.Item name="valueTable" label="值表">
            <Input placeholder="例如: 0=OFF,1=ON" />
          </Form.Item>
          <Form.Item name="initialValue" label="初始值">
            <Input />
          </Form.Item>
          <Form.Item name="bus" label="总线">
            <Input />
          </Form.Item>
          <Form.Item name="storageClass" label="存储类型">
            <Input />
          </Form.Item>
          <Form.Item name="dimension" label="维度">
            <Input />
          </Form.Item>
          <Space>
            <Form.Item name="factor" label="因子" style={{ width: 120 }}>
              <InputNumber step={0.01} />
            </Form.Item>
            <Form.Item name="offset" label="偏移量" style={{ width: 120 }}>
              <InputNumber step={0.01} />
            </Form.Item>
            <Form.Item name="minValue" label="最小值" style={{ width: 120 }}>
              <InputNumber />
            </Form.Item>
            <Form.Item name="maxValue" label="最大值" style={{ width: 120 }}>
              <InputNumber />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  );
};

export default SignalLibraryTable;
