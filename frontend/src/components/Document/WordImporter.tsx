import React, { useState } from 'react';
import { Upload, message, Progress, Alert } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { requirementApi } from '../../services/api';
import { useAppStore } from '../../stores/appStore';

const { Dragger } = Upload;

const WordImporter: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const setRequirements = useAppStore((s) => s.setRequirements);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setProgress(10);
    setStatusText('上传文档中...');
    try {
      setProgress(30);
      setStatusText('LLM 正在解析需求文档，请稍候...');
      const response = await requirementApi.uploadWord(file);
      setProgress(90);
      if (response.data.success && response.data.data) {
        setRequirements(response.data.data);
        setProgress(100);
        setStatusText(`成功解析 ${response.data.data.length} 条需求`);
        message.success(`成功解析 ${response.data.data.length} 条需求`);
      } else {
        message.error(response.data.error || '解析失败');
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail || error.message || '上传失败';
      message.error(detail);
      setStatusText('');
    } finally {
      setUploading(false);
      setTimeout(() => { setProgress(0); setStatusText(''); }, 2000);
    }
    return false;
  };

  return (
    <div>
      <Alert
        message={'上传前请先在「设置」页面配置大模型 API，解析过程由 LLM 智能识别需求结构'}
        type="info"
        showIcon
        style={{ marginBottom: 12 }}
      />
      <Dragger
        accept=".docx"
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
        <p className="ant-upload-text">点击或拖拽 Word 文档到此处上传</p>
        <p className="ant-upload-hint">支持 .docx 格式，由 AI 智能解析需求</p>
      </Dragger>
      {progress > 0 && (
        <Progress
          percent={progress}
          status={progress === 100 ? 'success' : 'active'}
          format={() => statusText || `${progress}%`}
        />
      )}
    </div>
  );
};

export default WordImporter;
