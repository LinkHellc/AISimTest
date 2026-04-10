import React, { useMemo } from 'react';
import { Tree, Checkbox, Space, Typography } from 'antd';
import type { TreeDataNode } from 'antd';
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

  const treeData = useMemo(() => {
    const map = new Map<string, TreeDataNode>();
    const roots: TreeDataNode[] = [];

    requirements.forEach((req) => {
      map.set(req.id, {
        key: req.id,
        title: (
          <span>
            <Text type="secondary">[{req.id}]</Text> {req.title}
          </span>
        ),
        children: [],
      });
    });

    requirements.forEach((req) => {
      const node = map.get(req.id)!;
      if (req.parentId && map.has(req.parentId)) {
        map.get(req.parentId)!.children!.push(node);
      } else {
        roots.push(node);
      }
    });

    return roots;
  }, [requirements]);

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
      <Tree
        defaultExpandAll
        checkable
        checkedKeys={selectedRequirementIds}
        onCheck={(checked) => {
          const keys = Array.isArray(checked) ? checked : checked.checked;
          useAppStore.setState({ selectedRequirementIds: keys as string[] });
        }}
        onSelect={(selectedKeys) => {
          if (onSelect) {
            const key = selectedKeys.length > 0 ? (selectedKeys[0] as string) : null;
            onSelect(key);
          }
        }}
        treeData={treeData}
        style={{ marginTop: 8 }}
      />
    </div>
  );
};

export default RequirementTree;
