/**
 * Component to display and manage systems connected to a tenant
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Tooltip,
  Modal,
  message,
  Badge,
  Typography
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  StarOutlined,
  StarFilled
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import systemService from '../../services/system.service';
import { TenantSystem, ExternalSystem } from '../../types';
import AddSystemModal from './AddSystemModal';
import EditSystemModal from './EditSystemModal';
import moment from 'moment';

const { Text, Paragraph } = Typography;

interface TenantSystemsListProps {
  tenantId: string;
}

const TenantSystemsList: React.FC<TenantSystemsListProps> = ({ tenantId }) => {
  const [systems, setSystems] = useState<TenantSystem[]>([]);
  const [loading, setLoading] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState<TenantSystem | null>(null);
  const [testingConnectionId, setTestingConnectionId] = useState<string | null>(null);

  useEffect(() => {
    loadSystems();
  }, [tenantId]);

  const loadSystems = async () => {
    setLoading(true);
    try {
      const data = await systemService.getTenantSystems(tenantId, false);
      setSystems(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to load systems');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (connectionId: string) => {
    setTestingConnectionId(connectionId);
    try {
      const result = await systemService.testExistingConnection(tenantId, connectionId);
      if (result.success) {
        message.success({
          content: (
            <div>
              <div>✅ Connection successful!</div>
              {result.system_info && (
                <div style={{ fontSize: '12px', marginTop: '4px' }}>
                  {result.system_info.sitename && <div>Site: {result.system_info.sitename}</div>}
                  {result.system_info.version && <div>Version: {result.system_info.version}</div>}
                </div>
              )}
            </div>
          ),
          duration: 5
        });
        loadSystems(); // Refresh to update connection status
      } else {
        message.error({
          content: (
            <div>
              <div>❌ Connection failed</div>
              {result.error && (
                <div style={{ fontSize: '12px', marginTop: '4px', color: '#ff4d4f' }}>
                  {result.error}
                </div>
              )}
            </div>
          ),
          duration: 7
        });
      }
    } catch (error: any) {
      message.error('Failed to test connection');
    } finally {
      setTestingConnectionId(null);
    }
  };

  const handleSetPrimary = async (connectionId: string) => {
    try {
      await systemService.setPrimarySystem(tenantId, connectionId);
      message.success('Primary system updated successfully');
      loadSystems();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to set primary system');
    }
  };

  const handleDelete = (system: TenantSystem) => {
    Modal.confirm({
      title: 'Delete System Connection',
      content: `Are you sure you want to delete the connection to ${system.external_system?.name}?`,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: async () => {
        try {
          await systemService.deleteTenantSystem(tenantId, system.id);
          message.success('System connection deleted successfully');
          loadSystems();
        } catch (error: any) {
          message.error(error.response?.data?.detail || 'Failed to delete system');
        }
      },
    });
  };

  const getSystemTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      odoo: '🏢',
      moodle: '🎓',
      sap: '💼',
      salesforce: '☁️',
      dynamics: '🔷'
    };
    return icons[type] || '🔌';
  };

  const getConnectionStatusTag = (system: TenantSystem) => {
    if (!system.is_active) {
      return <Tag color="default">Inactive</Tag>;
    }

    if (system.last_successful_connection) {
      const lastSuccess = moment(system.last_successful_connection);
      const hoursSince = moment().diff(lastSuccess, 'hours');

      if (hoursSince < 24) {
        return (
          <Tooltip title={`Last connected: ${lastSuccess.fromNow()}`}>
            <Tag color="green" icon={<CheckCircleOutlined />}>
              Connected
            </Tag>
          </Tooltip>
        );
      }
    }

    if (system.connection_error) {
      return (
        <Tooltip title={system.connection_error}>
          <Tag color="red" icon={<CloseCircleOutlined />}>
            Error
          </Tag>
        </Tooltip>
      );
    }

    return <Tag color="orange">Unknown</Tag>;
  };

  const columns: ColumnsType<TenantSystem> = [
    {
      title: 'System',
      key: 'system',
      render: (_, record) => (
        <Space>
          <span style={{ fontSize: '20px' }}>
            {getSystemTypeIcon(record.external_system?.system_type || '')}
          </span>
          <div>
            <div>
              <Text strong>{record.external_system?.name}</Text>
              {record.is_primary && (
                <Tag color="gold" icon={<StarFilled />} style={{ marginLeft: 8 }}>
                  Primary
                </Tag>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.external_system?.system_type.toUpperCase()}
            </Text>
          </div>
        </Space>
      ),
      width: 250,
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, record) => getConnectionStatusTag(record),
      width: 130,
    },
    {
      title: 'Connection Info',
      key: 'info',
      render: (_, record) => (
        <div>
          {record.connection_config.url && (
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>URL:</Text>{' '}
              <Text style={{ fontSize: '12px' }}>{record.connection_config.url}</Text>
            </div>
          )}
          {record.connection_config.database && (
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>DB:</Text>{' '}
              <Text style={{ fontSize: '12px' }}>{record.connection_config.database}</Text>
            </div>
          )}
          {record.last_connection_test && (
            <div>
              <Text type="secondary" style={{ fontSize: '11px' }}>
                Last tested: {moment(record.last_connection_test).fromNow()}
              </Text>
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Test Connection">
            <Button
              type="text"
              icon={<SyncOutlined spin={testingConnectionId === record.id} />}
              onClick={() => handleTestConnection(record.id)}
              loading={testingConnectionId === record.id}
              size="small"
            />
          </Tooltip>

          {!record.is_primary && (
            <Tooltip title="Set as Primary">
              <Button
                type="text"
                icon={<StarOutlined />}
                onClick={() => handleSetPrimary(record.id)}
                size="small"
              />
            </Tooltip>
          )}

          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedSystem(record);
                setEditModalVisible(true);
              }}
              size="small"
            />
          </Tooltip>

          <Tooltip title="Delete">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
              size="small"
            />
          </Tooltip>
        </Space>
      ),
      width: 180,
    },
  ];

  return (
    <Card
      title={
        <Space>
          <span>🔌 Connected Systems</span>
          <Badge count={systems.length} style={{ backgroundColor: '#52c41a' }} />
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setAddModalVisible(true)}
        >
          Add System
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={systems}
        rowKey="id"
        loading={loading}
        pagination={false}
        locale={{
          emptyText: (
            <div style={{ padding: '40px 0' }}>
              <Text type="secondary">
                No systems connected yet. Click "Add System" to connect external systems like Moodle, SAP, or Salesforce.
              </Text>
            </div>
          ),
        }}
      />

      <AddSystemModal
        visible={addModalVisible}
        tenantId={tenantId}
        onCancel={() => setAddModalVisible(false)}
        onSuccess={() => {
          setAddModalVisible(false);
          loadSystems();
        }}
      />

      {selectedSystem && (
        <EditSystemModal
          visible={editModalVisible}
          tenantId={tenantId}
          system={selectedSystem}
          onCancel={() => {
            setEditModalVisible(false);
            setSelectedSystem(null);
          }}
          onSuccess={() => {
            setEditModalVisible(false);
            setSelectedSystem(null);
            loadSystems();
          }}
        />
      )}
    </Card>
  );
};

export default TenantSystemsList;
