import React, { useState } from 'react';
import { Upload, message, Progress } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { signalApi } from '../../services/api';
import { useAppStore } from '../../stores/appStore';

const { Dragger } = Upload;

const SignalImporter: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const setSignals = useAppStore((s) => s.setSignals);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setProgress(30);
    try {
      const response = await signalApi.uploadExcel(file);
      setProgress(80);
      if (response.data.success && response.data.data) {
        setSignals(response.data.data);
        setProgress(100);
        message.success(`成功导入 ${response.data.data.length} 个信号`);
      } else {
        message.error(response.data.error || '导入失败');
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail || error.message || '上传失败';
      message.error(detail);
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 1000);
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
        <p className="ant-upload-text">点击或拖拽 Excel 信号矩阵到此处</p>
        <p className="ant-upload-hint">支持 .xlsx / .xls 格式</p>
      </Dragger>
      {progress > 0 && (
        <Progress percent={progress} status={progress === 100 ? 'success' : 'active'} />
      )}
    </div>
  );
};

export default SignalImporter;
