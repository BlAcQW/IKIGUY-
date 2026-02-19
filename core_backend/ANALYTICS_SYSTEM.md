# Analytics and Health Monitoring System

## Overview

The Analytics and Health Monitoring System provides comprehensive real-time analytics and health monitoring for automation workflows, including VAPI voice agents, N8N workflows, integrations, custom tools, and campaigns. The system tracks performance metrics, costs, and health indicators to ensure optimal automation performance.

## Architecture

### Core Components

1. **Analytics Service** (`backend/services/analytics_service.py`)
   - Comprehensive analytics data processing using MongoDB aggregation pipelines
   - Real-time metrics collection and storage
   - Cost analytics across all integrated services
   - Performance tracking and reporting

2. **Automation Health Service** (`backend/services/automation_health_service.py`)
   - Real-time health monitoring for automation components
   - Component-level health checks with configurable intervals
   - Health scoring algorithms
   - Automated alerting for critical issues

3. **Analytics API Routes** (`backend/routes/analytics.py`)
   - RESTful endpoints for analytics data retrieval
   - Dashboard data aggregation
   - Service-specific analytics (VAPI, N8N, integrations)
   - Cost and usage analytics

4. **Health Monitoring API Routes** (`backend/routes/automation_health.py`)
   - Component registration and management
   - Health status monitoring and updates
   - Real-time health dashboards
   - Health metrics and analytics

## Features

### Analytics Features

#### 1. Overview Analytics
- **Endpoint**: `GET /analytics/overview`
- **Description**: Comprehensive analytics overview across all services
- **Metrics**: Total automations, calls, workflows, costs, success rates

#### 2. Automation Analytics
- **Endpoint**: `GET /analytics/automations/{automation_id}`
- **Description**: Detailed analytics for specific automations
- **Metrics**: Execution count, success rate, average response time, cost breakdown

#### 3. VAPI Analytics
- **Endpoint**: `GET /analytics/vapi`
- **Description**: Voice AI analytics and call tracking
- **Metrics**: Call volume, success rates, average call duration, cost per call

#### 4. N8N Analytics
- **Endpoint**: `GET /analytics/n8n`
- **Description**: Workflow execution monitoring
- **Metrics**: Workflow runs, success rates, execution times, error analysis

#### 5. Cost Analytics
- **Endpoint**: `GET /analytics/costs`
- **Description**: Cost tracking across all services
- **Metrics**: Total costs, cost by service, cost trends, budget tracking

#### 6. Service Analytics
- **Endpoint**: `GET /analytics/services/{service_name}`
- **Description**: Service-specific metrics
- **Metrics**: Usage patterns, performance metrics, error rates

### Health Monitoring Features

#### 1. Component Registration
- **Endpoint**: `POST /automation-health/components/register`
- **Description**: Register automation components for health monitoring
- **Component Types**: VAPI agents, N8N workflows, integrations, custom tools

#### 2. Real-Time Health Checks
- **Endpoint**: `GET /automation-health/components/{component_id}/check`
- **Description**: Trigger immediate health checks
- **Health Levels**: Healthy, Warning, Critical, Unknown

#### 3. Automation Health Status
- **Endpoint**: `GET /automation-health/automations/{automation_id}/status`
- **Description**: Overall health status for automations
- **Metrics**: Component health summary, health score (0-100), alerts

#### 4. Health Dashboard
- **Endpoint**: `GET /automation-health/dashboard`
- **Description**: Comprehensive health dashboard
- **Features**: Status distribution, recent alerts, automation summaries

#### 5. Continuous Monitoring
- **Endpoints**:
  - `POST /automation-health/monitoring/start`
  - `POST /automation-health/monitoring/stop`
- **Description**: Start/stop background health monitoring
- **Features**: Configurable check intervals, automated health tracking

## Database Schema

### Analytics Collections

#### `analytics_data`
```javascript
{
  "_id": ObjectId,
  "automation_id": String,
  "tenant_id": String,
  "service_name": String,       // "vapi", "n8n", "integration", etc.
  "metric_type": String,        // "execution", "cost", "performance"
  "metric_name": String,        // "call_duration", "success_rate", etc.
  "value": Number,
  "metadata": Object,
  "timestamp": DateTime,
  "date_bucket": String         // "2024-01-15" for daily aggregation
}
```

