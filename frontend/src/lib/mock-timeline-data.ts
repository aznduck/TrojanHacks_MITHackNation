import { AgentEvent } from './types';

// Mock events for testing the Agent Timeline
export const mockTimelineEvents: AgentEvent[] = [
  // Clone stage events
  {
    type: 'status',
    stage: 'clone',
    message: 'Starting repository clone',
    ts: 1704067200, // 2024-01-01 00:00:00
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'clone',
    message: 'Cloning from GitHub repository',
    ts: 1704067205,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'clone',
    message: 'Clone completed successfully',
    ts: 1704067220,
    deployment_id: 'mock-deployment-123'
  },

  // Architect stage events
  {
    type: 'status',
    stage: 'architect',
    message: 'Starting project analysis',
    ts: 1704067225,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'architect',
    subtype: 'llm_start',
    model: 'claude-3-sonnet',
    ts: 1704067230,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'architect',
    subtype: 'tool_start',
    tool: 'file_analyzer',
    ts: 1704067235,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'architect',
    subtype: 'tool_end',
    tool: 'file_analyzer',
    ts: 1704067240,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'architect',
    subtype: 'llm_end',
    model: 'claude-3-sonnet',
    ts: 1704067250,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'architect',
    message: 'Generated Dockerfile and CI/CD configuration',
    ts: 1704067255,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'architect',
    message: 'Architecture analysis completed',
    ts: 1704067260,
    deployment_id: 'mock-deployment-123'
  },

  // Dependencies stage events
  {
    type: 'status',
    stage: 'deps',
    message: 'Starting dependency analysis',
    ts: 1704067265,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'deps',
    subtype: 'tool_start',
    tool: 'package_scanner',
    ts: 1704067270,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'deps',
    message: 'Analyzing package.json dependencies',
    ts: 1704067275,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'deps',
    message: 'Found 2 security vulnerabilities',
    ts: 1704067280,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'deps',
    subtype: 'tool_end',
    tool: 'package_scanner',
    ts: 1704067285,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'deps',
    message: 'Dependency analysis completed',
    ts: 1704067290,
    deployment_id: 'mock-deployment-123'
  },

  // Tests stage events
  {
    type: 'status',
    stage: 'tests',
    message: 'Starting test suite execution',
    ts: 1704067295,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'tests',
    subtype: 'tool_start',
    tool: 'jest_runner',
    ts: 1704067300,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'tests',
    message: 'Running unit tests',
    ts: 1704067305,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'tests',
    message: 'Running integration tests',
    ts: 1704067320,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'tests',
    subtype: 'tool_end',
    tool: 'jest_runner',
    ts: 1704067335,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'tests',
    message: 'All tests passed (24/24)',
    ts: 1704067340,
    deployment_id: 'mock-deployment-123'
  },

  // Deployment stage events
  {
    type: 'status',
    stage: 'deployment',
    message: 'Starting Vercel deployment',
    ts: 1704067345,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'deployment',
    subtype: 'tool_start',
    tool: 'vercel_cli',
    ts: 1704067350,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'deployment',
    message: 'Building application',
    ts: 1704067355,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'deployment',
    message: 'Uploading build artifacts',
    ts: 1704067380,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'deployment',
    subtype: 'tool_end',
    tool: 'vercel_cli',
    ts: 1704067400,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'deployment',
    message: 'Deployment successful',
    ts: 1704067405,
    deployment_id: 'mock-deployment-123',
    deployment_url: 'https://my-app-abc123.vercel.app'
  },

  // Monitor stage events
  {
    type: 'status',
    stage: 'incident_monitor',
    message: 'Starting health monitoring',
    ts: 1704067410,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'incident_monitor',
    subtype: 'tool_start',
    tool: 'health_checker',
    ts: 1704067415,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'incident_monitor',
    message: 'Checking application health',
    ts: 1704067420,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'incident_monitor',
    message: 'All health checks passed',
    ts: 1704067440,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'trace',
    stage: 'incident_monitor',
    subtype: 'tool_end',
    tool: 'health_checker',
    ts: 1704067445,
    deployment_id: 'mock-deployment-123'
  },
  {
    type: 'status',
    stage: 'incident_monitor',
    message: 'Monitoring setup completed',
    ts: 1704067450,
    deployment_id: 'mock-deployment-123'
  },

  // Final stage events
  {
    type: 'status',
    stage: 'final',
    message: 'Pipeline completed successfully',
    ts: 1704067455,
    deployment_id: 'mock-deployment-123',
    status: 'succeeded'
  }
];

// Mock events for a failed deployment
export const mockFailedTimelineEvents: AgentEvent[] = [
  // Clone stage (successful)
  {
    type: 'status',
    stage: 'clone',
    message: 'Starting repository clone',
    ts: 1704067200,
    deployment_id: 'mock-failed-456'
  },
  {
    type: 'status',
    stage: 'clone',
    message: 'Clone completed successfully',
    ts: 1704067220,
    deployment_id: 'mock-failed-456'
  },

  // Architect stage (successful)
  {
    type: 'status',
    stage: 'architect',
    message: 'Starting project analysis',
    ts: 1704067225,
    deployment_id: 'mock-failed-456'
  },
  {
    type: 'status',
    stage: 'architect',
    message: 'Architecture analysis completed',
    ts: 1704067260,
    deployment_id: 'mock-failed-456'
  },

  // Dependencies stage (successful)
  {
    type: 'status',
    stage: 'deps',
    message: 'Starting dependency analysis',
    ts: 1704067265,
    deployment_id: 'mock-failed-456'
  },
  {
    type: 'status',
    stage: 'deps',
    message: 'Dependency analysis completed',
    ts: 1704067290,
    deployment_id: 'mock-failed-456'
  },

  // Tests stage (failed)
  {
    type: 'status',
    stage: 'tests',
    message: 'Starting test suite execution',
    ts: 1704067295,
    deployment_id: 'mock-failed-456'
  },
  {
    type: 'status',
    stage: 'tests',
    message: 'Running unit tests',
    ts: 1704067305,
    deployment_id: 'mock-failed-456'
  },
  {
    type: 'status',
    stage: 'tests',
    message: 'Test failed: Authentication module tests failing',
    ts: 1704067320,
    deployment_id: 'mock-failed-456',
    error: 'TypeError: Cannot read property of undefined'
  },

  // Final stage (failed)
  {
    type: 'status',
    stage: 'final',
    message: 'Pipeline failed during testing phase',
    ts: 1704067325,
    deployment_id: 'mock-failed-456',
    status: 'failed',
    error: 'Test suite execution failed'
  }
];
