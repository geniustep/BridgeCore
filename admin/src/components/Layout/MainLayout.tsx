import React, { useState } from 'react';
import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const { Content } = Layout;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar collapsed={collapsed} />
      <Layout>
        <Header collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
