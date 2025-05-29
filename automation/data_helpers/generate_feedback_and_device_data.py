import json
from datetime import datetime, timedelta
import random
import os

# Realistic comments to randomly choose from
comments_pool = [
    "Staff was very kind and professional.",
    "Wait time was too long for a routine check-up.",
    "The doctor answered all my questions clearly.",
    "I felt rushed during my consultation.",
    "Great service and very clean facility.",
    "Confused by some of the billing details.",
    "Nurse was helpful and friendly.",
    "Appointment was delayed but care was good.",
    "Check-in process was fast and efficient.",
    "I didn’t feel like my concerns were taken seriously."
]

# Generate data
feedback_data = []
device_data = []

for i in range(50):
    patient_id = f"p{1000 + i}"
    visit_id = f"v{5000 + i}"
    timestamp = (datetime.utcnow() - timedelta(minutes=random.randint(1, 1440))).isoformat() + "Z"

    feedback_data.append({
        "patient_id": patient_id,
        "visit_id": visit_id,
        "timestamp": timestamp,
        "satisfaction_score": random.randint(1, 5),
        "comments": random.choice(comments_pool)
    })

    device_data.append({
        "patient_id": patient_id,
        "timestamp": timestamp,
        "heart_rate": random.randint(60, 120),
        "steps": random.randint(0, 20000),
        "device_id": f"fitbit-{random.randint(1000, 9999)}"
    })

# Ensure folder exists
os.makedirs("data/raw/feedback", exist_ok=True)

# Write files
with open("data/raw/feedback/feedback.json", "w") as f:
    json.dump(feedback_data, f, indent=2)

with open("data/raw/feedback/device_data.json", "w") as f:
    json.dump(device_data, f, indent=2)

print("Clean and realistic feedback + device JSON files generated.")
