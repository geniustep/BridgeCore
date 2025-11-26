/**
 * Modal for adding a new system connection to a tenant
 */
import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Select,
  Input,
  Switch,
  Button,
  Space,
  message,
  Alert,
  Divider,
  Spin
} from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import systemService from '../../services/system.service';
import { ExternalSystem, SystemType, TenantSystemCreate } from '../../types';

const { Option } = Select;
const { TextArea } = Input;

interface AddSystemModalProps {
  visible: boolean;
  tenantId: string;
  onCancel: () => void;
  onSuccess: () => void;
}

const AddSystemModal: React.FC<AddSystemModalProps> = ({
  visible,
  tenantId,
  onCancel,
  onSuccess
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [availableSystems, setAvailableSystems] = useState<ExternalSystem[]>([]);
  const [selectedSystemType, setSelectedSystemType] = useState<SystemType | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    if (visible) {
      loadAvailableSystems();
      form.resetFields();
      setSelectedSystemType(null);
      setTestResult(null);
    }
  }, [visible]);

  const loadAvailableSystems = async () => {
    try {
      const systems = await systemService.getAllSystems(true);
      setAvailableSystems(systems);
    } catch (error) {
      message.error('Failed to load available systems');
    }
  };

  const handleSystemTypeChange = (systemId: string) => {
    const system = availableSystems.find(s => s.id === systemId);
    if (system) {
      setSelectedSystemType(system.system_type);
      const template = systemService.getConfigTemplate(system.system_type);
      form.setFieldsValue({ connection_config: template });
    }
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const values = form.getFieldsValue();
      const config = values.connection_config || {};

      const result = await systemService.testConnection({
        system_type: selectedSystemType!,
        connection_config: config
      });

      setTestResult({
        success: result.success,
        message: result.success
          ? `✅ Connection successful! ${result.system_info?.sitename || ''}`
          : `❌ Connection failed: ${result.error}`
      });
    } catch (error: any) {
      setTestResult({
        success: false,
        message: '❌ Connection test failed'
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      setLoading(true);

      const data: TenantSystemCreate = {
        tenant_id: tenantId,
        system_id: values.system_id,
        connection_config: values.connection_config || {},
        is_active: values.is_active !== false,
        is_primary: values.is_primary || false,
        custom_config: values.custom_config ? JSON.parse(values.custom_config) : null
      };

      await systemService.addTenantSystem(tenantId, data);
      message.success('System added successfully');
      onSuccess();
    } catch (error: any) {
      if (error.errorFields) {
        // Validation error
        return;
      }
      message.error(error.response?.data?.detail || 'Failed to add system');
    } finally {
      setLoading(false);
    }
  };

  const renderConnectionFields = () => {
    if (!selectedSystemType) return null;

    switch (selectedSystemType) {
      case 'odoo':
        return (
          <>
            <Form.Item
              label="Odoo URL"
              name={['connection_config', 'url']}
              rules={[{ required: true, message: 'Please enter Odoo URL' }]}
            >
              <Input placeholder="https://your-odoo.com" />
            </Form.Item>

            <Form.Item
              label="Database"
              name={['connection_config', 'database']}
              rules={[{ required: true, message: 'Please enter database name' }]}
            >
              <Input placeholder="production" />
            </Form.Item>

            <Form.Item
              label="Username"
              name={['connection_config', 'username']}
              rules={[{ required: true, message: 'Please enter username' }]}
            >
              <Input placeholder="admin" />
            </Form.Item>

            <Form.Item
              label="Password"
              name={['connection_config', 'password']}
              rules={[{ required: true, message: 'Please enter password' }]}
            >
              <Input.Password placeholder="••••••••" />
            </Form.Item>
          </>
        );

      case 'moodle':
        return (
          <>
            <Form.Item
              label="Moodle URL"
              name={['connection_config', 'url']}
              rules={[{ required: true, message: 'Please enter Moodle URL' }]}
              help="Your Moodle site URL (e.g., https://lms.school.com)"
            >
              <Input placeholder="https://lms.yourschool.com" />
            </Form.Item>

            <Form.Item
              label="Web Services Token"
              name={['connection_config', 'token']}
              rules={[{ required: true, message: 'Please enter web services token' }]}
              help="Generate this token in Moodle: Site Administration → Plugins → Web Services → Manage Tokens"
            >
              <Input.Password placeholder="Enter Moodle web services token" />
            </Form.Item>

            <Form.Item
              label="Service Name"
              name={['connection_config', 'service']}
              initialValue="moodle_mobile_app"
            >
              <Input placeholder="moodle_mobile_app" />
            </Form.Item>
          </>
        );

      case 'sap':
        return (
          <>
            <Form.Item
              label="SAP URL"
              name={['connection_config', 'url']}
              rules={[{ required: true, message: 'Please enter SAP URL' }]}
            >
              <Input placeholder="https://your-sap.com" />
            </Form.Item>

            <Form.Item
              label="Client"
              name={['connection_config', 'client']}
              rules={[{ required: true, message: 'Please enter client' }]}
            >
              <Input placeholder="100" />
            </Form.Item>

            <Form.Item
              label="Username"
              name={['connection_config', 'username']}
              rules={[{ required: true, message: 'Please enter username' }]}
            >
              <Input placeholder="username" />
            </Form.Item>

            <Form.Item
              label="Password"
              name={['connection_config', 'password']}
              rules={[{ required: true, message: 'Please enter password' }]}
            >
              <Input.Password placeholder="••••••••" />
            </Form.Item>
          </>
        );

      default:
        return (
          <Alert
            message="System configuration not available"
            description="This system type is coming soon."
            type="info"
            showIcon
          />
        );
    }
  };

  return (
    <Modal
      title="🔌 Add External System"
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          key="test"
          onClick={handleTestConnection}
          loading={testing}
          disabled={!selectedSystemType}
        >
          Test Connection
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleSubmit}
          disabled={!selectedSystemType}
        >
          Add System
        </Button>
      ]}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          is_active: true,
          is_primary: false
        }}
      >
        <Form.Item
          label="System Type"
          name="system_id"
          rules={[{ required: true, message: 'Please select a system' }]}
        >
          <Select
            placeholder="Select system type"
            onChange={handleSystemTypeChange}
            size="large"
          >
            {availableSystems.map(system => (
              <Option key={system.id} value={system.id}>
                <Space>
                  <span>
                    {system.system_type === 'odoo' && '🏢'}
                    {system.system_type === 'moodle' && '🎓'}
                    {system.system_type === 'sap' && '💼'}
                    {system.system_type === 'salesforce' && '☁️'}
                  </span>
                  <span>{system.name}</span>
                </Space>
              </Option>
            ))}
          </Select>
        </Form.Item>

        {selectedSystemType && (
          <>
            <Divider />
            {renderConnectionFields()}

            <Divider />

            <Form.Item label="Active" name="is_active" valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item label="Set as Primary" name="is_primary" valuePropName="checked">
              <Switch />
            </Form.Item>

            {testResult && (
              <Alert
                message={testResult.message}
                type={testResult.success ? 'success' : 'error'}
                icon={testResult.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </>
        )}
      </Form>
    </Modal>
  );
};

export default AddSystemModal;
