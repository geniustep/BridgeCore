import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Select,
  DatePicker,
  Space,
  Tag,
  Button,
  Row,
  Col,
  message,
  Drawer,
  Descriptions,
  Typography,
} from 'antd';
import {
  ReloadOutlined,
  FilterOutlined,
  EyeOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { logsService } from '@/services/logs.service';
import { useTenantStore } from '@/store/tenant.store';
import { UsageLog } from '@/types';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text } = Typography;

const UsageLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<UsageLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<UsageLog | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });

  // Filters
  const [filters, setFilters] = useState({
    tenant_id: undefined as string | undefined,
    method: undefined as string | undefined,
    status_code: undefined as number | undefined,
    start_date: undefined as string | undefined,
    end_date: undefined as string | undefined,
  });

  const { tenants, fetchTenants } = useTenantStore();

  useEffect(() => {
    fetchTenants();
    fetchLogs();
  }, []);

  const fetchLogs = async (page = 1) => {
    setLoading(true);
    try {
      const skip = (page - 1) * pagination.pageSize;
      const data = await logsService.getUsageLogs({
        skip,
        limit: pagination.pageSize,
        ...filters,
      });
      setLogs(data);
      setPagination((prev) => ({
        ...prev,
        current: page,
        total: data.length < pagination.pageSize ? skip + data.length : skip + pagination.pageSize * 2,
      }));
    } catch (error: any) {
      message.error('Failed to load usage logs');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleDateRangeChange = (dates: any) => {
    if (dates && dates.length === 2) {
      setFilters((prev) => ({
        ...prev,
        start_date: dates[0].toISOString(),
        end_date: dates[1].toISOString(),
      }));
    } else {
      setFilters((prev) => ({
        ...prev,
        start_date: undefined,
        end_date: undefined,
      }));
    }
  };

  const handleApplyFilters = () => {
    fetchLogs(1);
  };

  const handleResetFilters = () => {
    setFilters({
      tenant_id: undefined,
      method: undefined,
      status_code: undefined,
      start_date: undefined,
      end_date: undefined,
    });
    fetchLogs(1);
  };

  const handleViewDetails = (log: UsageLog) => {
    setSelectedLog(log);
    setDrawerVisible(true);
  };

  const handleTableChange = (paginationConfig: any) => {
    fetchLogs(paginationConfig.current);
  };

  const getStatusCodeColor = (code: number): string => {
    if (code >= 200 && code < 300) return 'green';
    if (code >= 300 && code < 400) return 'blue';
    if (code >= 400 && code < 500) return 'orange';
    return 'red';
  };

  const getMethodColor = (method: string): string => {
    const colors: Record<string, string> = {
      GET: 'green',
      POST: 'blue',
      PUT: 'orange',
      PATCH: 'cyan',
      DELETE: 'red',
    };
    return colors[method] || 'default';
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: 'Tenant',
      dataIndex: 'tenant_id',
      key: 'tenant_id',
      width: 150,
      render: (tenantId: string) => {
        const tenant = tenants.find((t) => t.id === tenantId);
        return tenant?.name || tenantId?.substring(0, 8) + '...';
      },
    },
    {
      title: 'Method',
      dataIndex: 'method',
      key: 'method',
      width: 90,
      render: (method: string) => (
        <Tag color={getMethodColor(method)}>{method}</Tag>
      ),
    },
    {
      title: 'Endpoint',
      dataIndex: 'endpoint',
      key: 'endpoint',
      ellipsis: true,
      render: (endpoint: string) => (
        <code style={{ fontSize: '12px' }}>{endpoint}</code>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status_code',
      key: 'status_code',
      width: 80,
      render: (code: number) => (
        <Tag color={getStatusCodeColor(code)}>{code}</Tag>
      ),
    },
    {
      title: 'Response Time',
      dataIndex: 'response_time_ms',
      key: 'response_time_ms',
      width: 120,
      render: (time: number) => {
        const color = time < 300 ? '#52c41a' : time < 1000 ? '#faad14' : '#f5222d';
        return <span style={{ color }}>{time}ms</span>;
      },
    },
    {
      title: 'IP Address',
      dataIndex: 'client_ip',
      key: 'client_ip',
      width: 130,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_: any, record: UsageLog) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetails(record)}
        >
          View
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '24px' }}>Usage Logs</h1>

      {/* Filters */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Select Tenant"
              value={filters.tenant_id}
              onChange={(value) => handleFilterChange('tenant_id', value)}
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

          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Method"
              value={filters.method}
              onChange={(value) => handleFilterChange('method', value)}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="GET">GET</Option>
              <Option value="POST">POST</Option>
              <Option value="PUT">PUT</Option>
              <Option value="PATCH">PATCH</Option>
              <Option value="DELETE">DELETE</Option>
            </Select>
          </Col>

          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Status Code"
              value={filters.status_code}
              onChange={(value) => handleFilterChange('status_code', value)}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value={200}>200 OK</Option>
              <Option value={201}>201 Created</Option>
              <Option value={400}>400 Bad Request</Option>
              <Option value={401}>401 Unauthorized</Option>
              <Option value={403}>403 Forbidden</Option>
              <Option value={404}>404 Not Found</Option>
              <Option value={500}>500 Server Error</Option>
            </Select>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <RangePicker
              showTime
              onChange={handleDateRangeChange}
              style={{ width: '100%' }}
            />
          </Col>

          <Col xs={24} sm={24} md={4}>
            <Space>
              <Button
                type="primary"
                icon={<FilterOutlined />}
                onClick={handleApplyFilters}
              >
                Apply
              </Button>
              <Button onClick={handleResetFilters}>Reset</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Logs Table */}
      <Card
        title={
          <Space>
            <span>API Request Logs</span>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchLogs(pagination.current)}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
        extra={
          <Button icon={<DownloadOutlined />}>
            Export CSV
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* Log Details Drawer */}
      <Drawer
        title="Log Details"
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedLog && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="ID">{selectedLog.id}</Descriptions.Item>
            <Descriptions.Item label="Timestamp">
              {dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss.SSS')}
            </Descriptions.Item>
            <Descriptions.Item label="Tenant ID">
              {selectedLog.tenant_id}
            </Descriptions.Item>
            <Descriptions.Item label="User ID">
              {selectedLog.user_id || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Method">
              <Tag color={getMethodColor(selectedLog.method)}>
                {selectedLog.method}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Endpoint">
              <code>{selectedLog.endpoint}</code>
            </Descriptions.Item>
            <Descriptions.Item label="Status Code">
              <Tag color={getStatusCodeColor(selectedLog.status_code)}>
                {selectedLog.status_code}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Response Time">
              {selectedLog.response_time_ms}ms
            </Descriptions.Item>
            <Descriptions.Item label="Client IP">
              {selectedLog.client_ip}
            </Descriptions.Item>
            <Descriptions.Item label="User Agent">
              <Text
                style={{ fontSize: '12px', wordBreak: 'break-all' }}
                copyable
              >
                {selectedLog.user_agent || 'N/A'}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Request Body Size">
              {selectedLog.request_body_size || 0} bytes
            </Descriptions.Item>
            <Descriptions.Item label="Response Body Size">
              {selectedLog.response_body_size || 0} bytes
            </Descriptions.Item>
            {selectedLog.odoo_model && (
              <Descriptions.Item label="Odoo Model">
                {selectedLog.odoo_model}
              </Descriptions.Item>
            )}
            {selectedLog.odoo_method && (
              <Descriptions.Item label="Odoo Method">
                {selectedLog.odoo_method}
              </Descriptions.Item>
            )}
            {selectedLog.error_message && (
              <Descriptions.Item label="Error Message">
                <Text type="danger">{selectedLog.error_message}</Text>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
};

export default UsageLogsPage;
