import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Spin, Alert } from 'antd';
import {
  TeamOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  StopOutlined,
  ApiOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import { analyticsService } from '@/services/analytics.service';
import { SystemOverview } from '@/types';
import { useTenantStore } from '@/store/tenant.store';

const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { statistics, fetchStatistics } = useTenantStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [overviewData] = await Promise.all([
        analyticsService.getOverview(),
        fetchStatistics(),
      ]);
      setOverview(overviewData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return <Alert message="Error" description={error} type="error" showIcon />;
  }

  return (
    <div>
      <h1>Dashboard Overview</h1>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Tenants"
              value={statistics?.total || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Tenants"
              value={statistics?.active || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Trial Tenants"
              value={statistics?.trial || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Suspended"
              value={statistics?.suspended || 0}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <h2 style={{ marginTop: 32 }}>Last 24 Hours</h2>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Total Requests"
              value={overview?.usage_24h.total_requests || 0}
              prefix={<ApiOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Success Rate"
              value={overview?.usage_24h.success_rate_percent || 0}
              suffix="%"
              precision={2}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={overview?.usage_24h.avg_response_time_ms || 0}
              suffix="ms"
              precision={0}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;
