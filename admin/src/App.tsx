import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { useAuthStore } from './store/auth.store';

// Pages
import LoginPage from './pages/Auth/LoginPage';
import DashboardPage from './pages/Dashboard/DashboardPage';
import TenantsListPage from './pages/Tenants/TenantsListPage';
import CreateTenantPage from './pages/Tenants/CreateTenantPage';
import EditTenantPage from './pages/Tenants/EditTenantPage';
import TenantUsersPage from './pages/Tenants/TenantUsersPage';
import AnalyticsPage from './pages/Analytics/AnalyticsPage';
import UsageLogsPage from './pages/Logs/UsageLogsPage';
import ErrorLogsPage from './pages/Logs/ErrorLogsPage';

// Layout
import MainLayout from './components/Layout/MainLayout';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  // Use relative path since basename is /admin
  return isAuthenticated ? <>{children}</> : <Navigate to="login" replace />;
};

const App: React.FC = () => {
  const { loadAdmin, isAuthenticated } = useAuthStore();

  useEffect(() => {
    loadAdmin();
  }, []);

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#667eea',
          borderRadius: 6,
        },
      }}
    >
      <BrowserRouter basename="/admin">
        <Routes>
          {/* Public Routes */}
          <Route
            path="login"
            element={
              isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
            }
          />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="tenants" element={<TenantsListPage />} />
            <Route path="tenants/create" element={<CreateTenantPage />} />
            <Route path="tenants/:id/edit" element={<EditTenantPage />} />
            <Route path="tenants/:tenantId/users" element={<TenantUsersPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="logs/usage" element={<UsageLogsPage />} />
            <Route path="logs/errors" element={<ErrorLogsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
