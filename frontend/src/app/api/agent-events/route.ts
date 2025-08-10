import { NextRequest, NextResponse } from 'next/server';

// In-memory storage for events (in production, use Redis or database)
const deploymentEvents: Record<string, any[]> = {};
const deploymentAgentOutputs: Record<string, Record<string, any>> = {};

/**
 * POST /api/agent-events
 * Receives agent events from the backend via HTTP callbacks
 */
export async function POST(request: NextRequest) {
  try {
    const event = await request.json();
    const deploymentId = event.deployment_id;
    
    // Log received event for debugging
    console.log('📨 Received HTTP callback event:', {
      deployment_id: deploymentId,
      type: event.type,
      stage: event.stage,
      message: event.message,
      has_agent_outputs: !!event.agent_outputs
    });
    
    if (!deploymentId) {
      console.error('❌ Event missing deployment_id:', event);
      return NextResponse.json(
        { ok: false, error: 'deployment_id is required', received_event: event },
        { status: 400 }
      );
    }
    
    // Store the event
    if (!deploymentEvents[deploymentId]) {
      deploymentEvents[deploymentId] = [];
    }
    deploymentEvents[deploymentId].push(event);
    
    // Store agent outputs if present
    // Check for agent_outputs field (direct) or delta field (from trace events)
    let agentOutputsData = null;
    if (event.agent_outputs) {
      agentOutputsData = event.agent_outputs;
    } else if (event.type === 'trace' && event.subtype === 'agent_delta' && event.delta) {
      agentOutputsData = event.delta;
    }
    
    if (agentOutputsData) {
      if (!deploymentAgentOutputs[deploymentId]) {
        deploymentAgentOutputs[deploymentId] = {};
      }
      // Merge delta data with existing outputs for this stage
      if (!deploymentAgentOutputs[deploymentId][event.stage]) {
        deploymentAgentOutputs[deploymentId][event.stage] = {};
      }
      deploymentAgentOutputs[deploymentId][event.stage] = {
        ...deploymentAgentOutputs[deploymentId][event.stage],
        ...agentOutputsData
      };
      console.log('💾 Stored agent outputs for stage:', event.stage, deploymentAgentOutputs[deploymentId][event.stage]);
    } else {
      console.log('⚠️ No agent_outputs or delta in event for stage:', event.stage, 'type:', event.type);
    }
    
    // Log the received event for debugging
    console.log('📨 Received agent event via HTTP callback:', {
      type: event.type,
      stage: event.stage,
      deployment_id: deploymentId,
      timestamp: event.ts || event.timestamp,
      message: event.message,
      has_agent_outputs: !!event.agent_outputs
    });
    
    return NextResponse.json({
      ok: true,
      message: 'Agent event received successfully',
      event_type: event.type,
      stage: event.stage,
      deployment_id: deploymentId
    });
    
  } catch (error) {
    console.error('❌ Error processing agent event:', error);
    
    return NextResponse.json(
      { 
        ok: false, 
        error: 'Failed to process agent event',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 400 }
    );
  }
}

/**
 * GET /api/agent-events?deployment_id=xxx
 * Get stored events for a deployment
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const deploymentId = searchParams.get('deployment_id');
  
  if (!deploymentId) {
    return NextResponse.json({
      ok: true,
      message: 'Agent events endpoint is ready',
      endpoint: '/api/agent-events',
      methods: ['POST', 'GET'],
      usage: 'GET /api/agent-events?deployment_id=xxx'
    });
  }
  
  const events = deploymentEvents[deploymentId] || [];
  const agentOutputs = deploymentAgentOutputs[deploymentId] || {};
  
  return NextResponse.json({
    ok: true,
    deployment_id: deploymentId,
    events,
    agent_outputs: agentOutputs,
    event_count: events.length
  });
}
