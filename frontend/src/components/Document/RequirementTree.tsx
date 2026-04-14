import React from 'react';
import { Checkbox, Space, Typography, List } from 'antd';
import { useAppStore } from '../../stores/appStore';

const { Text } = Typography;

interface RequirementTreeProps {
  onSelect?: (id: string | null) => void;
}

const RequirementTree: React.FC<RequirementTreeProps> = ({ onSelect }) => {
  const requirements = useAppStore((s) => s.requirements);
  const selectedRequirementIds = useAppStore((s) => s.selectedRequirementIds);
  const selectAllRequirements = useAppStore((s) => s.selectAllRequirements);
  const clearRequirementSelection = useAppStore((s) => s.clearRequirementSelection);

  if (requirements.length === 0) {
    return null;
  }

  const allSelected = selectedRequirementIds.length === requirements.length;

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Space>
          <Checkbox
            checked={allSelected}
            indeterminate={selectedRequirementIds.length > 0 && !allSelected}
            onChange={(e) => e.target.checked ? selectAllRequirements() : clearRequirementSelection()}
          >
            全选 ({selectedRequirementIds.length}/{requirements.length})
          </Checkbox>
        </Space>
      </div>
      <List
        size="small"
        dataSource={requirements}
        rowKey="id"
        renderItem={(req) => {
          const isSelected = selectedRequirementIds.includes(req.id);
          return (
            <List.Item
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                background: isSelected ? '#e6f4ff' : 'transparent',
                borderLeft: isSelected ? '3px solid #1677ff' : '3px solid transparent',
              }}
              onClick={() => {
                useAppStore.setState({
                  selectedRequirementIds: isSelected
                    ? selectedRequirementIds.filter((id) => id !== req.id)
                    : [...selectedRequirementIds, req.id],
                });
                if (onSelect) onSelect(req.id);
              }}
            >
              <Text type="secondary" style={{ marginRight: 8 }}>[{req.id}]</Text>
              <Text>{req.title}</Text>
            </List.Item>
          );
        }}
      />
    </div>
  );
};

export default RequirementTree;
