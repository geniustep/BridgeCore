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
  Drawer,
  Descriptions,
  Typography,
  Modal,
  Form,
  Input,
  Switch,
  Badge,
} from 'antd';
import {
  ReloadOutlined,
  FilterOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  BugOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { logsService } from '@/services/logs.service';
import { useTenantStore } from '@/store/tenant.store';
import { ErrorLog } from '@/types';
import dayjs from 'dayjs';

const { Option } = Select;
const { Text } = Typography;
const { TextArea } = Input;

const ErrorLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<ErrorLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<ErrorLog | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [resolveModalVisible, setResolveModalVisible] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [form] = Form.useForm();

  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });

  // Filters
  const [filters, setFilters] = useState({
    tenant_id: undefined as string | undefined,
    severity: undefined as string | undefined,
    unresolved_only: true,
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
      const data = await logsService.getErrorLogs({
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
      message.error('Failed to load error logs');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = () => {
    fetchLogs(1);
  };

  const handleResetFilters = () => {
    setFilters({
      tenant_id: undefined,
      severity: undefined,
      unresolved_only: true,
    });
    fetchLogs(1);
  };

  const handleViewDetails = (log: ErrorLog) => {
    setSelectedLog(log);
    setDrawerVisible(true);
  };

  const handleOpenResolveModal = (log: ErrorLog) => {
    setSelectedLog(log);
    setResolveModalVisible(true);
  };

  const handleResolveError = async () => {
    if (!selectedLog) return;

    setResolving(true);
    try {
      const values = await form.validateFields();
      await logsService.resolveError(selectedLog.id, values.resolution_notes);
      message.success('Error marked as resolved');
      setResolveModalVisible(false);
      form.resetFields();
      fetchLogs(pagination.current);
    } catch (error: any) {
      message.error('Failed to resolve error');
    } finally {
      setResolving(false);
    }
  };

  const handleTableChange = (paginationConfig: any) => {
    fetchLogs(paginationConfig.current);
  };

  const getSeverityConfig = (
    severity: string
  ): { color: string; icon: React.ReactNode } => {
    const configs: Record<string, { color: string; icon: React.ReactNode }> = {
      critical: { color: 'red', icon: <ExclamationCircleOutlined /> },
      high: { color: 'orange', icon: <WarningOutlined /> },
      medium: { color: 'gold', icon: <BugOutlined /> },
      low: { color: 'blue', icon: <BugOutlined /> },
    };
    return configs[severity] || { color: 'default', icon: <BugOutlined /> };
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
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => {
        const config = getSeverityConfig(severity);
        return (
          <Tag color={config.color} icon={config.icon}>
            {severity.toUpperCase()}
          </Tag>
        );
      },
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
      title: 'Error Type',
      dataIndex: 'error_type',
      key: 'error_type',
      width: 150,
      render: (type: string) => (
        <code style={{ fontSize: '11px', color: '#cf1322' }}>{type}</code>
      ),
    },
    {
      title: 'Message',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
      render: (msg: string) => (
        <Text style={{ fontSize: '12px' }}>{msg}</Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'resolved',
      key: 'resolved',
      width: 100,
      render: (resolved: boolean) => (
        <Badge
          status={resolved ? 'success' : 'error'}
          text={resolved ? 'Resolved' : 'Open'}
        />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_: any, record: ErrorLog) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetails(record)}
          >
            View
          </Button>
          {!record.resolved && (
            <Button
              type="text"
              size="small"
              icon={<CheckCircleOutlined />}
              onClick={() => handleOpenResolveModal(record)}
              style={{ color: '#52c41a' }}
            >
              Resolve
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const unresolvedCount = logs.filter((l) => !l.resolved).length;

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '24px' }}>
        Error Logs
        {unresolvedCount > 0 && (
          <Badge
            count={unresolvedCount}
            style={{ marginLeft: '12px' }}
            overflowCount={999}
          />
        )}
      </h1>

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
              placeholder="Severity"
              value={filters.severity}
              onChange={(value) => handleFilterChange('severity', value)}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="critical">
                <Tag color="red">Critical</Tag>
              </Option>
              <Option value="high">
                <Tag color="orange">High</Tag>
              </Option>
              <Option value="medium">
                <Tag color="gold">Medium</Tag>
              </Option>
              <Option value="low">
                <Tag color="blue">Low</Tag>
              </Option>
            </Select>
          </Col>

          <Col xs={24} sm={12} md={4}>
            <Space>
              <Switch
                checked={filters.unresolved_only}
                onChange={(checked) =>
                  handleFilterChange('unresolved_only', checked)
                }
              />
              <span>Unresolved Only</span>
            </Space>
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

      {/* Error Logs Table */}
      <Card
        title={
          <Space>
            <span>Application Errors</span>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchLogs(pagination.current)}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
          scroll={{ x: 1100 }}
          size="small"
          rowClassName={(record) =>
            record.severity === 'critical' ? 'critical-row' : ''
          }
        />
      </Card>

      {/* Error Details Drawer */}
      <Drawer
        title="Error Details"
        placement="right"
        width={700}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        extra={
          selectedLog && !selectedLog.resolved && (
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => {
                setDrawerVisible(false);
                handleOpenResolveModal(selectedLog);
              }}
            >
              Mark Resolved
            </Button>
          )
        }
      >
        {selectedLog && (
          <div>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="ID">{selectedLog.id}</Descriptions.Item>
              <Descriptions.Item label="Timestamp">
                {dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss.SSS')}
              </Descriptions.Item>
              <Descriptions.Item label="Severity">
                <Tag color={getSeverityConfig(selectedLog.severity).color}>
                  {selectedLog.severity.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Badge
                  status={selectedLog.resolved ? 'success' : 'error'}
                  text={selectedLog.resolved ? 'Resolved' : 'Open'}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Tenant ID">
                {selectedLog.tenant_id || 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="User ID">
                {selectedLog.user_id || 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Error Type">
                <code style={{ color: '#cf1322' }}>
                  {selectedLog.error_type}
                </code>
              </Descriptions.Item>
              <Descriptions.Item label="Endpoint">
                <code>{selectedLog.endpoint || 'N/A'}</code>
              </Descriptions.Item>
              <Descriptions.Item label="Request ID">
                {selectedLog.request_id || 'N/A'}
              </Descriptions.Item>
            </Descriptions>

            <Card
              title="Error Message"
              size="small"
              style={{ marginTop: '16px' }}
            >
              <Text type="danger">{selectedLog.error_message}</Text>
            </Card>

            {selectedLog.stack_trace && (
              <Card
                title="Stack Trace"
                size="small"
                style={{ marginTop: '16px' }}
              >
                <pre
                  style={{
                    fontSize: '11px',
                    background: '#f5f5f5',
                    padding: '12px',
                    borderRadius: '4px',
                    overflow: 'auto',
                    maxHeight: '300px',
                  }}
                >
                  {selectedLog.stack_trace}
                </pre>
              </Card>
            )}

            {selectedLog.request_data && (
              <Card
                title="Request Data"
                size="small"
                style={{ marginTop: '16px' }}
              >
                <pre
                  style={{
                    fontSize: '11px',
                    background: '#f5f5f5',
                    padding: '12px',
                    borderRadius: '4px',
                    overflow: 'auto',
                    maxHeight: '200px',
                  }}
                >
                  {JSON.stringify(selectedLog.request_data, null, 2)}
                </pre>
              </Card>
            )}

            {selectedLog.resolved && (
              <Card
                title="Resolution"
                size="small"
                style={{ marginTop: '16px' }}
              >
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Resolved At">
                    {selectedLog.resolved_at
                      ? dayjs(selectedLog.resolved_at).format(
                          'YYYY-MM-DD HH:mm:ss'
                        )
                      : 'N/A'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Resolved By">
                    {selectedLog.resolved_by || 'N/A'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Resolution Notes">
                    {selectedLog.resolution_notes || 'No notes provided'}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            )}
          </div>
        )}
      </Drawer>

      {/* Resolve Modal */}
      <Modal
        title="Resolve Error"
        open={resolveModalVisible}
        onOk={handleResolveError}
        onCancel={() => {
          setResolveModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={resolving}
        okText="Mark Resolved"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="resolution_notes"
            label="Resolution Notes"
            rules={[
              {
                required: true,
                message: 'Please enter resolution notes',
              },
            ]}
          >
            <TextArea
              rows={4}
              placeholder="Describe how this error was resolved..."
            />
          </Form.Item>
        </Form>

        {selectedLog && (
          <div style={{ marginTop: '16px' }}>
            <Text type="secondary">
              Error: <code>{selectedLog.error_type}</code>
            </Text>
            <br />
            <Text type="secondary">{selectedLog.error_message}</Text>
          </div>
        )}
      </Modal>

      <style>{`
        .critical-row {
          background-color: #fff2f0;
        }
        .critical-row:hover td {
          background-color: #ffe8e6 !important;
        }
      `}</style>
    </div>
  );
};

export default ErrorLogsPage;
