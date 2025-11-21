import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Form,
  Input,
  Button,
  Card,
  message,
  Select,
  InputNumber,
  Space,
  Divider,
  DatePicker,
  Tag,
  Spin,
  Alert,
} from 'antd';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons';
import { tenantService } from '@/services/tenant.service';
import { Tenant, TenantUpdate, Plan } from '@/types';
import apiClient from '@/services/api';
import { API_ENDPOINTS } from '@/config/api';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { Option } = Select;

const EditTenantPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [tenant, setTenant] = useState<Tenant | null>(null);

  useEffect(() => {
    if (id) {
      fetchTenant();
      fetchPlans();
    }
  }, [id]);

  const fetchTenant = async () => {
    if (!id) return;

    setFetching(true);
    try {
      const data = await tenantService.getTenant(id);
      setTenant(data);

      // Populate form with existing data
      form.setFieldsValue({
        name: data.name,
        slug: data.slug,
        description: data.description,
        contact_email: data.contact_email,
        contact_phone: data.contact_phone,
        odoo_url: data.odoo_url,
        odoo_database: data.odoo_database,
        odoo_version: data.odoo_version,
        odoo_username: data.odoo_username,
        status: data.status,
        plan_id: data.plan_id,
        max_requests_per_day: data.max_requests_per_day,
        max_requests_per_hour: data.max_requests_per_hour,
        allowed_models: data.allowed_models,
        allowed_features: data.allowed_features,
        trial_ends_at: data.trial_ends_at ? dayjs(data.trial_ends_at) : null,
        subscription_ends_at: data.subscription_ends_at
          ? dayjs(data.subscription_ends_at)
          : null,
      });
    } catch (error: any) {
      message.error('Failed to load tenant details');
      navigate('/tenants');
    } finally {
      setFetching(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await apiClient.get<Plan[]>(API_ENDPOINTS.PLANS);
      setPlans(response.data);
    } catch (error: any) {
      message.error('Failed to load subscription plans');
    }
  };

  const handlePlanChange = (planId: string) => {
    const plan = plans.find((p) => p.id === planId);

    // Auto-fill rate limits from plan if not custom
    if (plan) {
      form.setFieldsValue({
        max_requests_per_day: plan.max_requests_per_day,
        max_requests_per_hour: plan.max_requests_per_hour,
      });
    }
  };

  const onFinish = async (values: any) => {
    if (!id) return;

    setLoading(true);
    try {
      const updateData: TenantUpdate = {
        ...values,
        trial_ends_at: values.trial_ends_at?.toISOString(),
        subscription_ends_at: values.subscription_ends_at?.toISOString(),
        allowed_models: values.allowed_models || [],
        allowed_features: values.allowed_features || [],
      };

      // Only include password if it was changed
      if (!values.odoo_password) {
        delete updateData.odoo_password;
      }

      await tenantService.updateTenant(id, updateData);
      message.success('Tenant updated successfully');
      navigate('/tenants');
    } catch (error: any) {
      message.error(
        error.response?.data?.detail || 'Failed to update tenant'
      );
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
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

  return (
    <div style={{ padding: '24px' }}>
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/tenants')}
        style={{ marginBottom: '16px' }}
      >
        Back to Tenants
      </Button>

      <Card title={`Edit Tenant: ${tenant.name}`}>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Divider orientation="left">Basic Information</Divider>

          <Form.Item
            name="name"
            label="Tenant Name"
            rules={[
              { required: true, message: 'Please enter tenant name' },
              { min: 3, message: 'Name must be at least 3 characters' },
            ]}
          >
            <Input placeholder="e.g., Acme Corporation" />
          </Form.Item>

          <Form.Item
            name="slug"
            label="Slug (URL identifier)"
            rules={[
              { required: true, message: 'Please enter slug' },
              {
                pattern: /^[a-z0-9-]+$/,
                message:
                  'Slug must contain only lowercase letters, numbers, and hyphens',
              },
            ]}
          >
            <Input placeholder="e.g., acme-corporation" disabled />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea
              rows={3}
              placeholder="Brief description of the tenant"
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="Status"
            rules={[{ required: true, message: 'Please select status' }]}
          >
            <Select>
              <Option value="active">
                <Tag color="green">Active</Tag>
              </Option>
              <Option value="trial">
                <Tag color="blue">Trial</Tag>
              </Option>
              <Option value="suspended">
                <Tag color="orange">Suspended</Tag>
              </Option>
              <Option value="deleted">
                <Tag color="red">Deleted</Tag>
              </Option>
            </Select>
          </Form.Item>

          <Divider orientation="left">Contact Information</Divider>

          <Form.Item
            name="contact_email"
            label="Contact Email"
            rules={[
              { required: true, message: 'Please enter contact email' },
              { type: 'email', message: 'Please enter a valid email' },
            ]}
          >
            <Input placeholder="contact@example.com" />
          </Form.Item>

          <Form.Item
            name="contact_phone"
            label="Contact Phone"
            rules={[
              {
                pattern: /^[+]?[\d\s()-]+$/,
                message: 'Please enter a valid phone number',
              },
            ]}
          >
            <Input placeholder="+1 (555) 123-4567" />
          </Form.Item>

          <Divider orientation="left">Odoo Connection</Divider>

          <Form.Item
            name="odoo_url"
            label="Odoo URL"
            rules={[
              { required: true, message: 'Please enter Odoo URL' },
              { type: 'url', message: 'Please enter a valid URL' },
            ]}
          >
            <Input placeholder="https://your-odoo-instance.odoo.com" />
          </Form.Item>

          <Form.Item
            name="odoo_database"
            label="Odoo Database Name"
            rules={[{ required: true, message: 'Please enter database name' }]}
          >
            <Input placeholder="your_database" />
          </Form.Item>

          <Form.Item name="odoo_version" label="Odoo Version">
            <Select placeholder="Select Odoo version">
              <Option value="17.0">Odoo 17.0</Option>
              <Option value="16.0">Odoo 16.0</Option>
              <Option value="15.0">Odoo 15.0</Option>
              <Option value="14.0">Odoo 14.0</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="odoo_username"
            label="Odoo Username"
            rules={[{ required: true, message: 'Please enter Odoo username' }]}
          >
            <Input placeholder="admin" />
          </Form.Item>

          <Form.Item
            name="odoo_password"
            label="Odoo Password"
            tooltip="Leave blank to keep existing password"
          >
            <Input.Password placeholder="Leave blank to keep existing" />
          </Form.Item>

          <Divider orientation="left">Subscription Plan</Divider>

          <Form.Item
            name="plan_id"
            label="Subscription Plan"
            rules={[{ required: true, message: 'Please select a plan' }]}
          >
            <Select
              placeholder="Select a subscription plan"
              onChange={handlePlanChange}
              loading={plans.length === 0}
            >
              {plans.map((plan) => (
                <Option key={plan.id} value={plan.id}>
                  <Space direction="vertical" size={0}>
                    <span style={{ fontWeight: 500 }}>{plan.name}</span>
                    <span style={{ fontSize: '12px', color: '#888' }}>
                      {plan.max_requests_per_day.toLocaleString()} req/day • $
                      {plan.price_monthly}/month
                    </span>
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Divider orientation="left">Rate Limits (Optional Override)</Divider>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item
              name="max_requests_per_day"
              label="Max Requests per Day"
              style={{ flex: 1 }}
            >
              <InputNumber
                min={0}
                placeholder="Override plan limit"
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item
              name="max_requests_per_hour"
              label="Max Requests per Hour"
              style={{ flex: 1 }}
            >
              <InputNumber
                min={0}
                placeholder="Override plan limit"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Space>

          <Divider orientation="left">Advanced Settings</Divider>

          <Form.Item
            name="allowed_models"
            label="Allowed Odoo Models"
            tooltip="Specify which Odoo models this tenant can access. Leave empty for all."
          >
            <Select
              mode="tags"
              placeholder="e.g., res.partner, sale.order"
              style={{ width: '100%' }}
            >
              <Option value="res.partner">res.partner</Option>
              <Option value="sale.order">sale.order</Option>
              <Option value="product.product">product.product</Option>
              <Option value="account.move">account.move</Option>
              <Option value="stock.picking">stock.picking</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="allowed_features"
            label="Allowed Features"
            tooltip="Specify which BridgeCore features this tenant can use."
          >
            <Select
              mode="tags"
              placeholder="e.g., sync, webhooks, analytics"
              style={{ width: '100%' }}
            >
              <Option value="sync">Smart Sync</Option>
              <Option value="webhooks">Webhooks</Option>
              <Option value="analytics">Analytics</Option>
              <Option value="batch">Batch Operations</Option>
            </Select>
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="trial_ends_at" label="Trial End Date" style={{ flex: 1 }}>
              <DatePicker showTime style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="subscription_ends_at"
              label="Subscription End Date"
              style={{ flex: 1 }}
            >
              <DatePicker showTime style={{ width: '100%' }} />
            </Form.Item>
          </Space>

          <Form.Item style={{ marginTop: '32px' }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={loading}
                size="large"
              >
                Save Changes
              </Button>
              <Button size="large" onClick={() => navigate('/tenants')}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default EditTenantPage;
