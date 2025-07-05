from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://localhost:27017/")
db = client["webhook_db"]
collection = db["events"]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')

    parsed = None

    if event_type == "push":
        parsed = {
            "author": data["pusher"]["name"],
            "action": "PUSH",
            "from_branch": None,
            "to_branch": data["ref"].split("/")[-1],
            "timestamp": datetime.utcnow()
        }

    elif event_type == "pull_request":
        action = data["action"]
        if action in ["opened", "closed"]:
            merged = data["pull_request"].get("merged", False)
            if merged:
                
                parsed = {
                    "author": data["pull_request"]["user"]["login"],
                    "action": "MERGE",
                    "from_branch": data["pull_request"]["head"]["ref"],
                    "to_branch": data["pull_request"]["base"]["ref"],
                    "timestamp": datetime.utcnow()
                }
            else:
                
                parsed = {
                    "author": data["pull_request"]["user"]["login"],
                    "action": "PULL_REQUEST",
                    "from_branch": data["pull_request"]["head"]["ref"],
                    "to_branch": data["pull_request"]["base"]["ref"],
                    "timestamp": datetime.utcnow()
                }

    if parsed:
        collection.insert_one(parsed)
        return jsonify({"status": "saved"}), 200
    else:
        return jsonify({"status": "ignored"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find({}, {"_id": 0}))
    for e in events:
        e["timestamp"] = e["timestamp"].strftime("%d %B %Y - %I:%M %p UTC")
    return jsonify(events)

if __name__ == '__main__':
    app.run(port=5000, debug=True)

