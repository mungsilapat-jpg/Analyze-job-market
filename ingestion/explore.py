import requests
import json

url = "https://remotive.com/api/remote-jobs"
params = {"category": "data", "limit": 5}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
data = response.json()

jobs = data["jobs"]
print("จำนวนงานที่ได้:", len(jobs))
print("ฟิลด์ที่มี:", list(jobs[0].keys()))
print()

# ดูตัวอย่างงานแรกแบบเต็ม (ตัด description ให้สั้นลง)
first = dict(jobs[0])
first["description"] = first["description"][:200] + "..."
print(json.dumps(first, indent=2, ensure_ascii=False))