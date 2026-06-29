import React, { useState, useEffect } from 'react';
import { Card, Badge, List, Tag, Button, Space, Empty, Tooltip, Typography, Spin } from 'antd';
import {
  BellOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { alertService } from '@/services/alert.service';
import { Alert, AlertCounts, AlertSeverity } from '@/types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Text } = Typography;

const AlertWidget: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [counts, setCounts] = useState<AlertCounts | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    fetchData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchData();
    }, 30000);

    return () => clearInterval(interval);
  }, [refreshKey]);

  const fetchData = async () => {
    try {
      const [alertsData, countsData] = await Promise.all([
        alertService.getAlerts({ active_only: true, limit: 5 }),
        alertService.getAlertCounts(),
      ]);
      // Filter out invalid alerts
      const validAlerts = (alertsData || []).filter(a => a && a.id);
      setAlerts(validAlerts);
      setCounts(countsData || { critical: 0, error: 0, warning: 0, info: 0, total: 0 });
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      setAlerts([]);
      setCounts({ critical: 0, error: 0, warning: 0, info: 0, total: 0 });
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: AlertSeverity) => {
    const icons = {
      critical: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
      error: <ExclamationCircleOutlined style={{ color: '#ff7a45' }} />,
      warning: <WarningOutlined style={{ color: '#faad14' }} />,
      info: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
    };
    return icons[severity] || icons.info;
  };

  const getSeverityColor = (severity: AlertSeverity): string => {
    const colors: Record<AlertSeverity, string> = {
      critical: 'red',
      error: 'orange',
      warning: 'gold',
      info: 'blue',
    };
    return colors[severity] || 'default';
  };

  const handleAcknowledge = async (alertId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await alertService.acknowledgeAlert(alertId);
      setRefreshKey((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to acknowledge:', error);
    }
  };

  const totalActive = counts?.total || 0;
  const hasCritical = (counts?.critical || 0) > 0;

  return (
    <Card
      title={
        <Space>
          <BellOutlined />
          <span>Active Alerts</span>
          {totalActive > 0 && (
            <Badge
              count={totalActive}
              style={{ backgroundColor: hasCritical ? '#ff4d4f' : '#faad14' }}
            />
          )}
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="Refresh">
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={() => setRefreshKey((prev) => prev + 1)}
              loading={loading}
            />
          </Tooltip>
          <Button type="link" size="small" onClick={() => navigate('/alerts')}>
            View All
          </Button>
        </Space>
      }
      style={{
        height: '100%',
        borderLeft: hasCritical
          ? '4px solid #ff4d4f'
          : totalActive > 0
          ? '4px solid #faad14'
          : undefined,
      }}
      styles={{
        body: {
          padding: '0 16px 16px 16px',
          maxHeight: 350,
          overflowY: 'auto',
        },
      }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin />
        </div>
      ) : alerts.length === 0 ? (
        <Empty
          image={<CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />}
          description={
            <Text type="secondary">No active alerts. System is healthy!</Text>
          }
          style={{ padding: '32px 0' }}
        />
      ) : (
        <List
          dataSource={alerts}
          renderItem={(alert) => (
            <List.Item
              style={{
                padding: '12px 0',
                borderBottom: '1px solid #f0f0f0',
                cursor: 'pointer',
              }}
              onClick={() => navigate('/alerts')}
              actions={[
                <Tooltip title="Acknowledge" key="ack">
                  <Button
                    type="text"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={(e) => handleAcknowledge(alert.id, e)}
                  />
                </Tooltip>,
              ]}
            >
                <List.Item.Meta
                avatar={getSeverityIcon(alert.severity || 'info')}
                title={
                  <Space size="small">
                    <Text
                      strong
                      style={{
                        fontSize: 13,
                        animation:
                          alert.severity === 'critical' ? 'pulse 2s infinite' : undefined,
                      }}
                    >
                      {alert.title || 'Alert'}
                    </Text>
                    <Tag color={getSeverityColor(alert.severity || 'info')} style={{ fontSize: 10 }}>
                      {(alert.severity || 'info').toUpperCase()}
                    </Tag>
                  </Space>
                }
                description={
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {dayjs(alert.created_at).fromNow()}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      )}

      {/* Summary footer */}
      {counts && totalActive > 0 && (
        <div
          style={{
            borderTop: '1px solid #f0f0f0',
            paddingTop: 12,
            marginTop: 8,
            display: 'flex',
            justifyContent: 'space-around',
          }}
        >
          {counts.critical > 0 && (
            <Tag color="red" icon={<ExclamationCircleOutlined />}>
              {counts.critical} Critical
            </Tag>
          )}
          {counts.error > 0 && (
            <Tag color="orange" icon={<ExclamationCircleOutlined />}>
              {counts.error} Error
            </Tag>
          )}
          {counts.warning > 0 && (
            <Tag color="gold" icon={<WarningOutlined />}>
              {counts.warning} Warning
            </Tag>
          )}
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </Card>
  );
};

export default AlertWidget;

