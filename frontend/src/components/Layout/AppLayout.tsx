import React, { useState } from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  FileTextOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import './AppLayout.css';

const { Header, Sider, Content } = Layout;

const menuItems = [
  {
    key: '/requirements',
    icon: <FileTextOutlined />,
    label: '需求导入',
  },
  {
    key: '/requirements/list',
    icon: <FileTextOutlined />,
    label: '需求管理',
  },
  {
    key: '/signals',
    icon: <ApiOutlined />,
    label: '信号管理',
  },
  {
    key: '/testcases',
    icon: <ThunderboltOutlined />,
    label: '用例生成',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '设置',
  },
];

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();

  return (
    <Layout className="app-layout">
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        className="app-sider"
        theme="light"
      >
        <div className="app-logo">
          <ThunderboltOutlined style={{ fontSize: 24, color: token.colorPrimary }} />
          {!collapsed && <span className="app-logo-text">AISimTest</span>}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <span className="app-header-title">
            汽车空调热管理测试用例生成器
          </span>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
