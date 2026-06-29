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
  Modal,
  Form,
  Input,
  InputNumber,
  Switch,
  Statistic,
  Tooltip,
  Typography,
  Badge,
} from 'antd';
import {
  ReloadOutlined,
  PlusOutlined,
  DeleteOutlined,
  UnlockOutlined,
  SafetyOutlined,
  StopOutlined,
  SearchOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { ipBlockService } from '@/services/ipblock.service';
import { useTenantStore } from '@/store/tenant.store';
import { IPBlock, IPBlockStats, BlockReason } from '@/types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Option } = Select;
const { Text } = Typography;
const { TextArea } = Input;

const IPBlocksPage: React.FC = () => {
  const [blocks, setBlocks] = useState<IPBlock[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<IPBlockStats | null>(null);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [checkModalVisible, setCheckModalVisible] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [checkResult, setCheckResult] = useState<{ is_blocked: boolean; block_info: IPBlock | null } | null>(null);
  const [form] = Form.useForm();
  const [checkForm] = Form.useForm();

  const [filters, setFilters] = useState({
    reason: undefined as BlockReason | undefined,
    active_only: true,
  });

  const { tenants, fetchTenants } = useTenantStore();

  useEffect(() => {
    fetchTenants();
    fetchBlocks();
    fetchStats();
  }, []);

  const fetchBlocks = async () => {
    setLoading(true);
    try {
      const data = await ipBlockService.getBlockedIPs({
        ...filters,
        limit: 100,
      });
      setBlocks(data);
    } catch (error) {
      message.error('Failed to load blocked IPs');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await ipBlockService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleAddBlock = async (values: any) => {
    setAddLoading(true);
    try {
      await ipBlockService.blockIP({
        ip_address: values.ip_address,
        reason: values.reason,
        description: values.description,
        tenant_id: values.tenant_id,
        duration_hours: values.is_permanent ? undefined : values.duration_hours,
        is_permanent: values.is_permanent,
      });
      message.success('IP blocked successfully');
      setAddModalVisible(false);
      form.resetFields();
      fetchBlocks();
      fetchStats();
    } catch (error) {
      message.error('Failed to block IP');
    } finally {
      setAddLoading(false);
    }
  };

  const handleUnblock = async (ipAddress: string) => {
    Modal.confirm({
      title: 'Unblock IP?',
      content: `Are you sure you want to unblock ${ipAddress}?`,
      okText: 'Unblock',
      onOk: async () => {
        try {
          await ipBlockService.unblockIP(ipAddress);
          message.success('IP unblocked');
          fetchBlocks();
          fetchStats();
        } catch (error) {
          message.error('Failed to unblock IP');
        }
      },
    });
  };

  const handleDelete = async (blockId: number) => {
    Modal.confirm({
      title: 'Delete Block Record?',
      content: 'This will permanently delete the block record. Continue?',
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          await ipBlockService.deleteBlock(blockId);
          message.success('Block record deleted');
          fetchBlocks();
          fetchStats();
        } catch (error) {
          message.error('Failed to delete block');
        }
      },
    });
  };

  const handleCheckIP = async (values: { ip_address: string }) => {
    try {
      const result = await ipBlockService.checkIP(values.ip_address);
      setCheckResult(result);
    } catch (error) {
      message.error('Failed to check IP');
    }
  };

  const getReasonConfig = (reason: BlockReason) => {
    const configs: Record<BlockReason, { color: string; label: string }> = {
      rate_limit_abuse: { color: 'orange', label: 'Rate Limit Abuse' },
      brute_force: { color: 'red', label: 'Brute Force' },
      suspicious_activity: { color: 'volcano', label: 'Suspicious Activity' },
      security_threat: { color: 'magenta', label: 'Security Threat' },
      manual_block: { color: 'blue', label: 'Manual Block' },
      spam: { color: 'gold', label: 'Spam' },
    };
    return configs[reason] || { color: 'default', label: reason };
  };

  const columns = [
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ip: string, record: IPBlock) => (
        <Space>
          <code style={{ fontSize: 13, fontWeight: 600 }}>{ip}</code>
          {record.is_permanent && (
            <Tag color="red" icon={<StopOutlined />}>Permanent</Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      width: 160,
      render: (reason: BlockReason) => {
        const config = getReasonConfig(reason);
        return <Tag color={config.color}>{config.label}</Tag>;
      },
    },
    {
      title: 'Violations',
      dataIndex: 'violation_count',
      key: 'violation_count',
      width: 100,
      render: (count: number) => (
        <Badge count={count} showZero color={count > 3 ? 'red' : 'orange'} />
      ),
    },
    {
      title: 'Tenant',
      dataIndex: 'tenant_id',
      key: 'tenant_id',
      width: 150,
      render: (tenantId: string) => {
        if (!tenantId) return <Text type="secondary">-</Text>;
        const tenant = tenants.find((t) => t.id === tenantId);
        return tenant?.name || tenantId?.substring(0, 8) + '...';
      },
    },
    {
      title: 'Blocked At',
      dataIndex: 'blocked_at',
      key: 'blocked_at',
      width: 150,
      render: (date: string) => (
        <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm:ss')}>
          <span>{dayjs(date).fromNow()}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Expires',
      dataIndex: 'expires_at',
      key: 'expires_at',
      width: 150,
      render: (date: string | null, record: IPBlock) => {
        if (record.is_permanent) return <Text type="danger">Never</Text>;
        if (!date) return <Text type="secondary">-</Text>;
        const isExpired = dayjs(date).isBefore(dayjs());
        return (
          <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm:ss')}>
            <Text type={isExpired ? 'secondary' : 'warning'}>
              {dayjs(date).fromNow()}
            </Text>
          </Tooltip>
        );
      },
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'red' : 'green'}>
          {isActive ? 'Blocked' : 'Unblocked'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: any, record: IPBlock) => (
        <Space size="small">
          {record.is_active && (
            <Tooltip title="Unblock">
              <Button
                type="text"
                size="small"
                icon={<UnlockOutlined />}
                onClick={() => handleUnblock(record.ip_address)}
                style={{ color: '#52c41a' }}
              />
            </Tooltip>
          )}
          <Tooltip title="Delete Record">
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.id)}
              danger
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '24px' }}>
        <SafetyOutlined style={{ marginRight: 8 }} />
        IP Blocking
        {stats && stats.active_blocks > 0 && (
          <Badge
            count={stats.active_blocks}
            style={{ marginLeft: 12, backgroundColor: '#ff4d4f' }}
          />
        )}
      </h1>

      {/* Statistics */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={8}>
            <Card size="small" style={{ borderLeft: '4px solid #ff4d4f' }}>
              <Statistic
                title="Active Blocks"
                value={stats.active_blocks}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<StopOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small" style={{ borderLeft: '4px solid #faad14' }}>
              <Statistic
                title="Blocked Last 24h"
                value={stats.blocked_last_24h}
                valueStyle={{ color: '#faad14' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small">
              <div>
                <Text type="secondary">Top Reasons:</Text>
                <div style={{ marginTop: 8 }}>
                  {Object.entries(stats.by_reason || {}).map(([reason, count]) => (
                    <Tag key={reason} color={getReasonConfig(reason as BlockReason).color}>
                      {getReasonConfig(reason as BlockReason).label}: {count}
                    </Tag>
                  ))}
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* Actions */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle" justify="space-between">
          <Col>
            <Space>
              <Select
                placeholder="Filter by Reason"
                value={filters.reason}
                onChange={(value) => setFilters((prev) => ({ ...prev, reason: value }))}
                style={{ width: 200 }}
                allowClear
              >
                <Option value="rate_limit_abuse">Rate Limit Abuse</Option>
                <Option value="brute_force">Brute Force</Option>
                <Option value="suspicious_activity">Suspicious Activity</Option>
                <Option value="security_threat">Security Threat</Option>
                <Option value="manual_block">Manual Block</Option>
                <Option value="spam">Spam</Option>
              </Select>
              <Switch
                checked={filters.active_only}
                onChange={(checked) => setFilters((prev) => ({ ...prev, active_only: checked }))}
              />
              <span>Active Only</span>
              <Button icon={<ReloadOutlined />} onClick={fetchBlocks}>
                Refresh
              </Button>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<SearchOutlined />}
                onClick={() => setCheckModalVisible(true)}
              >
                Check IP
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setAddModalVisible(true)}
                danger
              >
                Block IP
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Blocks Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={blocks}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* Add Block Modal */}
      <Modal
        title={
          <Space>
            <StopOutlined style={{ color: '#ff4d4f' }} />
            Block IP Address
          </Space>
        }
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddBlock}
          initialValues={{
            duration_hours: 24,
            is_permanent: false,
            reason: 'manual_block',
          }}
        >
          <Form.Item
            name="ip_address"
            label="IP Address"
            rules={[
              { required: true, message: 'Please enter IP address' },
              {
                pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([a-fA-F0-9:]+)$/,
                message: 'Please enter a valid IP address',
              },
            ]}
          >
            <Input placeholder="e.g., 192.168.1.1" />
          </Form.Item>

          <Form.Item
            name="reason"
            label="Block Reason"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="manual_block">Manual Block</Option>
              <Option value="rate_limit_abuse">Rate Limit Abuse</Option>
              <Option value="brute_force">Brute Force</Option>
              <Option value="suspicious_activity">Suspicious Activity</Option>
              <Option value="security_threat">Security Threat</Option>
              <Option value="spam">Spam</Option>
            </Select>
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Reason for blocking..." />
          </Form.Item>

          <Form.Item name="tenant_id" label="Associated Tenant (Optional)">
            <Select allowClear placeholder="Select tenant...">
              {tenants.map((tenant) => (
                <Option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="is_permanent" valuePropName="checked" label="Permanent Block">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                noStyle
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.is_permanent !== currentValues.is_permanent
                }
              >
                {({ getFieldValue }) =>
                  !getFieldValue('is_permanent') && (
                    <Form.Item name="duration_hours" label="Duration (hours)">
                      <InputNumber min={1} max={8760} style={{ width: '100%' }} />
                    </Form.Item>
                  )
                }
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setAddModalVisible(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={addLoading} danger>
                Block IP
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Check IP Modal */}
      <Modal
        title={
          <Space>
            <SearchOutlined />
            Check IP Status
          </Space>
        }
        open={checkModalVisible}
        onCancel={() => {
          setCheckModalVisible(false);
          checkForm.resetFields();
          setCheckResult(null);
        }}
        footer={null}
      >
        <Form form={checkForm} layout="vertical" onFinish={handleCheckIP}>
          <Form.Item
            name="ip_address"
            label="IP Address"
            rules={[{ required: true, message: 'Please enter IP address' }]}
          >
            <Input.Search
              placeholder="Enter IP to check..."
              enterButton="Check"
              onSearch={(value) => handleCheckIP({ ip_address: value })}
            />
          </Form.Item>
        </Form>

        {checkResult && (
          <Card
            size="small"
            style={{
              marginTop: 16,
              backgroundColor: checkResult.is_blocked ? '#fff2f0' : '#f6ffed',
              borderColor: checkResult.is_blocked ? '#ffccc7' : '#b7eb8f',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              {checkResult.is_blocked ? (
                <>
                  <StopOutlined style={{ fontSize: 32, color: '#ff4d4f' }} />
                  <h3 style={{ color: '#ff4d4f', marginTop: 8 }}>IP is Blocked</h3>
                  {checkResult.block_info && (
                    <div style={{ textAlign: 'left', marginTop: 16 }}>
                      <p><strong>Reason:</strong> {getReasonConfig(checkResult.block_info.reason).label}</p>
                      <p><strong>Blocked:</strong> {dayjs(checkResult.block_info.blocked_at).format('YYYY-MM-DD HH:mm')}</p>
                      <p><strong>Violations:</strong> {checkResult.block_info.violation_count}</p>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <SafetyOutlined style={{ fontSize: 32, color: '#52c41a' }} />
                  <h3 style={{ color: '#52c41a', marginTop: 8 }}>IP is Not Blocked</h3>
                </>
              )}
            </div>
          </Card>
        )}
      </Modal>
    </div>
  );
};

export default IPBlocksPage;