#### `automation_configs`
```javascript
{
  "_id": ObjectId,
  "automation_id": String,
  "tenant_id": String,
  "name": String,
  "type": String,               // "voice", "workflow", "integration"
  "status": String,             // "active", "paused", "stopped"
  "components": Array,          // Component IDs
  "created_at": DateTime,
  "updated_at": DateTime,
  "metadata": Object
}
```

### Health Monitoring Collections

#### `monitored_components`
```javascript
{
  "_id": ObjectId,
  "component_id": String,
  "component_type": String,     // "vapi_agent", "n8n_workflow", etc.
  "automation_id": String,
  "tenant_id": String,
  "metadata": Object,
  "status": String,             // "healthy", "warning", "critical"
  "registered_at": DateTime,
  "last_checked": DateTime,
  "check_enabled": Boolean
}
```

#### `automation_health`
```javascript
{
  "_id": ObjectId,
  "component_id": String,
  "component_type": String,
  "status": String,             // "healthy", "warning", "critical", "unknown"
  "response_time": Number,      // In seconds
  "error_message": String,
  "metadata": Object,
  "checked_at": DateTime
}
```

#### `health_history`
```javascript
{
  "_id": ObjectId,
  "component_id": String,
  "component_type": String,
  "status": String,
  "response_time": Number,
  "error_message": String,
  "metadata": Object,
  "checked_at": DateTime
}
```

## Health Check Configuration

### Component Types and Check Intervals

| Component Type | Check Interval | Response Time Thresholds |
|----------------|----------------|-------------------------|
| VAPI Agent     | 30 seconds     | Warning: 1s, Critical: 3s |
| N8N Workflow   | 60 seconds     | Warning: 5s, Critical: 15s |
| Integration    | 120 seconds    | Warning: 2s, Critical: 10s |
| Custom Tool    | 180 seconds    | Warning: 3s, Critical: 10s |
| Automation     | 60 seconds     | Warning: 5s, Critical: 20s |

### Health Status Levels

1. **Healthy** (Green)
   - All components responding within acceptable time limits
   - No errors detected
   - All services operational

2. **Warning** (Yellow)
   - Components responding but slower than optimal
   - Non-critical errors detected
   - Service degradation possible

3. **Critical** (Red)
   - Components not responding or timing out
   - Critical errors preventing operation
   - Service unavailable

4. **Unknown** (Gray)
   - No recent health data available
   - Component not yet checked
   - Monitoring disabled

## Health Scoring Algorithm

The health score is calculated using a weighted average:

```python
def calculate_health_score(status_counts):
    total = sum(status_counts.values())
    if total == 0:
        return 0.0

    score = (
        status_counts["healthy"] * 1.0 +
        status_counts["warning"] * 0.6 +
        status_counts["critical"] * 0.0 +
        status_counts["unknown"] * 0.3
    ) / total

    return round(score * 100, 1)
```

## Integration with Services

### VAPI Integration

The system integrates with VAPI services to monitor:
- Agent availability and response times
- Call success rates and durations
- Real-time call analytics
- Cost tracking per call

### N8N Integration

Monitors N8N workflows by:
- Checking workflow execution status
- Tracking execution times and success rates
- Monitoring workflow health via N8N API
- Alerting on workflow failures

### Custom Tools Integration

For custom tools registered in the system:
- Health checks via HTTP endpoints
- Response time monitoring
- Error rate tracking
- Performance analytics

### Integration Services

Monitors all integrated services including:
- External API health checks
- Service availability monitoring
- Response time tracking
- Error rate analysis

## Usage Examples

### Registering a Component for Health Monitoring

