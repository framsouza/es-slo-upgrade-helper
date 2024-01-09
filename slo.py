import http.client
import base64
import json
import os

# ES credentials
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
kibana_endpoint = os.getenv('KIBANA_ENDPOINT')

conn = http.client.HTTPSConnection(kibana_endpoint, 9243)

credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode("ascii")
authorization_header = f"Basic {encoded_credentials}"

headers = {
    'kbn-xsrf': "oui",
    'Authorization': authorization_header,
    'Content-Type': 'application/json'
}

conn.request("GET", "/s/default/api/observability/slos/_definitions?includeOutdatedOnly=1", headers=headers)
res = conn.getresponse()
data = res.read().decode("utf-8")

slo_definitions = json.loads(data)
slo_list = slo_definitions.get("results", [])

slo_ids = [slo['id'] for slo in slo_list]

# Iterate through each SLO ID and call the reset API
for slo_id in slo_ids:
    conn.request("POST", f"/s/default/api/observability/slos/{slo_id}/_reset", headers=headers)
    reset_res = conn.getresponse()
    reset_data = reset_res.read().decode("utf-8")
    print(f"Reset SLO ID {slo_id}: {reset_res.status} - {reset_data}")

conn.close()

