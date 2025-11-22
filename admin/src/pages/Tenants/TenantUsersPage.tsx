import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Tag,
  Popconfirm,
  Typography,
  Alert,
} from 'antd';
import {
  ArrowLeftOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  KeyOutlined,
  UserOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import apiClient from '@/services/api';
import { API_ENDPOINTS } from '@/config/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface TenantUser {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
  is_active: boolean;
  odoo_user_id: number | null;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

interface TenantUserFormData {
  email: string;
  password?: string;
  full_name: string;
  role: 'admin' | 'user';
  is_active: boolean;
  odoo_user_id?: number;
}

interface OdooCompany {
  id: number;
  name: string;
}

interface OdooUser {
  id: number;
  name: string;
  login: string;
  email: string;
  company_id: number;
}

const TenantUsersPage: React.FC = () => {
  const { tenantId } = useParams<{ tenantId: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const [users, setUsers] = useState<TenantUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<TenantUser | null>(null);
  const [changingPasswordUser, setChangingPasswordUser] = useState<TenantUser | null>(null);
  const [tenantName, setTenantName] = useState<string>('');
  
  // Odoo integration states
  const [odooCompanies, setOdooCompanies] = useState<OdooCompany[]>([]);
  const [odooUsers, setOdooUsers] = useState<OdooUser[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null);
  const [loadingCompanies, setLoadingCompanies] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [maxUsers, setMaxUsers] = useState<number>(5);
  const [currentUserCount, setCurrentUserCount] = useState<number>(0);

  useEffect(() => {
    if (tenantId) {
      fetchUsers();
      fetchTenantInfo();
    }
  }, [tenantId]);

  const fetchTenantInfo = async () => {
    try {
      const response = await apiClient.get(`${API_ENDPOINTS.TENANT(tenantId!)}`);
      setTenantName(response.data.name);
      setMaxUsers(response.data.max_users || 5);
    } catch (error: any) {
      console.error('Failed to fetch tenant info:', error);
    }
  };

  const fetchOdooCompanies = async () => {
    if (!tenantId) return;
    
    setLoadingCompanies(true);
    try {
      const response = await apiClient.get(`/admin/odoo-helpers/companies/${tenantId}`);
      if (response.data.success) {
        setOdooCompanies(response.data.companies);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to fetch Odoo companies');
      setOdooCompanies([]);
    } finally {
      setLoadingCompanies(false);
    }
  };

  const fetchOdooUsers = async (companyId: number) => {
    if (!tenantId) return;
    
    setLoadingUsers(true);
    try {
      const response = await apiClient.get(`/admin/odoo-helpers/users/${tenantId}`, {
        params: { company_id: companyId }
      });
      if (response.data.success) {
        setOdooUsers(response.data.users);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to fetch Odoo users');
      setOdooUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/admin/tenant-users', {
        params: { tenant_id: tenantId },
      });
      setUsers(response.data);
      setCurrentUserCount(response.data.length);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    form.setFieldsValue({ role: 'user', is_active: true });
    setSelectedCompany(null);
    setOdooUsers([]);
    setModalVisible(true);
    
    // Fetch companies when creating new user
    fetchOdooCompanies();
  };

  const handleCompanyChange = (companyId: number) => {
    setSelectedCompany(companyId);
    setOdooUsers([]);
    form.setFieldsValue({ odoo_user_id: undefined });
    fetchOdooUsers(companyId);
  };

  const handleOdooUserSelect = (userId: number) => {
    const selectedUser = odooUsers.find(u => u.id === userId);
    if (selectedUser) {
      form.setFieldsValue({
        full_name: selectedUser.name,
        email: selectedUser.email || `${selectedUser.login}@${tenantName.toLowerCase().replace(/\s+/g, '-')}.bridgecore.internal`,
      });
    }
  };

  const handleEdit = (user: TenantUser) => {
    setEditingUser(user);
    form.setFieldsValue({
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
      odoo_user_id: user.odoo_user_id,
    });
    setModalVisible(true);
  };

  const handleChangePassword = (user: TenantUser) => {
    setChangingPasswordUser(user);
    passwordForm.resetFields();
    setPasswordModalVisible(true);
  };

  const handleSubmit = async (values: TenantUserFormData) => {
    try {
      if (editingUser) {
        // Update user (without password)
        const { password, ...updateData } = values;
        await apiClient.put(`/admin/tenant-users/${editingUser.id}`, updateData);
        message.success('User updated successfully');
      } else {
        // Create new user (with password)
        await apiClient.post('/admin/tenant-users', {
          ...values,
          tenant_id: tenantId,
        });
        message.success('User created successfully');
      }
      setModalVisible(false);
      fetchUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handlePasswordSubmit = async (values: { password: string; confirm_password: string }) => {
    if (!changingPasswordUser) return;

    try {
      await apiClient.put(`/admin/tenant-users/${changingPasswordUser.id}`, {
        password: values.password,
      });
      message.success('Password changed successfully');
      setPasswordModalVisible(false);
      setChangingPasswordUser(null);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to change password');
    }
  };

  const handleDelete = async (userId: string) => {
    try {
      await apiClient.delete(`/admin/tenant-users/${userId}`);
      message.success('User deleted successfully');
      fetchUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const columns: ColumnsType<TenantUser> = [
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => (
        <Space>
          <UserOutlined />
          <Text strong>{email}</Text>
        </Space>
      ),
    },
    {
      title: 'Full Name',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'blue' : 'default'}>
          {role.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Odoo User ID',
      dataIndex: 'odoo_user_id',
      key: 'odoo_user_id',
      render: (id: number | null) => id || '-',
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string | null) =>
        date ? dayjs(date).format('YYYY-MM-DD HH:mm') : 'Never',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: TenantUser) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Edit
          </Button>
          <Button
            type="link"
            icon={<KeyOutlined />}
            onClick={() => handleChangePassword(record)}
          >
            Password
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this user?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/tenants')}
              >
                Back to Tenants
              </Button>
              <Title level={3} style={{ margin: 0 }}>
                Manage Users - {tenantName}
              </Title>
            </Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              Add User
            </Button>
          </Space>
        </Card>

        {/* Users Table */}
        <Card>
          <Table
            columns={columns}
            dataSource={users}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} users`,
            }}
          />
        </Card>
      </Space>

      {/* Create/Edit User Modal */}
      <Modal
        title={editingUser ? 'Edit User' : 'Create New User'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          {/* User Count Alert */}
          {!editingUser && (
            <Alert
              message={`Users: ${currentUserCount} / ${maxUsers}`}
              description={
                currentUserCount >= maxUsers
                  ? '⚠️ Maximum users reached. Please upgrade your plan or contact support.'
                  : `You can add ${maxUsers - currentUserCount} more user(s).`
              }
              type={currentUserCount >= maxUsers ? 'error' : 'info'}
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* Odoo Company Selection */}
          {!editingUser && (
            <>
              <Alert
                message="Link to Odoo User"
                description="Select a company and then choose an Odoo user to link with this BridgeCore account."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form.Item
                label="Odoo Company"
                tooltip="Select the company from your Odoo instance"
              >
                <Select
                  placeholder="Select Odoo Company"
                  onChange={handleCompanyChange}
                  loading={loadingCompanies}
                  value={selectedCompany}
                  showSearch
                  optionFilterProp="children"
                >
                  {odooCompanies.map(company => (
                    <Option key={company.id} value={company.id}>
                      {company.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="odoo_user_id"
                label="Odoo User"
                rules={[{ required: true, message: 'Please select an Odoo user' }]}
                tooltip="Select the Odoo user to link with this BridgeCore account"
              >
                <Select
                  placeholder="Select Odoo User"
                  onChange={handleOdooUserSelect}
                  loading={loadingUsers}
                  disabled={!selectedCompany}
                  showSearch
                  optionFilterProp="children"
                >
                  {odooUsers.map(user => (
                    <Option key={user.id} value={user.id}>
                      {user.name} ({user.login})
                      {user.email && ` - ${user.email}`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </>
          )}

          <Form.Item
            name="email"
            label="BridgeCore Email"
            rules={[
              { required: true, message: 'Please enter email' },
            ]}
            tooltip="This email will be used to login to BridgeCore"
          >
            <Input placeholder="user@company.bridgecore.internal" disabled={!!editingUser} />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="BridgeCore Password"
              rules={[
                { required: true, message: 'Please enter password' },
                { min: 8, message: 'Password must be at least 8 characters' },
              ]}
              tooltip="This password will be used to login to BridgeCore"
            >
              <Input.Password placeholder="Enter password (min 8 characters)" />
            </Form.Item>
          )}

          {editingUser && (
            <Alert
              message="To change password, use the 'Password' button in the table"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          <Form.Item
            name="full_name"
            label="Full Name"
            rules={[{ required: true, message: 'Please enter full name' }]}
          >
            <Input placeholder="John Doe" />
          </Form.Item>

          <Form.Item
            name="role"
            label="BridgeCore Role"
            rules={[{ required: true, message: 'Please select role' }]}
            tooltip="This role applies to BridgeCore only"
          >
            <Select placeholder="Select role">
              <Option value="user">User</Option>
              <Option value="admin">Admin</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label="Active"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          {editingUser && (
            <Form.Item
              name="odoo_user_id"
              label="Odoo User ID"
              tooltip="Cannot be changed after creation"
            >
              <Input type="number" disabled />
            </Form.Item>
          )}

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                disabled={!editingUser && currentUserCount >= maxUsers}
              >
                {editingUser ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Change Password Modal */}
      <Modal
        title={`Change Password - ${changingPasswordUser?.email}`}
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          setChangingPasswordUser(null);
        }}
        footer={null}
        width={500}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordSubmit}
        >
          <Form.Item
            name="password"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter new password' },
              { min: 8, message: 'Password must be at least 8 characters' },
            ]}
          >
            <Input.Password placeholder="Enter new password (min 8 characters)" />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="Confirm Password"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Please confirm password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Passwords do not match'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="Confirm new password" />
          </Form.Item>

          <Alert
            message="The user will need to use this new password for their next login"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setPasswordModalVisible(false);
                setChangingPasswordUser(null);
              }}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                Change Password
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TenantUsersPage;

