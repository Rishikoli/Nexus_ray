import asyncio
import websockets
import json
import requests
import uuid

API_URL = "http://127.0.0.1:8000/api/reference/semiconductor"
WS_URL = "ws://127.0.0.1:8000/ws"

SAMPLE_PAYLOAD = {
    "wafer_id": "WAF-9982-X",
    "defect_data": {"total": 120}
}

async def verify_semiconductor():
    print(f"🔌 Connecting to WebSocket at {WS_URL}...")
    async with websockets.connect(WS_URL) as websocket:
        print("✅ WebSocket Connected!")
        
        # Trigger Workflow
        print(f"🚀 Triggering Semiconductor Workflow via API...")
        response = requests.post(API_URL, json=SAMPLE_PAYLOAD)
        
        if response.status_code != 200:
            print(f"❌ API Request Failed: {response.text}")
            return
            
        data = response.json()
        workflow_id = data.get("workflow_id")
        print(f"✅ Workflow Started! ID: {workflow_id}")
        print("👀 Listening for events...")

        start_time = asyncio.get_event_loop().time()
        event_count = 0
        
        while True:
            try:
                # Set timeout for receiving messages
                message = await asyncio.wait_for(websocket.recv(), timeout=40.0)
                data = json.loads(message)
                
                # Filter for our workflow
                if data.get("workflow_id") == workflow_id:
                    event_type = data.get("type")
                    payload = data.get("payload", {})
                    
                    agent_name = payload.get('agent', 'System')
                    msg_text = payload.get('message', '')
                    print(f"📨 [{event_type}] {agent_name}: {msg_text}")
                    event_count += 1
                    
                    if event_type == "workflow_complete":
                        print("🎉 Workflow Complete Event Received!")
                        print(f"✅ VERIFICATION SUCCESS: Received {event_count} events.")
                        result = data.get("result", {})
                        print(f"🔍 Root Cause: {result.get('root_cause')}")
                        print(f"🛠️ Optimizations: {len(result.get('optimizations', {}).get('optimizations', []))}")
                        break
                    
                    if event_type == "workflow_failed":
                        print("❌ Workflow Failed Event Received!")
                        print(f"Error: {data.get('error')}")
                        break

            except asyncio.TimeoutError:
                print("⚠️ Timeout waiting for events. No data received for 40s.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(verify_semiconductor())
