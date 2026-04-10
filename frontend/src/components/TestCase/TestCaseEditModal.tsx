import React, { useEffect } from 'react';
import { Modal, Form, Input, Select } from 'antd';
import type { TestCase } from '../../types';

interface Props {
  visible: boolean;
  testCase: TestCase | null;
  onSave: (id: string, data: Partial<TestCase>) => void;
  onCancel: () => void;
}

const TestCaseEditModal: React.FC<Props> = ({ visible, testCase, onSave, onCancel }) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (testCase) {
      form.setFieldsValue({
        name: testCase.name,
        precondition: testCase.precondition,
        steps: testCase.steps.join('\n'),
        expectedResult: testCase.expectedResult,
        category: testCase.category,
      });
    }
  }, [testCase, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (testCase) {
        onSave(testCase.id, {
          name: values.name,
          precondition: values.precondition,
          steps: values.steps.split('\n').filter((s: string) => s.trim()),
          expectedResult: values.expectedResult,
          category: values.category,
        });
      }
    } catch { /* validation error */ }
  };

  return (
    <Modal title="编辑测试用例" open={visible} onOk={handleSave} onCancel={onCancel} width={640}>
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="用例名称" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="category" label="类型">
          <Select options={[
            { value: 'positive', label: '正例' },
            { value: 'negative', label: '反例' },
          ]} />
        </Form.Item>
        <Form.Item name="precondition" label="前提条件">
          <Input.TextArea rows={2} />
        </Form.Item>
        <Form.Item name="steps" label="测试步骤（每行一步）">
          <Input.TextArea rows={5} />
        </Form.Item>
        <Form.Item name="expectedResult" label="预期结果">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default TestCaseEditModal;
