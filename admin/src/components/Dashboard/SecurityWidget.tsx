import React, { useState, useEffect } from 'react';
import { Card, Space, Statistic, Row, Col, Tag, Typography, Spin, Button, Tooltip } from 'antd';
import {
  SafetyOutlined,
  StopOutlined,
  WarningOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ipBlockService } from '@/services/ipblock.service';
import { IPBlockStats } from '@/types';

const { Text } = Typography;

const SecurityWidget: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<IPBlockStats | null>(null);

  useEffect(() => {
    fetchStats();

    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const data = await ipBlockService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch security stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getReasonLabel = (reason: string): string => {
    const labels: Record<string, string> = {
      rate_limit_abuse: 'Rate Limit',
      brute_force: 'Brute Force',
      suspicious_activity: 'Suspicious',
      security_threat: 'Security',
      manual_block: 'Manual',
      spam: 'Spam',
    };
    return labels[reason] || reason;
  };

  const hasBlocks = stats && stats.active_blocks > 0;
  const hasRecent = stats && stats.blocked_last_24h > 0;

  return (
    <Card
      title={
        <Space>
          <SafetyOutlined />
          <span>Security Overview</span>
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="Refresh">
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={fetchStats}
              loading={loading}
            />
          </Tooltip>
          <Button type="link" size="small" onClick={() => navigate('/security/ip-blocks')}>
            Manage
          </Button>
        </Space>
      }
      style={{
        height: '100%',
        borderLeft: hasRecent ? '4px solid #ff4d4f' : hasBlocks ? '4px solid #faad14' : undefined,
      }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin />
        </div>
      ) : stats ? (
        <>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Statistic
                title="Active IP Blocks"
                value={stats.active_blocks}
                valueStyle={{ color: stats.active_blocks > 0 ? '#ff4d4f' : '#52c41a' }}
                prefix={<StopOutlined />}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Blocked (24h)"
                value={stats.blocked_last_24h}
                valueStyle={{ color: stats.blocked_last_24h > 0 ? '#faad14' : '#52c41a' }}
                prefix={<WarningOutlined />}
              />
            </Col>
          </Row>

          {Object.keys(stats.by_reason || {}).length > 0 && (
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Block Reasons:
              </Text>
              <div style={{ marginTop: 8 }}>
                {Object.entries(stats.by_reason).map(([reason, count]) => (
                  <Tag
                    key={reason}
                    color={
                      reason === 'brute_force' || reason === 'security_threat'
                        ? 'red'
                        : reason === 'rate_limit_abuse'
                        ? 'orange'
                        : 'default'
                    }
                    style={{ marginBottom: 4 }}
                  >
                    {getReasonLabel(reason)}: {count}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {stats.active_blocks === 0 && (
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <SafetyOutlined style={{ fontSize: 32, color: '#52c41a' }} />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">No blocked IPs. System is clean!</Text>
              </div>
            </div>
          )}
        </>
      ) : (
        <Text type="secondary">Failed to load security stats</Text>
      )}
    </Card>
  );
};

export default SecurityWidget;

