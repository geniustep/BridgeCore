import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Select,
  Space,
  Table,
  Tag,
  Spin,
  message,
} from 'antd';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  RiseOutlined,
  FallOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { analyticsService } from '@/services/analytics.service';

const { Option } = Select;

const AnalyticsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<any>(null);
  const [topTenants, setTopTenants] = useState<any[]>([]);
  const [selectedDays, setSelectedDays] = useState(7);

  useEffect(() => {
    fetchData();
  }, [selectedDays]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewData, topTenantsData] = await Promise.all([
        analyticsService.getOverview(),
        analyticsService.getTopTenants({ limit: 10, days: selectedDays }),
      ]);
      setOverview(overviewData);
      setTopTenants(topTenantsData);
    } catch (error: any) {
      message.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  // Mock data for charts (replace with real data from API)
  const requestsOverTimeData = [
    { date: '2024-01-15', requests: 4200, errors: 120 },
    { date: '2024-01-16', requests: 5100, errors: 95 },
    { date: '2024-01-17', requests: 4800, errors: 140 },
    { date: '2024-01-18', requests: 6200, errors: 110 },
    { date: '2024-01-19', requests: 5900, errors: 88 },
    { date: '2024-01-20', requests: 7100, errors: 102 },
    { date: '2024-01-21', requests: 6500, errors: 95 },
  ];

  const responseTimeData = [
    { hour: '00:00', avgTime: 245 },
    { hour: '04:00', avgTime: 198 },
    { hour: '08:00', avgTime: 312 },
    { hour: '12:00', avgTime: 450 },
    { hour: '16:00', avgTime: 389 },
    { hour: '20:00', avgTime: 267 },
    { hour: '23:00', avgTime: 221 },
  ];

  const statusCodeData = [
    { name: '2xx Success', value: 8547, color: '#52c41a' },
    { name: '4xx Client Error', value: 342, color: '#faad14' },
    { name: '5xx Server Error', value: 89, color: '#f5222d' },
  ];

  const endpointData = [
    {
      endpoint: '/api/v1/odoo/execute',
      requests: 3245,
      avgTime: 324,
      errorRate: 2.1,
    },
    {
      endpoint: '/api/v1/odoo/search_read',
      requests: 2890,
      avgTime: 289,
      errorRate: 1.5,
    },
    {
      endpoint: '/api/v1/sync/trigger',
      requests: 1567,
      avgTime: 456,
      errorRate: 3.2,
    },
    {
      endpoint: '/api/v1/odoo/write',
      requests: 1234,
      avgTime: 398,
      errorRate: 2.8,
    },
    {
      endpoint: '/api/v1/webhooks/receive',
      requests: 987,
      avgTime: 178,
      errorRate: 0.9,
    },
  ];

  const topTenantsColumns = [
    {
      title: 'Tenant',
      dataIndex: 'tenant_name',
      key: 'tenant_name',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Total Requests',
      dataIndex: 'total_requests',
      key: 'total_requests',
      render: (value: number) => value.toLocaleString(),
      sorter: (a: any, b: any) => a.total_requests - b.total_requests,
    },
    {
      title: 'Avg Response Time',
      dataIndex: 'avg_response_time',
      key: 'avg_response_time',
      render: (value: number) => `${value}ms`,
    },
    {
      title: 'Success Rate',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (value: number) => (
        <Tag color={value > 95 ? 'green' : value > 90 ? 'orange' : 'red'}>
          {value.toFixed(1)}%
        </Tag>
      ),
    },
    {
      title: 'Error Count',
      dataIndex: 'error_count',
      key: 'error_count',
      render: (value: number) => (
        <span style={{ color: value > 100 ? '#f5222d' : '#52c41a' }}>
          {value}
        </span>
      ),
    },
  ];

  const endpointColumns = [
    {
      title: 'Endpoint',
      dataIndex: 'endpoint',
      key: 'endpoint',
      render: (text: string) => (
        <code style={{ fontSize: '12px' }}>{text}</code>
      ),
    },
    {
      title: 'Requests',
      dataIndex: 'requests',
      key: 'requests',
      render: (value: number) => value.toLocaleString(),
      sorter: (a: any, b: any) => a.requests - b.requests,
    },
    {
      title: 'Avg Time',
      dataIndex: 'avgTime',
      key: 'avgTime',
      render: (value: number) => `${value}ms`,
    },
    {
      title: 'Error Rate',
      dataIndex: 'errorRate',
      key: 'errorRate',
      render: (value: number) => (
        <Tag color={value < 2 ? 'green' : value < 5 ? 'orange' : 'red'}>
          {value.toFixed(1)}%
        </Tag>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
        }}
      >
        <h1 style={{ margin: 0 }}>Analytics Dashboard</h1>
        <Space>
          <Select
            value={selectedDays}
            onChange={setSelectedDays}
            style={{ width: 150 }}
          >
            <Option value={1}>Last 24 hours</Option>
            <Option value={7}>Last 7 days</Option>
            <Option value={30}>Last 30 days</Option>
            <Option value={90}>Last 90 days</Option>
          </Select>
        </Space>
      </div>

      {/* Overview Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Requests"
              value={overview?.total_requests || 0}
              precision={0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<RiseOutlined />}
              suffix={
                <span style={{ fontSize: '14px', color: '#888' }}>
                  +12.5%
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={overview?.avg_response_time || 0}
              precision={0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ThunderboltOutlined />}
              suffix="ms"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={overview?.success_rate || 0}
              precision={1}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Errors"
              value={overview?.total_errors || 0}
              precision={0}
              valueStyle={{ color: '#cf1322' }}
              prefix={<FallOutlined />}
              suffix={
                <span style={{ fontSize: '14px', color: '#888' }}>
                  -5.2%
                </span>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* Requests Over Time Chart */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Requests Over Time">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={requestsOverTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="#1890ff"
                  strokeWidth={2}
                  name="Total Requests"
                />
                <Line
                  type="monotone"
                  dataKey="errors"
                  stroke="#f5222d"
                  strokeWidth={2}
                  name="Errors"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Status Code Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusCodeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusCodeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Response Time Chart */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24}>
          <Card title="Average Response Time by Hour">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={responseTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="avgTime"
                  fill="#52c41a"
                  name="Avg Response Time (ms)"
                />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Top Tenants Table */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24}>
          <Card title="Top Tenants by Activity">
            <Table
              columns={topTenantsColumns}
              dataSource={topTenants}
              rowKey="tenant_id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Top Endpoints Table */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="Top API Endpoints">
            <Table
              columns={endpointColumns}
              dataSource={endpointData}
              rowKey="endpoint"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AnalyticsPage;
