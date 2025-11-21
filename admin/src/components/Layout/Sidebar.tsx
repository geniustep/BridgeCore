import React from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  BarChartOutlined,
  FileTextOutlined,
  ApiOutlined,
  BugOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { APP_NAME } from '@/config/api';

const { Sider } = Layout;

interface SidebarProps {
  collapsed: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: 'tenants-group',
      icon: <TeamOutlined />,
      label: 'Tenants',
      children: [
        {
          key: '/tenants',
          label: 'All Tenants',
        },
        {
          key: '/tenants/create',
          icon: <PlusOutlined />,
          label: 'Create Tenant',
        },
      ],
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: 'Analytics',
    },
    {
      key: 'logs-group',
      icon: <FileTextOutlined />,
      label: 'Logs',
      children: [
        {
          key: '/logs/usage',
          icon: <ApiOutlined />,
          label: 'Usage Logs',
        },
        {
          key: '/logs/errors',
          icon: <BugOutlined />,
          label: 'Error Logs',
        },
      ],
    },
  ];

  return (
    <Sider trigger={null} collapsible collapsed={collapsed}>
      <div style={{
        height: 64,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize: collapsed ? 16 : 20,
        fontWeight: 'bold',
      }}>
        {collapsed ? 'BC' : APP_NAME}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  );
};

export default Sidebar;
