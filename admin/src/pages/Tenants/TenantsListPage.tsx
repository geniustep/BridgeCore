import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Tag, Input, Select, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, StopOutlined, CheckOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTenantStore } from '@/store/tenant.store';
import type { Tenant } from '@/types';

const { Search } = Input;

const TenantsListPage: React.FC = () => {
  const navigate = useNavigate();
  const { tenants, isLoading, fetchTenants, suspendTenant, activateTenant, deleteTenant } = useTenantStore();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();

  useEffect(() => {
    loadTenants();
  }, [statusFilter]);

  const loadTenants = () => {
    fetchTenants({ status: statusFilter });
  };

  const handleSuspend = async (id: string) => {
    try {
      await suspendTenant(id);
      message.success('Tenant suspended successfully');
    } catch {
      message.error('Failed to suspend tenant');
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await activateTenant(id);
      message.success('Tenant activated successfully');
    } catch {
      message.error('Failed to activate tenant');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteTenant(id);
      message.success('Tenant deleted successfully');
    } catch {
      message.error('Failed to delete tenant');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: any = {
      active: 'green',
      suspended: 'red',
      trial: 'orange',
      deleted: 'default',
    };
    return colors[status] || 'default';
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Tenant) => (
        <a onClick={() => navigate(`/tenants/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: 'Slug',
      dataIndex: 'slug',
      key: 'slug',
    },
    {
      title: 'Email',
      dataIndex: 'contact_email',
      key: 'contact_email',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Odoo URL',
      dataIndex: 'odoo_url',
      key: 'odoo_url',
      ellipsis: true,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Tenant) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => navigate(`/tenants/${record.id}`)}
          >
            Edit
          </Button>
          {record.status === 'active' ? (
            <Popconfirm
              title="Suspend this tenant?"
              onConfirm={() => handleSuspend(record.id)}
            >
              <Button type="link" size="small" danger icon={<StopOutlined />}>
                Suspend
              </Button>
            </Popconfirm>
          ) : (
            <Popconfirm
              title="Activate this tenant?"
              onConfirm={() => handleActivate(record.id)}
            >
              <Button type="link" size="small" icon={<CheckOutlined />}>
                Activate
              </Button>
            </Popconfirm>
          )}
          <Popconfirm
            title="Delete this tenant?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>Tenants</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/tenants/new')}
        >
          Add Tenant
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Filter by status"
          style={{ width: 200 }}
          allowClear
          onChange={setStatusFilter}
        >
          <Select.Option value="active">Active</Select.Option>
          <Select.Option value="trial">Trial</Select.Option>
          <Select.Option value="suspended">Suspended</Select.Option>
          <Select.Option value="deleted">Deleted</Select.Option>
        </Select>
      </Space>

      <Table
        columns={columns}
        dataSource={tenants}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default TenantsListPage;
