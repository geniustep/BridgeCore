import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Select,
  Space,
  Tag,
  Button,
  Row,
  Col,
  message,
  Badge,
  Statistic,
  Tooltip,
  Modal,
  Switch,
  Typography,
} from 'antd';
import {
  ReloadOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  BellOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { alertService } from '@/services/alert.service';
import { useTenantStore } from '@/store/tenant.store';
import { Alert, AlertCounts, AlertSeverity, AlertStatusType } from '@/types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Option } = Select;
const { Text } = Typography;

const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [counts, setCounts] = useState<AlertCounts | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  
  const [filters, setFilters] = useState({
    tenant_id: undefined as string | undefined,
    status: undefined as AlertStatusType | undefined,
    severity: undefined as AlertSeverity | undefined,
    active_only: true,
  });

  const { tenants, fetchTenants } = useTenantStore();

  useEffect(() => {
    fetchTenants();
    fetchAlerts();
    fetchCounts();
  }, []);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const data = await alertService.getAlerts({
        ...filters,
        limit: 100,
      });
      setAlerts(data);
    } catch (error) {
      message.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const fetchCounts = async () => {
    try {
      const data = await alertService.getAlertCounts();
      setCounts(data);
    } catch (error) {
      console.error('Failed to fetch counts:', error);
    }
  };

  const handleAcknowledge = async (alertId: number) => {
    try {
      await alertService.acknowledgeAlert(alertId);
      message.success('Alert acknowledged');
      fetchAlerts();
      fetchCounts();
    } catch (error) {
      message.error('Failed to acknowledge alert');
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      await alertService.resolveAlert(alertId);
      message.success('Alert resolved');
      fetchAlerts();
      fetchCounts();
    } catch (error) {
      message.error('Failed to resolve alert');
    }
  };

  const handleDismiss = async (alertId: number) => {
    try {
      await alertService.dismissAlert(alertId);
      message.success('Alert dismissed');
      fetchAlerts();
      fetchCounts();
    } catch (error) {
      message.error('Failed to dismiss alert');
    }
  };

  const handleBulkDismiss = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select alerts to dismiss');
      return;
    }

    Modal.confirm({
      title: 'Dismiss Selected Alerts?',
      content: `Are you sure you want to dismiss ${selectedRowKeys.length} alert(s)?`,
      okText: 'Dismiss All',
      okType: 'danger',
      onOk: async () => {
        try {
          await alertService.bulkDismissAlerts(selectedRowKeys);
          message.success(`Dismissed ${selectedRowKeys.length} alerts`);
          setSelectedRowKeys([]);
          fetchAlerts();
          fetchCounts();
        } catch (error) {
          message.error('Failed to dismiss alerts');
        }
      },
    });
  };

  const getSeverityConfig = (severity: AlertSeverity) => {
    const configs = {
      critical: { color: '#ff4d4f', bg: '#fff2f0', icon: <ExclamationCircleOutlined /> },
      error: { color: '#ff7a45', bg: '#fff7e6', icon: <ExclamationCircleOutlined /> },
      warning: { color: '#faad14', bg: '#fffbe6', icon: <WarningOutlined /> },
      info: { color: '#1890ff', bg: '#e6f7ff', icon: <InfoCircleOutlined /> },
    };
    return configs[severity] || configs.info;
  };

  const getStatusConfig = (status: AlertStatusType) => {
    const configs = {
      active: { color: 'red', text: 'Active' },
      acknowledged: { color: 'orange', text: 'Acknowledged' },
      resolved: { color: 'green', text: 'Resolved' },
      dismissed: { color: 'default', text: 'Dismissed' },
    };
    return configs[status] || configs.active;
  };

  const columns = [
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: AlertSeverity) => {
        const safeSeverity = severity || 'info';
        const config = getSeverityConfig(safeSeverity);
        return (
          <Tag color={config.color} icon={config.icon}>
            {safeSeverity.toUpperCase()}
          </Tag>
        );
      },
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title: string, record: Alert) => (
        <Tooltip title={record.message}>
          <span style={{ fontWeight: record.status === 'active' ? 600 : 400 }}>
            {title}
          </span>
        </Tooltip>
      ),
    },
    {
      title: 'Tenant',
      dataIndex: 'tenant_id',
      key: 'tenant_id',
      width: 150,
      render: (tenantId: string) => {
        if (!tenantId) return <Text type="secondary">System</Text>;
        const tenant = tenants.find((t) => t.id === tenantId);
        return tenant?.name || tenantId?.substring(0, 8) + '...';
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: AlertStatusType) => {
        const config = getStatusConfig(status);
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: 'Time',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => (
        <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm:ss')}>
          <span>{dayjs(date).fromNow()}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_: any, record: Alert) => (
        <Space size="small">
          {record.status === 'active' && (
            <>
              <Tooltip title="Acknowledge">
                <Button
                  type="text"
                  size="small"
                  icon={<EyeOutlined />}
                  onClick={() => handleAcknowledge(record.id)}
                />
              </Tooltip>
              <Tooltip title="Resolve">
                <Button
                  type="text"
                  size="small"
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleResolve(record.id)}
                  style={{ color: '#52c41a' }}
                />
              </Tooltip>
            </>
          )}
          {record.status !== 'dismissed' && (
            <Tooltip title="Dismiss">
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => handleDismiss(record.id)}
                danger
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys as number[]),
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '24px' }}>
        <BellOutlined style={{ marginRight: 8 }} />
        System Alerts
        {counts && counts.total > 0 && (
          <Badge
            count={counts.total}
            style={{ marginLeft: 12, backgroundColor: counts.critical > 0 ? '#ff4d4f' : '#faad14' }}
          />
        )}
      </h1>

      {/* Statistics */}
      {counts && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderLeft: '4px solid #ff4d4f' }}>
              <Statistic
                title="Critical"
                value={counts.critical}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderLeft: '4px solid #ff7a45' }}>
              <Statistic
                title="Error"
                value={counts.error}
                valueStyle={{ color: '#ff7a45' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderLeft: '4px solid #faad14' }}>
              <Statistic
                title="Warning"
                value={counts.warning}
                valueStyle={{ color: '#faad14' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small" style={{ borderLeft: '4px solid #1890ff' }}>
              <Statistic
                title="Info"
                value={counts.info}
                valueStyle={{ color: '#1890ff' }}
                prefix={<InfoCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="Filter by Tenant"
              value={filters.tenant_id}
              onChange={(value) => setFilters((prev) => ({ ...prev, tenant_id: value }))}
              style={{ width: '100%' }}
              allowClear
            >
              {tenants.map((tenant) => (
                <Option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="Severity"
              value={filters.severity}
              onChange={(value) => setFilters((prev) => ({ ...prev, severity: value }))}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="critical"><Tag color="red">Critical</Tag></Option>
              <Option value="error"><Tag color="orange">Error</Tag></Option>
              <Option value="warning"><Tag color="gold">Warning</Tag></Option>
              <Option value="info"><Tag color="blue">Info</Tag></Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="Status"
              value={filters.status}
              onChange={(value) => setFilters((prev) => ({ ...prev, status: value }))}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="active">Active</Option>
              <Option value="acknowledged">Acknowledged</Option>
              <Option value="resolved">Resolved</Option>
              <Option value="dismissed">Dismissed</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Space>
              <Switch
                checked={filters.active_only}
                onChange={(checked) => setFilters((prev) => ({ ...prev, active_only: checked }))}
              />
              <span>Active Only</span>
            </Space>
          </Col>
          <Col xs={12} sm={6} md={6}>
            <Space>
              <Button
                type="primary"
                icon={<FilterOutlined />}
                onClick={fetchAlerts}
              >
                Apply
              </Button>
              <Button
                onClick={() => {
                  setFilters({
                    tenant_id: undefined,
                    status: undefined,
                    severity: undefined,
                    active_only: true,
                  });
                  fetchAlerts();
                }}
              >
                Reset
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Alerts Table */}
      <Card
        title={
          <Space>
            <span>Alerts</span>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                fetchAlerts();
                fetchCounts();
              }}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
        extra={
          <Space>
            {selectedRowKeys.length > 0 && (
              <Button danger onClick={handleBulkDismiss}>
                Dismiss Selected ({selectedRowKeys.length})
              </Button>
            )}
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={alerts}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          pagination={{ pageSize: 20 }}
          scroll={{ x: 900 }}
          size="small"
          rowClassName={(record) => {
            if (record.severity === 'critical' && record.status === 'active') {
              return 'critical-alert-row';
            }
            return '';
          }}
        />
      </Card>

      <style>{`
        .critical-alert-row {
          background-color: #fff2f0;
          animation: pulse 2s infinite;
        }
        .critical-alert-row:hover td {
          background-color: #ffe8e6 !important;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
      `}</style>
    </div>
  );
};

export default AlertsPage;

