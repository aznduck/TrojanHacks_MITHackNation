#!/usr/bin/env python3
"""
Test script to create a deployment with agent outputs for frontend testing
"""

import requests
import json
import time

def test_agent_outputs():
    print("🧪 Testing Agent Outputs Feature")
    print("=" * 50)
    
    # API endpoint
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
    
    # Create a mock webhook payload
    webhook_payload = {
        "repository": {
            "clone_url": "file:///Users/dohan/TrojanHacks_MITHackNation/test-sample-app",
            "name": "test-agent-outputs",
            "full_name": "test/test-agent-outputs"
        },
        "after": "4253306446f992d1cc3395c262dd40b3f72114bb",
        "head_commit": {
            "id": "4253306446f992d1cc3395c262dd40b3f72114bb",
            "message": "Test commit for agent outputs",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    
    print("🚀 Triggering deployment via webhook...")
    
    try:
        # Trigger webhook (no signature needed for testing)
        webhook_response = requests.post(
            f"{api_url}/webhook/github",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Give it time to complete
        )
        
        if webhook_response.status_code != 200:
            print(f"❌ Webhook failed: {webhook_response.status_code}")
            print(f"Response: {webhook_response.text}")
            return
            
        result = webhook_response.json()
        deployment_id = result.get("deployment_id")
        
        if not deployment_id:
            print("❌ No deployment_id returned")
            return
            
        print(f"✅ Deployment created: {deployment_id}")
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Check if agent outputs were stored
        print("🔍 Checking for agent outputs...")
        outputs_response = requests.get(f"{api_url}/deployment/{deployment_id}/outputs")
        
        if outputs_response.status_code == 200:
            outputs = outputs_response.json()
            print("✅ Agent outputs found!")
            print(f"📊 Available agents: {list(outputs.keys())}")
            
            # Show sample of what's available
            for agent, data in outputs.items():
                if data:
                    print(f"  - {agent}: {len(data)} outputs")
                    for key in list(data.keys())[:6]:  # Show first 3 keys
                        print(f"    • {key}")
        else:
            print(f"❌ No agent outputs found (HTTP {outputs_response.status_code})")
            
        print("\n🎯 To test in frontend:")
        print(f"1. Go to: http://localhost:3000/replay/{deployment_id}")
        print("2. Click on any event in the timeline")
        print("3. Look for 'Agent Outputs' section in event details")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_agent_outputs()
