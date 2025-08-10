import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const deploymentId = searchParams.get('deployment_id');
    
    if (!deploymentId) {
      return NextResponse.json(
        { error: 'deployment_id is required' },
        { status: 400 }
      );
    }

    const backendUrl = process.env.DEPLOYMENT_BACKEND_URL || 'http://localhost:8000';
    
    // Get events from the backend
    const eventsResponse = await fetch(`${backendUrl}/replay/${deploymentId}`);
    if (!eventsResponse.ok) {
      throw new Error(`Backend responded with status: ${eventsResponse.status}`);
    }
    
    const events = await eventsResponse.json();
    
    // Get agent outputs from the backend
    const outputsResponse = await fetch(`${backendUrl}/deployment/${deploymentId}/outputs`);
    let agentOutputs = {};
    
    if (outputsResponse.ok) {
      agentOutputs = await outputsResponse.json();
    }
    
    return NextResponse.json({
      ok: true,
      events: events || [],
      agent_outputs: agentOutputs
    });
    
  } catch (error) {
    console.error('Error fetching agent events:', error);
    return NextResponse.json(
      { 
        ok: false,
        error: 'Failed to fetch agent events',
        events: [],
        agent_outputs: {}
      },
      { status: 500 }
    );
  }
}
