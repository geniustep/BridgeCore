import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button,
  Card,
  Descriptions,
  Space,
  Tag,
  Spin,
  Alert,
  Typography,
  Row,
  Col,
  Statistic,
  Tabs,
  message,
  Badge,
  Tooltip,
  Divider,
  Progress,
  Modal,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  UserOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  ApiOutlined,
  ClockCircleOutlined,
  CalendarOutlined,
  SettingOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import { tenantService } from '@/services/tenant.service';
import { Tenant, RateLimitStatus } from '@/types';
import TenantSystemsList from '@/components/Systems/TenantSystemsList';
import AddSystemModal from '@/components/Systems/AddSystemModal';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Title, Text } = Typography;

const TenantDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [testing, setTesting] = useState(false);
  const [addSystemModalVisible, setAddSystemModalVisible] = useState(false);
  const [systemsRefreshKey, setSystemsRefreshKey] = useState(0);
  const [rateLimitStatus, setRateLimitStatus] = useState<RateLimitStatus | null>(null);
  const [rateLimitLoading, setRateLimitLoading] = useState(false);
  const [rateLimitResetting, setRateLimitResetting] = useState(false);

  useEffect(() => {
    if (id) {
      fetchTenant();
      fetchRateLimitStatus();
    }
  }, [id]);

  const fetchTenant = async () => {
    if (!id) return;

    setLoading(true);
    try {
      const data = await tenantService.getTenant(id);
      setTenant(data);
    } catch (error: any) {
      message.error('Failed to load tenant details');
      navigate('/tenants');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!id) return;

    setTesting(true);
    try {
      await tenantService.testConnection(id);
      message.success('Connection test successful!');
      fetchTenant(); // Refresh data
    } catch (error: any) {
      message.error(
        error.response?.data?.detail || 'Connection test failed'
      );
    } finally {
      setTesting(false);
    }
  };

  const fetchRateLimitStatus = async () => {
    if (!id) return;

    setRateLimitLoading(true);
    try {
      const status = await tenantService.getRateLimitStatus(id);
      setRateLimitStatus(status);
    } catch (error: any) {
      console.error('Failed to fetch rate limit status:', error);
    } finally {
      setRateLimitLoading(false);
    }
  };

  const handleResetRateLimit = async (resetType: 'daily' | 'hourly' | 'all') => {
    if (!id) return;

    setRateLimitResetting(true);
    try {
      const result = await tenantService.resetRateLimit(id, resetType);
      message.success(`Rate limit reset successful! Deleted ${result.deleted_keys} key(s)`);
      await fetchRateLimitStatus(); // Refresh status
    } catch (error: any) {
      message.error(
        error.response?.data?.detail || 'Failed to reset rate limit'
      );
    } finally {
      setRateLimitResetting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; text: string }> = {
      active: { color: 'success', text: 'Active' },
      trial: { color: 'processing', text: 'Trial' },
      suspended: { color: 'error', text: 'Suspended' },
      inactive: { color: 'default', text: 'Inactive' },
    };

    const config = statusConfig[status] || statusConfig.inactive;
    return <Badge status={config.color as any} text={config.text} />;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'success',
      trial: 'processing',
      suspended: 'error',
      inactive: 'default',
    };
    return colors[status] || 'default';
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!tenant) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Tenant Not Found"
          description="The requested tenant could not be found."
          type="error"
          showIcon
        />
      </div>
    );
  }

  const tabItems = [
    {
      key: 'overview',
      label: (
        <span>
          <LineChartOutlined /> Overview
        </span>
      ),
      children: (
        <div>
          {/* Statistics Cards */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Status"
                  value={tenant.status.toUpperCase()}
                  valueStyle={{
                    color:
                      tenant.status === 'active'
                        ? '#52c41a'
                        : tenant.status === 'trial'
                        ? '#1890ff'
                        : '#ff4d4f',
                  }}
                  prefix={
                    tenant.status === 'active' ? (
                      <CheckCircleOutlined />
                    ) : (
                      <CloseCircleOutlined />
                    )
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Max Requests/Day"
                  value={tenant.max_requests_per_day || 0}
                  prefix={<ApiOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Max Requests/Hour"
                  value={tenant.max_requests_per_hour || 0}
                  prefix={<ClockCircleOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Last Active"
                  value={
                    tenant.last_active_at
                      ? dayjs(tenant.last_active_at).fromNow()
                      : 'Never'
                  }
                  prefix={<CalendarOutlined />}
                />
              </Card>
            </Col>
          </Row>

          {/* Basic Information */}
          <Card title="Basic Information" style={{ marginBottom: 16 }}>
            <Descriptions bordered column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="Tenant Name">
                <Text strong>{tenant.name}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Slug">
                <Tag color="blue">{tenant.slug}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status" span={2}>
                {getStatusBadge(tenant.status)}
              </Descriptions.Item>
              <Descriptions.Item label="Description" span={2}>
                {tenant.description || <Text type="secondary">N/A</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="Contact Email">
                {tenant.contact_email}
              </Descriptions.Item>
              <Descriptions.Item label="Contact Phone">
                {tenant.contact_phone || <Text type="secondary">N/A</Text>}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Odoo Configuration */}
          <Card
            title={
              <Space>
                <GlobalOutlined />
                Odoo Configuration
              </Space>
            }
            extra={
              <Button
                type="primary"
                size="small"
                icon={<ThunderboltOutlined />}
                onClick={handleTestConnection}
                loading={testing}
              >
                Test Connection
              </Button>
            }
            style={{ marginBottom: 16 }}
          >
            <Descriptions bordered column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="Odoo URL" span={2}>
                <Space>
                  <GlobalOutlined style={{ color: '#1890ff' }} />
                  <a href={tenant.odoo_url} target="_blank" rel="noopener noreferrer">
                    {tenant.odoo_url}
                  </a>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Database">
                <Space>
                  <DatabaseOutlined style={{ color: '#52c41a' }} />
                  <Text code>{tenant.odoo_database}</Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Version">
                {tenant.odoo_version ? (
                  <Tag color="blue">v{tenant.odoo_version}</Tag>
                ) : (
                  <Text type="secondary">N/A</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Username" span={2}>
                <Text code>{tenant.odoo_username}</Text>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Subscription & Limits */}
          <Card
            title={
              <Space>
                <SettingOutlined />
                Subscription & Rate Limits
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            <Descriptions bordered column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="Plan">
                {tenant.plan_id ? (
                  <Tag color="purple">Plan ID: {tenant.plan_id}</Tag>
                ) : (
                  <Text type="secondary">No plan assigned</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Max Requests/Day">
                <Text strong>{tenant.max_requests_per_day?.toLocaleString() || 'Unlimited'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Max Requests/Hour">
                <Text strong>{tenant.max_requests_per_hour?.toLocaleString() || 'Unlimited'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Trial Ends At" span={2}>
                {tenant.trial_ends_at ? (
                  <Space>
                    <CalendarOutlined />
                    <Text>
                      {dayjs(tenant.trial_ends_at).format('YYYY-MM-DD HH:mm')}
                    </Text>
                    <Text type="secondary">
                      ({dayjs(tenant.trial_ends_at).fromNow()})
                    </Text>
                  </Space>
                ) : (
                  <Text type="secondary">N/A</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Subscription Ends At" span={2}>
                {tenant.subscription_ends_at ? (
                  <Space>
                    <CalendarOutlined />
                    <Text>
                      {dayjs(tenant.subscription_ends_at).format('YYYY-MM-DD HH:mm')}
                    </Text>
                    <Text type="secondary">
                      ({dayjs(tenant.subscription_ends_at).fromNow()})
                    </Text>
                  </Space>
                ) : (
                  <Text type="secondary">N/A</Text>
                )}
              </Descriptions.Item>
            </Descriptions>

            {Array.isArray(tenant.allowed_models) && tenant.allowed_models.length > 0 && (
              <>
                <Divider orientation="left">Allowed Models</Divider>
                <Space wrap>
                  {tenant.allowed_models.map((model) => (
                    <Tag key={model} color="geekblue">
                      {model}
                    </Tag>
                  ))}
                </Space>
              </>
            )}

            {Array.isArray(tenant.allowed_features) && tenant.allowed_features.length > 0 && (
              <>
                <Divider orientation="left">Allowed Features</Divider>
                <Space wrap>
                  {tenant.allowed_features.map((feature) => (
                    <Tag key={feature} color="cyan">
                      {feature}
                    </Tag>
                  ))}
                </Space>
              </>
            )}
          </Card>

          {/* Rate Limit Status - Quick View */}
          <Card
            title={
              <Space>
                <ThunderboltOutlined />
                Rate Limit Status
                <Badge 
                  count={rateLimitStatus ? (rateLimitStatus.daily_remaining === 0 || rateLimitStatus.hourly_remaining === 0 ? '!' : null) : null}
                  style={{ backgroundColor: '#ff4d4f' }}
                />
              </Space>
            }
            extra={
              <Space>
                <Button
                  size="small"
                  onClick={fetchRateLimitStatus}
                  loading={rateLimitLoading}
                >
                  Refresh
                </Button>
                <Button
                  size="small"
                  type="primary"
                  danger
                  icon={<ThunderboltOutlined />}
                  onClick={() => {
                    Modal.confirm({
                      title: 'Reset All Rate Limits?',
                      content: 'This will reset both daily and hourly rate limits for this tenant. Continue?',
                      okText: 'Yes, Reset All',
                      okType: 'danger',
                      onOk: () => handleResetRateLimit('all'),
                    });
                  }}
                  loading={rateLimitResetting}
                >
                  Reset All
                </Button>
                <Button
                  size="small"
                  type="link"
                  onClick={() => {
                    const tabs = document.querySelectorAll('.ant-tabs-tab');
                    const rateLimitsTab = Array.from(tabs).find((tab: any) => 
                      tab.textContent?.includes('Rate Limits')
                    ) as HTMLElement;
                    if (rateLimitsTab) {
                      rateLimitsTab.click();
                    }
                  }}
                >
                  View Details
                </Button>
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            {rateLimitLoading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <Spin />
              </div>
            ) : rateLimitStatus ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <Card size="small" bordered={false}>
                    <Statistic
                      title="Daily Requests"
                      value={rateLimitStatus.daily_count}
                      suffix={`/ ${rateLimitStatus.daily_limit.toLocaleString()}`}
                      valueStyle={{
                        color: rateLimitStatus.daily_remaining > 0 ? '#52c41a' : '#ff4d4f'
                      }}
                      prefix={<CalendarOutlined />}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">Remaining: </Text>
                      <Text strong style={{ color: rateLimitStatus.daily_remaining > 0 ? '#52c41a' : '#ff4d4f' }}>
                        {rateLimitStatus.daily_remaining.toLocaleString()}
                      </Text>
                      <Progress
                        percent={Math.min(100, Math.round((rateLimitStatus.daily_count / rateLimitStatus.daily_limit) * 100))}
                        status={rateLimitStatus.daily_remaining > 0 ? 'active' : 'exception'}
                        size="small"
                        style={{ marginTop: 8 }}
                      />
                    </div>
                    <Button
                        type={rateLimitStatus.daily_remaining === 0 ? "primary" : "default"}
                        danger={rateLimitStatus.daily_remaining === 0}
                        size="small"
                        onClick={() => handleResetRateLimit('daily')}
                        loading={rateLimitResetting}
                        style={{ marginTop: 12 }}
                        icon={<ThunderboltOutlined />}
                      >
                        Reset Daily
                      </Button>
                  </Card>
                </Col>
                <Col xs={24} sm={12}>
                  <Card size="small" bordered={false}>
                    <Statistic
                      title="Hourly Requests"
                      value={rateLimitStatus.hourly_count}
                      suffix={`/ ${rateLimitStatus.hourly_limit.toLocaleString()}`}
                      valueStyle={{
                        color: rateLimitStatus.hourly_remaining > 0 ? '#52c41a' : '#ff4d4f'
                      }}
                      prefix={<ClockCircleOutlined />}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">Remaining: </Text>
                      <Text strong style={{ color: rateLimitStatus.hourly_remaining > 0 ? '#52c41a' : '#ff4d4f' }}>
                        {rateLimitStatus.hourly_remaining.toLocaleString()}
                      </Text>
                      <Progress
                        percent={Math.min(100, Math.round((rateLimitStatus.hourly_count / rateLimitStatus.hourly_limit) * 100))}
                        status={rateLimitStatus.hourly_remaining > 0 ? 'active' : 'exception'}
                        size="small"
                        style={{ marginTop: 8 }}
                      />
                    </div>
                    <Button
                        type={rateLimitStatus.hourly_remaining === 0 ? "primary" : "default"}
                        danger={rateLimitStatus.hourly_remaining === 0}
                        size="small"
                        onClick={() => handleResetRateLimit('hourly')}
                        loading={rateLimitResetting}
                        style={{ marginTop: 12 }}
                        icon={<ThunderboltOutlined />}
                      >
                        Reset Hourly
                      </Button>
                  </Card>
                </Col>
              </Row>
            ) : (
              <Alert
                message="Rate limit status not loaded"
                description="Click Refresh to load rate limit information."
                type="info"
                showIcon
                action={
                  <Button size="small" onClick={fetchRateLimitStatus}>
                    Load
                  </Button>
                }
              />
            )}
          </Card>

          {/* Timestamps */}
          <Card title="Timeline" size="small">
            <Descriptions bordered column={{ xs: 1, sm: 3 }} size="small">
              <Descriptions.Item label="Created At">
                <Tooltip title={dayjs(tenant.created_at).format('YYYY-MM-DD HH:mm:ss')}>
                  <Text type="secondary">
                    {dayjs(tenant.created_at).fromNow()}
                  </Text>
                </Tooltip>
              </Descriptions.Item>
              <Descriptions.Item label="Updated At">
                <Tooltip title={dayjs(tenant.updated_at).format('YYYY-MM-DD HH:mm:ss')}>
                  <Text type="secondary">
                    {dayjs(tenant.updated_at).fromNow()}
                  </Text>
                </Tooltip>
              </Descriptions.Item>
              <Descriptions.Item label="Last Active">
                {tenant.last_active_at ? (
                  <Tooltip
                    title={dayjs(tenant.last_active_at).format('YYYY-MM-DD HH:mm:ss')}
                  >
                    <Text type="secondary">
                      {dayjs(tenant.last_active_at).fromNow()}
                    </Text>
                  </Tooltip>
                ) : (
                  <Text type="secondary">Never</Text>
                )}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Quick Actions for External Systems */}
          <Card
            title={
              <Space>
                <ApiOutlined />
                Quick Connect External Systems
              </Space>
            }
            style={{ marginTop: 16 }}
          >
            <Space wrap size="large">
              <Button
                type="primary"
                size="large"
                icon={<ApiOutlined />}
                onClick={() => setAddSystemModalVisible(true)}
                style={{ 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  minWidth: 160
                }}
              >
                🎓 Add Moodle
              </Button>
              <Button
                size="large"
                icon={<ApiOutlined />}
                onClick={() => setAddSystemModalVisible(true)}
                style={{ minWidth: 160 }}
              >
                💼 Add SAP
              </Button>
              <Button
                size="large"
                icon={<ApiOutlined />}
                onClick={() => setAddSystemModalVisible(true)}
                style={{ minWidth: 160 }}
              >
                ☁️ Add Salesforce
              </Button>
            </Space>
            <Divider style={{ margin: '16px 0' }} />
            <Text type="secondary">
              Connect external systems to enable seamless data integration and synchronization.
              Already using Odoo by default.
            </Text>
          </Card>
        </div>
      ),
    },
    {
      key: 'systems',
      label: (
        <span>
          <ApiOutlined /> External Systems
        </span>
      ),
      children: <TenantSystemsList key={systemsRefreshKey} tenantId={id!} />,
    },
    {
      key: 'rate-limits',
      label: (
        <span>
          <ThunderboltOutlined /> Rate Limits
        </span>
      ),
      children: (
        <div>
          <Card
            title={
              <Space>
                <ThunderboltOutlined />
                Rate Limit Status & Management
              </Space>
            }
            extra={
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={fetchRateLimitStatus}
                loading={rateLimitLoading}
              >
                Refresh Status
              </Button>
            }
            style={{ marginBottom: 16 }}
          >
            {rateLimitLoading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">Loading rate limit status...</Text>
                </div>
              </div>
            ) : rateLimitStatus ? (
              <>
                <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                  <Col xs={24} sm={12}>
                    <Card 
                      size="small" 
                      style={{ 
                        background: rateLimitStatus.daily_remaining > 0 ? '#f6ffed' : '#fff1f0',
                        border: `2px solid ${rateLimitStatus.daily_remaining > 0 ? '#b7eb8f' : '#ffccc7'}`
                      }}
                    >
                      <Statistic
                        title="Daily Requests"
                        value={rateLimitStatus.daily_count}
                        suffix={`/ ${rateLimitStatus.daily_limit.toLocaleString()}`}
                        valueStyle={{
                          color: rateLimitStatus.daily_remaining > 0 ? '#52c41a' : '#ff4d4f',
                          fontSize: '24px'
                        }}
                        prefix={<CalendarOutlined />}
                      />
                      <div style={{ marginTop: 12 }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div>
                            <Text type="secondary">Remaining: </Text>
                            <Text strong style={{ fontSize: '16px', color: rateLimitStatus.daily_remaining > 0 ? '#52c41a' : '#ff4d4f' }}>
                              {rateLimitStatus.daily_remaining.toLocaleString()}
                            </Text>
                          </div>
                          <Progress
                            percent={Math.min(100, Math.round((rateLimitStatus.daily_count / rateLimitStatus.daily_limit) * 100))}
                            status={rateLimitStatus.daily_remaining > 0 ? 'active' : 'exception'}
                            strokeColor={rateLimitStatus.daily_remaining > 0 ? '#52c41a' : '#ff4d4f'}
                          />
                        </Space>
                      </div>
                    </Card>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Card 
                      size="small" 
                      style={{ 
                        background: rateLimitStatus.hourly_remaining > 0 ? '#f6ffed' : '#fff1f0',
                        border: `2px solid ${rateLimitStatus.hourly_remaining > 0 ? '#b7eb8f' : '#ffccc7'}`
                      }}
                    >
                      <Statistic
                        title="Hourly Requests"
                        value={rateLimitStatus.hourly_count}
                        suffix={`/ ${rateLimitStatus.hourly_limit.toLocaleString()}`}
                        valueStyle={{
                          color: rateLimitStatus.hourly_remaining > 0 ? '#52c41a' : '#ff4d4f',
                          fontSize: '24px'
                        }}
                        prefix={<ClockCircleOutlined />}
                      />
                      <div style={{ marginTop: 12 }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div>
                            <Text type="secondary">Remaining: </Text>
                            <Text strong style={{ fontSize: '16px', color: rateLimitStatus.hourly_remaining > 0 ? '#52c41a' : '#ff4d4f' }}>
                              {rateLimitStatus.hourly_remaining.toLocaleString()}
                            </Text>
                          </div>
                          <Progress
                            percent={Math.min(100, Math.round((rateLimitStatus.hourly_count / rateLimitStatus.hourly_limit) * 100))}
                            status={rateLimitStatus.hourly_remaining > 0 ? 'active' : 'exception'}
                            strokeColor={rateLimitStatus.hourly_remaining > 0 ? '#52c41a' : '#ff4d4f'}
                          />
                        </Space>
                      </div>
                    </Card>
                  </Col>
                </Row>

                <Card 
                  title="Reset Rate Limits"
                  style={{ background: '#fafafa' }}
                >
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <Alert
                      message="Rate Limit Management"
                      description="Use the buttons below to reset rate limit counters. This will allow the tenant to make requests again immediately."
                      type="info"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                    <Space wrap size="large">
                      <Button
                        type="default"
                        size="large"
                        onClick={() => handleResetRateLimit('daily')}
                        loading={rateLimitResetting}
                        danger={rateLimitStatus.daily_remaining === 0}
                        icon={<CalendarOutlined />}
                      >
                        Reset Daily Limit
                      </Button>
                      <Button
                        type="default"
                        size="large"
                        onClick={() => handleResetRateLimit('hourly')}
                        loading={rateLimitResetting}
                        danger={rateLimitStatus.hourly_remaining === 0}
                        icon={<ClockCircleOutlined />}
                      >
                        Reset Hourly Limit
                      </Button>
                      <Button
                        type="primary"
                        size="large"
                        danger
                        onClick={() => {
                          Modal.confirm({
                            title: 'Reset All Rate Limits?',
                            content: 'This will reset both daily and hourly rate limits for this tenant. Are you sure?',
                            okText: 'Yes, Reset All',
                            cancelText: 'Cancel',
                            okType: 'danger',
                            onOk: () => handleResetRateLimit('all'),
                          });
                        }}
                        loading={rateLimitResetting}
                        icon={<ThunderboltOutlined />}
                      >
                        Reset All Limits
                      </Button>
                    </Space>
                  </Space>
                </Card>
              </>
            ) : (
              <Alert
                message="Rate Limit Status Not Available"
                description="Unable to load rate limit status. Please check the connection and try again."
                type="warning"
                showIcon
                action={
                  <Button size="small" onClick={fetchRateLimitStatus}>
                    Retry
                  </Button>
                }
              />
            )}
          </Card>
        </div>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header with Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <Space direction="vertical" size={0}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/tenants')}
            style={{ padding: 0, marginBottom: 8 }}
          >
            Back to Tenants
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            {tenant.name}
          </Title>
          <Space>
            <Tag color={getStatusColor(tenant.status)}>
              {tenant.status.toUpperCase()}
            </Tag>
            <Text type="secondary">{tenant.slug}</Text>
          </Space>
        </Space>

        <Space wrap>
          <Button
            type="default"
            icon={<UserOutlined />}
            onClick={() => navigate(`/tenants/${id}/users`)}
          >
            Manage Users
          </Button>
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/tenants/${id}/edit`)}
          >
            Edit Tenant
          </Button>
        </Space>
      </div>

      {/* Tabs for different sections */}
      <Tabs defaultActiveKey="overview" items={tabItems} />

      {/* Add System Modal */}
      <AddSystemModal
        visible={addSystemModalVisible}
        tenantId={id!}
        onCancel={() => setAddSystemModalVisible(false)}
        onSuccess={() => {
          setAddSystemModalVisible(false);
          setSystemsRefreshKey(prev => prev + 1); // Refresh systems list
          message.success('System added successfully!');
        }}
      />
    </div>
  );
};

export default TenantDetailsPage;

