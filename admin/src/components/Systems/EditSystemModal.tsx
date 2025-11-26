/**
 * Modal for editing an existing system connection
 */
import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Switch,
  Button,
  message,
  Alert,
  Space
} from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import systemService from '../../services/system.service';
import { TenantSystem, TenantSystemUpdate } from '../../types';

interface EditSystemModalProps {
  visible: boolean;
  tenantId: string;
  system: TenantSystem;
  onCancel: () => void;
  onSuccess: () => void;
}

const EditSystemModal: React.FC<EditSystemModalProps> = ({
  visible,
  tenantId,
  system,
  onCancel,
  onSuccess
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    if (visible && system) {
      form.setFieldsValue({
        ...system.connection_config,
        is_active: system.is_active,
        is_primary: system.is_primary
      });
      setTestResult(null);
    }
  }, [visible, system]);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await systemService.testExistingConnection(tenantId, system.id);
      setTestResult({
        success: result.success,
        message: result.success
          ? `✅ Connection successful!`
          : `❌ ${result.error}`
      });
    } catch (error) {
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

      // Extract connection config fields based on system type
      const systemType = system.external_system?.system_type;
      let connectionConfig: Record<string, any> = {};

      if (systemType === 'odoo') {
        connectionConfig = {
          url: values.url,
          database: values.database,
          username: values.username,
          ...(values.password && { password: values.password })
        };
      } else if (systemType === 'moodle') {
        connectionConfig = {
          url: values.url,
          token: values.token,
          service: values.service
        };
      }

      const data: TenantSystemUpdate = {
        connection_config: connectionConfig,
        is_active: values.is_active,
        is_primary: values.is_primary
      };

      await systemService.updateTenantSystem(tenantId, system.id, data);
      message.success('System updated successfully');
      onSuccess();
    } catch (error: any) {
      if (error.errorFields) return;
      message.error(error.response?.data?.detail || 'Failed to update system');
    } finally {
      setLoading(false);
    }
  };

  const renderFields = () => {
    const systemType = system.external_system?.system_type;

    if (systemType === 'odoo') {
      return (
        <>
          <Form.Item label="Odoo URL" name="url" rules={[{ required: true }]}>
            <Input placeholder="https://your-odoo.com" />
          </Form.Item>
          <Form.Item label="Database" name="database" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Username" name="username" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item
            label="Password"
            name="password"
            help="Leave empty to keep current password"
          >
            <Input.Password placeholder="Enter new password (optional)" />
          </Form.Item>
        </>
      );
    }

    if (systemType === 'moodle') {
      return (
        <>
          <Form.Item label="Moodle URL" name="url" rules={[{ required: true }]}>
            <Input placeholder="https://lms.yourschool.com" />
          </Form.Item>
          <Form.Item
            label="Web Services Token"
            name="token"
            rules={[{ required: true }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item label="Service Name" name="service">
            <Input placeholder="moodle_mobile_app" />
          </Form.Item>
        </>
      );
    }

    return null;
  };

  return (
    <Modal
      title={`Edit ${system.external_system?.name} Connection`}
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button key="test" onClick={handleTestConnection} loading={testing}>
          Test Connection
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          Save Changes
        </Button>
      ]}
      width={600}
    >
      <Form form={form} layout="vertical">
        {renderFields()}

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
      </Form>
    </Modal>
  );
};

export default EditSystemModal;
