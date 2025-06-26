import sys
import os
import time
import requests
from flask import Flask, request, jsonify
from cloudevents.http import from_http

PUBSUB_NAME = "messagepubsub"
TOPIC_NAME = "LLMOrchestrator"
APP_PORT = int(os.getenv('APP_PORT', '6004'))
WORKFLOW_HOST = os.getenv("WORKFLOW_HOST", "localhost")
WORKFLOW_PORT = os.getenv("WORKFLOW_PORT", "8004")
STATUS_URL = f"http://{WORKFLOW_HOST}:{WORKFLOW_PORT}/status"
WORKFLOW_URL = f"http://{WORKFLOW_HOST}:{WORKFLOW_PORT}/start-workflow"

app = Flask(__name__)

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    return jsonify([{
        'pubsubname': PUBSUB_NAME,
        'topic': TOPIC_NAME,
        'route': 'chat'
    }])

@app.route('/chat', methods=['POST'])
def chat_subscriber():
    event = from_http(request.headers, request.get_data())
    print("Event received:", event.data)
    return jsonify(success=True)

def wait_for_workflow(timeout_seconds=60):
    print("⏳ Waiting for workflow service to become available...")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            response = requests.get(STATUS_URL, timeout=5)
            if response.status_code == 200:
                print("✅ Workflow service is ready.")
                return True
        except requests.RequestException:
            pass
        elapsed = int(time.time() - start_time)
        print(f"🔁 Still waiting... ({elapsed}s elapsed)")
        time.sleep(10)
    print(f"❌ Timeout: Workflow service did not respond after {timeout_seconds} seconds.")
    return False

def start_workflow():
    payload = {
         "task": (
            "Start a collaborative RFP evaluation session. "
            "The ClientAgent (representing the RFP issuer) will review and challenge the SupplierAgent's proposal. "
            "For each challenge, the SupplierAgent must provide a detailed, relevant response that defends or adapts the proposal accordingly. "
            "The goal is to ensure full coverage of the RFP requirements through iterative, structured dialogue between the two agents."
        )
    }
    try:
        response = requests.post(WORKFLOW_URL, json=payload, timeout=5)
        if response.status_code == 202:
            print("✅ Workflow started")
            return True
    except requests.RequestException:
        pass
    return False

if __name__ == "__main__":
    if not wait_for_workflow():
        sys.exit(1)
    if not start_workflow():
        sys.exit(1)
    app.run(port=APP_PORT)
