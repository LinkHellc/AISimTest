import React, { useState } from 'react';
import { Upload, message, Alert } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { signalLibraryApi } from '../../services/api';

const { Dragger } = Upload;

interface SignalLibraryImporterProps {
  onSuccess?: (result: { added: number; updated: number; total: number }) => void;
}

const SignalLibraryImporter: React.FC<SignalLibraryImporterProps> = ({ onSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ added: number; updated: number; total: number } | null>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setResult(null);
    try {
      const response = await signalLibraryApi.upload(file);
      if (response.data.success && response.data.data) {
        setResult(response.data.data);
        message.success(`成功导入 ${response.data.data.total} 个信号定义`);
        onSuccess?.(response.data.data);
      } else {
        message.error(response.data.error || '导入失败');
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail || error.message || '上传失败';
      message.error(detail);
    } finally {
      setUploading(false);
    }
    return false;
  };

  return (
    <div>
      <Dragger
        accept=".xlsx,.xls"
        showUploadList={false}
        beforeUpload={(file) => {
          handleUpload(file as unknown as File);
          return false;
        }}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽接口表 Excel 到此处</p>
        <p className="ant-upload-hint">支持 .xlsx / .xls 格式，将从 Input/Mea/Output 工作表提取信号定义</p>
      </Dragger>
      {result && (
        <Alert
          type="success"
          message={`导入完成：新增 ${result.added} 个，更新 ${result.updated} 个信号`}
          style={{ marginTop: 16 }}
          showIcon
        />
      )}
    </div>
  );
};

export default SignalLibraryImporter;
