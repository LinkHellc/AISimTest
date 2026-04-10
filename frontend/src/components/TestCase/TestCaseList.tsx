import React from 'react';
import { Table, Tag, Button, Space, Popconfirm } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useAppStore } from '../../stores/appStore';
import type { TestCase } from '../../types';

interface Props {
  onEdit: (testCase: TestCase) => void;
  onDelete: (id: string) => void;
}

const TestCaseList: React.FC<Props> = ({ onEdit, onDelete }) => {
  const testCases = useAppStore((s) => s.testCases);

  const columns: ColumnsType<TestCase> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 130 },
    { title: '名称', dataIndex: 'name', key: 'name', width: 200, ellipsis: true },
    { title: '关联需求', dataIndex: 'requirementId', key: 'requirementId', width: 120 },
    {
      title: '类型', dataIndex: 'category', key: 'category', width: 80,
      render: (val: string) => <Tag color={val === 'positive' ? 'green' : 'red'}>{val === 'positive' ? '正例' : '反例'}</Tag>,
    },
    { title: '前提条件', dataIndex: 'precondition', key: 'precondition', width: 200, ellipsis: true },
    { title: '预期结果', dataIndex: 'expectedResult', key: 'expectedResult', width: 200, ellipsis: true },
    {
      title: '操作', key: 'action', width: 100,
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => onEdit(record)} />
          <Popconfirm title="确认删除?" onConfirm={() => onDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={testCases}
      rowKey="id"
      size="small"
      pagination={{ pageSize: 15, showTotal: (total) => `共 ${total} 条用例` }}
    />
  );
};

export default TestCaseList;