```python
import requests

# Register a VAPI agent
registration_data = {
    "component_id": "vapi_agent_123",
    "component_type": "vapi_agent",
    "automation_id": "automation_456",
    "tenant_id": "tenant_789",
    "metadata": {
        "vapi_config": {
            "agent_id": "agent_123",
            "base_url": "https://api.vapi.ai"
        }
    }
}

response = requests.post(
    "https://api.ailabsafrica.com/automation-health/components/register",
    json=registration_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Getting Automation Health Status

```python
# Get health status for an automation
automation_id = "automation_456"
response = requests.get(
    f"https://api.ailabsafrica.com/automation-health/automations/{automation_id}/status",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

health_status = response.json()
print(f"Overall Status: {health_status['overall_status']}")
print(f"Health Score: {health_status['health_score']}")
print(f"Components: {len(health_status['components'])}")
```

### Getting Analytics Overview

```python
# Get analytics overview
response = requests.get(
    "https://api.ailabsafrica.com/analytics/overview",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

analytics = response.json()
print(f"Total Automations: {analytics['summary']['total_automations']}")
print(f"Total Costs: ${analytics['summary']['total_costs']}")
print(f"Success Rate: {analytics['summary']['overall_success_rate']}%")
```

## Frontend Integration

### Health Indicators in Automation Displays

The system provides real-time health indicators that can be displayed in automation UIs:

```javascript
// Example React component for health indicator
function HealthIndicator({ automationId }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      const response = await fetch(
        `/automation-health/automations/${automationId}/status`
      );
      const data = await response.json();
      setHealth(data);
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, [automationId]);

  if (!health) return <div>Loading...</div>;

  const statusColor = {
    healthy: 'green',
    warning: 'yellow',
    critical: 'red',
    unknown: 'gray'
  }[health.overall_status];

  return (
    <div className={`health-indicator ${statusColor}`}>
      <div className="status">{health.overall_status}</div>
      <div className="score">Score: {health.health_score}</div>
      <div className="components">{health.total_components} components</div>
    </div>
  );
}
```

### Analytics Dashboard Components

```javascript
// Example analytics dashboard component
function AnalyticsDashboard({ tenantId }) {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      const response = await fetch('/analytics/overview');
      const data = await response.json();
      setAnalytics(data);
    };

    fetchAnalytics();
  }, []);

  return (
    <div className="analytics-dashboard">
      <div className="metrics-grid">
        <MetricCard
          title="Total Automations"
          value={analytics?.summary?.total_automations || 0}
        />
        <MetricCard
          title="Success Rate"
          value={`${analytics?.summary?.overall_success_rate || 0}%`}
        />
        <MetricCard
          title="Total Costs"
          value={`$${analytics?.summary?.total_costs || 0}`}
        />
        <MetricCard
          title="Active Calls"
          value={analytics?.summary?.active_calls || 0}
        />
      </div>

      <div className="charts">
        <TrendChart data={analytics?.trends} />
        <CostBreakdownChart data={analytics?.cost_breakdown} />
      </div>
    </div>
  );
}
```

## Monitoring and Alerting

### Automated Alerts

The system can be configured to send alerts when:
- Component health status changes to warning or critical
- Response times exceed thresholds
- Error rates increase significantly
- Costs exceed budget limits

### Integration with External Monitoring

The health monitoring system can integrate with external monitoring tools:
- Webhooks for alert notifications
- Metrics export to Prometheus/Grafana
- Integration with PagerDuty/Slack for alerts

## Best Practices

### Component Registration

1. Register all automation components for comprehensive monitoring
2. Provide detailed metadata for better diagnostics
3. Use descriptive component IDs for easy identification
4. Enable monitoring for all production automations

### Health Monitoring

1. Set appropriate check intervals based on component criticality
2. Configure realistic response time thresholds
3. Monitor health dashboards regularly
4. Investigate and resolve warning states quickly

### Analytics Usage

1. Review analytics regularly to identify trends
2. Monitor costs to stay within budget
3. Use performance metrics to optimize automations
4. Track success rates to ensure quality

### Performance Optimization

1. Use MongoDB indexes for efficient queries
2. Implement data retention policies for historical data
3. Cache frequently accessed analytics data
4. Monitor system resource usage

## Troubleshooting

### Common Issues

1. **Component Not Showing Health Data**
   - Verify component is registered correctly
   - Check component metadata configuration
   - Ensure monitoring is enabled
   - Review health service logs

2. **Analytics Data Missing**
   - Confirm analytics collection is enabled
   - Check MongoDB connection
   - Verify data pipeline configuration
   - Review timestamp configurations

3. **High Response Times**
   - Check network connectivity
   - Review service performance
   - Optimize database queries
   - Consider caching strategies

4. **Health Monitoring Not Working**
   - Verify monitoring service is started
   - Check component configurations
   - Review background task logs
   - Confirm database connectivity

## Security Considerations

1. **Authentication**: All endpoints require proper authentication
2. **Authorization**: Tenant-based access control
3. **Data Privacy**: Analytics data is tenant-isolated
4. **Secure Storage**: Health data stored in encrypted MongoDB
5. **API Security**: Rate limiting and input validation

## Future Enhancements

1. **Machine Learning**: Predictive health monitoring using ML models
2. **Advanced Analytics**: More sophisticated analytics and reporting
3. **Real-time Dashboards**: WebSocket-based real-time updates
4. **Mobile Apps**: Mobile applications for monitoring on-the-go
5. **Integration Marketplace**: Enhanced integration with third-party tools