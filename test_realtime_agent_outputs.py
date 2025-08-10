#!/usr/bin/env python3
"""
Test script to verify real-time agent outputs streaming via WebSocket
"""

import requests
import json
import time
import uuid

def test_realtime_agent_outputs():
    print("🧪 Testing Real-time Agent Outputs Streaming")
    print("=" * 60)
    
    api_url = "http://localhost:8000"
    
    # Check if backend is running
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Backend is not healthy")
            return
        print("✅ Backend is running")
    except requests.exceptions.RequestException:
        print("❌ Backend is not running. Start it with: uvicorn api:app --reload")
        return
    
    print()
    print("📋 Test Instructions:")
    print("1. This will create a real deployment that streams agent outputs via WebSocket")
    print("2. Open the frontend URL that will be shown")
    print("3. Watch for agent outputs to appear in real-time as each agent completes")
    print("4. Look for the '🔴 Live' indicator next to Agent Outputs sections")
    print("5. Agent outputs should appear immediately when each agent finishes")
    print()
    
    # Create webhook payload to trigger real deployment
    webhook_payload = {
        "repository": {
            "clone_url": "file:///Users/dohan/TrojanHacks_MITHackNation/test-sample-app",
            "name": "test-realtime-outputs",
            "full_name": "test/test-realtime-outputs"
        },
        "after": "4253306446f992d1cc3395c262dd40b3f72114bb",
        "head_commit": {
            "id": "4253306446f992d1cc3395c262dd40b3f72114bb",
            "message": "Test commit for real-time agent outputs streaming",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    
    print("🚀 Triggering deployment with real-time agent outputs streaming...")
    
    try:
        webhook_response = requests.post(
            f"{api_url}/webhook/github",
            json=webhook_payload,
            timeout=30  # Increased timeout for webhook response
        )
        
        if webhook_response.status_code == 200:
            webhook_data = webhook_response.json()
            deployment_id = webhook_data.get('deployment_id')
            
            print(f"✅ Deployment started: {deployment_id}")
            print(f"🌐 Frontend URL: http://localhost:3000/monitor/{deployment_id}")
            print()
            print("🎯 OPEN THE URL NOW to watch live events streaming!")
            print("- Events will start appearing as the pipeline runs")
            print("- Agent outputs will stream in real-time as each agent completes")
            print("- Look for '🔴 Live' indicator in the Agent Outputs sections")
            print("- Each agent will have different timestamps showing real-time progress")
            print()
            print("📊 Expected sequence (watch them appear live):")
            print("1. Clone events - Repository cloning")
            print("2. Architect events - Infrastructure generation")
            print("3. Dependencies events - Security analysis")
            print("4. Tests events - Test execution")
            print("5. Deploy events - Deployment process")
            print("6. Monitor events - Health monitoring")
            print()
            print("✨ Pipeline is running in background - watch the frontend for live updates!")
            print("⏰ The pipeline will take 30-60 seconds to complete all agents.")
            
        else:
            print(f"❌ Failed to create deployment: HTTP {webhook_response.status_code}")
            print(f"Response: {webhook_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to trigger deployment: {e}")

if __name__ == "__main__":
    test_realtime_agent_outputs()
