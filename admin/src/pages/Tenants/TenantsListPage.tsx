import React, { useEffect, useState, useMemo } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Select,
  Input,
  Card,
  Row,
  Col,
  Statistic,
  message,
  Dropdown,
  Tooltip,
  Typography,
  Badge,
  Modal,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  StopOutlined,
  CheckOutlined,
  SearchOutlined,
  MoreOutlined,
  GlobalOutlined,
  MailOutlined,
  DatabaseOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTenantStore } from '@/store/tenant.store';
import type { Tenant } from '@/types';
import type { MenuProps } from 'antd';

const { Title } = Typography;
const { Search } = Input;

const TenantsListPage: React.FC = () => {
  const navigate = useNavigate();
  const { tenants, isLoading, fetchTenants, suspendTenant, activateTenant, deleteTenant, statistics, fetchStatistics } = useTenantStore();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [searchText, setSearchText] = useState<string>('');

  useEffect(() => {
    loadTenants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  useEffect(() => {
    fetchStatistics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadTenants = () => {
    fetchTenants({ status: statusFilter });
  };

  const handleSuspend = async (id: string) => {
    try {
      await suspendTenant(id);
      message.success('Tenant suspended successfully');
      loadTenants();
    } catch {
      message.error('Failed to suspend tenant');
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await activateTenant(id);
      message.success('Tenant activated successfully');
      loadTenants();
    } catch {
      message.error('Failed to activate tenant');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteTenant(id);
      message.success('Tenant deleted successfully');
      loadTenants();
    } catch {
      message.error('Failed to delete tenant');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      suspended: 'red',
      trial: 'orange',
      deleted: 'default',
    };
    return colors[status] || 'default';
  };

  const getBadgeStatus = (status: string): 'success' | 'error' | 'warning' | 'default' => {
    const statusMap: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
      active: 'success',
      suspended: 'error',
      trial: 'warning',
      deleted: 'default',
    };
    return statusMap[status] || 'default';
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, React.ReactNode> = {
      active: <CheckCircleOutlined />,
      suspended: <StopOutlined />,
      trial: <ClockCircleOutlined />,
      deleted: <CloseCircleOutlined />,
    };
    return icons[status] || null;
  };

  // Filter tenants based on search text
  const filteredTenants = useMemo(() => {
    if (!searchText) return tenants;
    
    const searchLower = searchText.toLowerCase();
    return tenants.filter((tenant) =>
      tenant.name.toLowerCase().includes(searchLower) ||
      tenant.slug.toLowerCase().includes(searchLower) ||
      tenant.contact_email.toLowerCase().includes(searchLower) ||
      tenant.odoo_url.toLowerCase().includes(searchLower) ||
      tenant.odoo_database.toLowerCase().includes(searchLower)
    );
  }, [tenants, searchText]);

  const getActionMenu = (record: Tenant): MenuProps => ({
    items: [
      {
        key: 'view',
        label: 'View Details',
        icon: <EyeOutlined />,
        onClick: () => navigate(`/tenants/${record.id}`),
      },
      {
        key: 'edit',
        label: 'Edit',
        icon: <EditOutlined />,
        onClick: () => navigate(`/tenants/${record.id}/edit`),
      },
      {
        type: 'divider',
      },
      record.status === 'active'
        ? {
            key: 'suspend',
            label: 'Suspend',
            icon: <StopOutlined />,
            danger: true,
            onClick: () => {
              Modal.confirm({
                title: 'Suspend Tenant',
                content: `Are you sure you want to suspend "${record.name}"?`,
                okText: 'Suspend',
                okType: 'danger',
                cancelText: 'Cancel',
                onOk: () => handleSuspend(record.id),
              });
            },
          }
        : {
            key: 'activate',
            label: 'Activate',
            icon: <CheckOutlined />,
            onClick: () => {
              Modal.confirm({
                title: 'Activate Tenant',
                content: `Are you sure you want to activate "${record.name}"?`,
                okText: 'Activate',
                okType: 'primary',
                cancelText: 'Cancel',
                onOk: () => handleActivate(record.id),
              });
            },
          },
      {
        type: 'divider',
      },
      {
        key: 'delete',
        label: 'Delete',
        icon: <DeleteOutlined />,
        danger: true,
        onClick: () => {
          Modal.confirm({
            title: 'Delete Tenant',
            content: `Are you sure you want to delete "${record.name}"? This action cannot be undone.`,
            okText: 'Delete',
            okType: 'danger',
            cancelText: 'Cancel',
            onOk: () => handleDelete(record.id),
          });
        },
      },
    ],
  });

  const columns = [
    {
      title: 'Tenant',
      key: 'tenant',
      width: 250,
      fixed: 'left' as const,
      render: (_: any, record: Tenant) => (
        <Space direction="vertical" size={0}>
          <Button
            type="link"
            style={{ padding: 0, height: 'auto', fontWeight: 500 }}
            onClick={() => navigate(`/tenants/${record.id}`)}
          >
            {record.name}
          </Button>
          <Space size={4}>
            <Tag color="default" style={{ margin: 0 }}>
              {record.slug}
            </Tag>
            <Badge
              status={getBadgeStatus(record.status)}
              text={
                <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
                  {record.status}
                </span>
              }
            />
          </Space>
        </Space>
      ),
    },
    {
      title: 'Contact',
      key: 'contact',
      width: 200,
      render: (_: any, record: Tenant) => (
        <Space direction="vertical" size={2}>
          <Space size={4}>
            <MailOutlined style={{ color: '#8c8c8c' }} />
            <span style={{ fontSize: '13px' }}>{record.contact_email}</span>
          </Space>
          {record.contact_phone && (
            <span style={{ fontSize: '12px', color: '#8c8c8c', marginLeft: 20 }}>
              {record.contact_phone}
            </span>
          )}
        </Space>
      ),
    },
    {
      title: 'Odoo Configuration',
      key: 'odoo',
      width: 300,
      render: (_: any, record: Tenant) => (
        <Space direction="vertical" size={4}>
          <Tooltip title={record.odoo_url}>
            <Space size={4}>
              <GlobalOutlined style={{ color: '#1890ff' }} />
              <span style={{ fontSize: '13px' }} className="text-ellipsis">
                {record.odoo_url.length > 40
                  ? `${record.odoo_url.substring(0, 40)}...`
                  : record.odoo_url}
              </span>
            </Space>
          </Tooltip>
          <Space size={4}>
            <DatabaseOutlined style={{ color: '#52c41a' }} />
            <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
              {record.odoo_database}
            </span>
          </Space>
          {record.odoo_version && (
            <Tag color="blue" style={{ fontSize: '11px', margin: 0 }}>
              v{record.odoo_version}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 120,
      render: (_: any, record: Tenant) => (
        <Tag
          color={getStatusColor(record.status)}
          icon={getStatusIcon(record.status)}
          style={{ fontSize: '12px', padding: '4px 8px' }}
        >
          {record.status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Last Active',
      key: 'last_active',
      width: 150,
      render: (_: any, record: Tenant) => (
        <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
          {record.last_active_at
            ? new Date(record.last_active_at).toLocaleDateString()
            : 'Never'}
        </span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: Tenant) => (
        <Space size="small">
          <Tooltip title="View tenant details and settings">
            <Button
              type="primary"
              size="middle"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/tenants/${record.id}`)}
            >
              Details
            </Button>
          </Tooltip>
          <Dropdown menu={getActionMenu(record)} trigger={['click']}>
            <Button
              type="default"
              size="middle"
              icon={<MoreOutlined />}
              onClick={(e) => e.stopPropagation()}
            />
          </Dropdown>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header Section */}
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
        <Title level={2} style={{ margin: 0 }}>
          Tenants Management
        </Title>
        <Button
          type="primary"
          size="large"
          icon={<PlusOutlined />}
          onClick={() => navigate('/tenants/create')}
        >
          Add New Tenant
        </Button>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
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
              title="Active"
              value={statistics?.active || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Trial"
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

      {/* Filters and Search */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="Search tenants..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={setSearchText}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="Filter by status"
              style={{ width: '100%' }}
              size="large"
              allowClear
              value={statusFilter}
              onChange={setStatusFilter}
            >
              <Select.Option value="active">
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  Active
                </Space>
              </Select.Option>
              <Select.Option value="trial">
                <Space>
                  <ClockCircleOutlined style={{ color: '#faad14' }} />
                  Trial
                </Space>
              </Select.Option>
              <Select.Option value="suspended">
                <Space>
                  <StopOutlined style={{ color: '#ff4d4f' }} />
                  Suspended
                </Space>
              </Select.Option>
              <Select.Option value="deleted">
                <Space>
                  <CloseCircleOutlined />
                  Deleted
                </Space>
              </Select.Option>
            </Select>
          </Col>
          <Col xs={24} sm={24} md={8} style={{ textAlign: 'right' }}>
            <span style={{ color: '#8c8c8c', fontSize: '14px' }}>
              Showing {filteredTenants.length} of {tenants.length} tenants
            </span>
          </Col>
        </Row>
      </Card>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredTenants}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} tenants`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          scroll={{ x: 1200 }}
          size="middle"
          rowClassName={(record) =>
            record.status === 'suspended' ? 'suspended-row' : ''
          }
        />
      </Card>

      <style>{`
        .suspended-row {
          opacity: 0.7;
        }
        .text-ellipsis {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 250px;
          display: inline-block;
        }
      `}</style>
    </div>
  );
};

export default TenantsListPage;
