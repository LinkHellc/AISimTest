import React, { useState, useEffect } from 'react';
import { Select, Button, Tag, Space, message } from 'antd';
import { useAppStore } from '../../stores/appStore';
import { linkApi } from '../../services/api';

interface Props {
  requirementId: string;
}

const SignalLinker: React.FC<Props> = ({ requirementId }) => {
  const signals = useAppStore((s) => s.signals);
  const [linkedIds, setLinkedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchLinks = async () => {
      try {
        const res = await linkApi.getLinks(requirementId);
        if (res.data.success && res.data.data) {
          setLinkedIds(res.data.data.map((l: any) => l.signalId));
        }
      } catch { /* ignore */ }
    };
    fetchLinks();
  }, [requirementId]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await linkApi.createLinks(requirementId, linkedIds);
      message.success('关联保存成功');
    } catch {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Select
        mode="multiple"
        style={{ width: '100%', minWidth: 300 }}
        placeholder="选择关联信号"
        value={linkedIds}
        onChange={setLinkedIds}
        options={signals.map((s) => ({ label: `${s.name} (${s.unit})`, value: s.id }))}
        optionFilterProp="label"
      />
      <Button type="primary" size="small" loading={loading} onClick={handleSave} style={{ marginTop: 8 }}>
        保存关联
      </Button>
      {linkedIds.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <Space wrap>
            {linkedIds.map((id) => {
              const sig = signals.find((s) => s.id === id);
              return sig ? (
                <Tag key={id} closable onClose={() => setLinkedIds(linkedIds.filter((i) => i !== id))}>
                  {sig.name}
                </Tag>
              ) : null;
            })}
          </Space>
        </div>
      )}
    </div>
  );
};

export default SignalLinker;
