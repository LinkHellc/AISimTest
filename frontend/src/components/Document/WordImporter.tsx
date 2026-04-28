import React, { useRef, useEffect } from 'react';
import { Upload, message, Progress, Alert, Card, Timeline, Typography, Space, Button } from 'antd';
import { InboxOutlined, CheckCircleOutlined, LoadingOutlined, ClearOutlined } from '@ant-design/icons';
import { requirementApi } from '../../services/api';
import { useAppStore } from '../../stores/appStore';

const { Dragger } = Upload;
const { Text } = Typography;

const WordImporter: React.FC = () => {
  const uploadProgress = useAppStore((s) => s.uploadProgress);
  const setUploadProgress = useAppStore((s) => s.setUploadProgress);
  const setRequirements = useAppStore((s) => s.setRequirements);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const handleUpload = async (file: File) => {
    setUploadProgress({
      uploading: true,
      progress: 5,
      statusText: '准备上传...',
      clearLogs: true,
      log: `开始上传文件: ${file.name}`,
    });

    try {
      setUploadProgress({ progress: 15, statusText: '上传文档中...', log: '文档上传中...' });
      const response = await requirementApi.uploadWord(file);

      if (response.data.success && response.data.data) {
        setUploadProgress({
          progress: 100,
          statusText: `成功解析 ${response.data.data.length} 条需求`,
          log: `解析完成！共 ${response.data.data.length} 条需求`,
        });
        setRequirements(response.data.data);
        setTimeout(() => setUploadProgress({ uploading: false, progress: 0, statusText: '', log: '' }), 3000);
        if (mountedRef.current) {
          message.success(`成功解析 ${response.data.data.length} 条需求`);
        }
      } else {
        setUploadProgress({
          uploading: false,
          progress: 0,
          statusText: '',
          log: `解析失败: ${response.data.error || '未知错误'}`,
        });
        if (mountedRef.current) {
          message.error(response.data.error || '解析失败');
        }
      }
    } catch (error: any) {
      setUploadProgress({
        uploading: false,
        progress: 0,
        statusText: '',
        log: `错误: ${error.response?.data?.detail || error.message || '上传失败'}`,
      });
      if (mountedRef.current) {
        message.error(error.response?.data?.detail || error.message || '上传失败');
      }
    }
    return false;
  };

  const isUploading = uploadProgress.uploading;
  const hasLogs = uploadProgress.logs.length > 0;

  return (
    <div>
      <Alert
        message={'上传前请先在「设置」页面配置大模型 API，解析过程由 LLM 智能识别需求结构'}
        type="info"
        showIcon
        style={{ marginBottom: 12 }}
      />

      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Dragger
          accept=".docx"
          showUploadList={false}
          beforeUpload={(file) => {
            handleUpload(file as unknown as File);
            return false;
          }}
          disabled={isUploading}
        >
          <p className="ant-upload-drag-icon">
            {isUploading ? <LoadingOutlined /> : <InboxOutlined />}
          </p>
          <p className="ant-upload-text">
            {isUploading ? '解析中...' : '点击或拖拽 Word 文档到此处上传'}
          </p>
          <p className="ant-upload-hint">支持 .docx 格式，由 AI 智能解析需求</p>
        </Dragger>

        {hasLogs && (
          <Card
            size="small"
            title="解析日志"
            extra={
              <Button
                type="text"
                size="small"
                icon={<ClearOutlined />}
                onClick={() => setUploadProgress({ clearLogs: true, progress: 0, statusText: '' })}
              >
                清除
              </Button>
            }
            style={{ background: '#fafafa' }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {isUploading && (
                <Progress
                  percent={uploadProgress.progress}
                  status={uploadProgress.progress === 100 ? 'success' : 'active'}
                  size="small"
                />
              )}
              <Text type="secondary" style={{ fontSize: 12 }}>
                {uploadProgress.statusText}
              </Text>
              <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                <Timeline style={{ margin: 0 }}>
                  {uploadProgress.logs.map((log, idx) => (
                    <Timeline.Item
                      key={idx}
                      dot={idx === uploadProgress.logs.length - 1 && isUploading ?
                        <LoadingOutlined style={{ color: '#1890ff' }} /> :
                        idx === uploadProgress.logs.length - 1 && uploadProgress.progress === 100 ?
                        <CheckCircleOutlined style={{ color: '#52c41a' }} /> : null}
                    >
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        [{log.time}]
                      </Text>{' '}
                      <Text style={{ fontSize: 12 }}>{log.text}</Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </div>
            </Space>
          </Card>
        )}
      </Space>
    </div>
  );
};

export default WordImporter;
