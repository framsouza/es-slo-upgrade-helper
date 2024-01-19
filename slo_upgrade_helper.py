import http.client
import base64
import json
import os

username = os.getenv('ES_USERNAME')
password = os.getenv('ES_PASSWORD')
kibana_endpoint = os.getenv('KIBANA_ENDPOINT')
kibana_space_names = os.getenv('KIBANA_SPACE_NAMES', '').split(',')
kibana_port = os.getenv('KIBANA_PORT', 9243)

for space_name in kibana_space_names:
    conn = http.client.HTTPSConnection(kibana_endpoint, kibana_port)

    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode("ascii")
    authorization_header = f"Basic {encoded_credentials}"

    headers = {
        'kbn-xsrf': "oui",
        'Authorization': authorization_header,
        'Content-Type': 'application/json'
    }

    try:
        total_slos = []
        page = 1
        while len(total_slos) < 5000:
            url = f"/s/{space_name}/api/observability/slos/_definitions?includeOutdatedOnly=true&perPage=1000&page={page}"
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()

            # Check for authentication error
            if res.status == 401:
                raise Exception("Authentication error. Check your credentials.")

            data = res.read().decode("utf-8")
            print(data)

            slo_definitions = json.loads(data)
            slo_list = slo_definitions.get("results", [])
            total_slos.extend(slo_list)

            if len(slo_list) < 1000:
                break

            page += 1

    except Exception as e:
        print(f"Error: {str(e)}")
        conn.close()
        continue

    conn.close()

    if not total_slos:
        print(f"No outdated SLOs found in Space '{space_name}'")
    else:
        print(f"Outdated SLOs found in Space '{space_name}': {len(total_slos)}")
        for slo in total_slos:
            print(slo['name'])
            slo_id = slo['id']
            conn = http.client.HTTPSConnection(kibana_endpoint, 9243)
            conn.request("POST", f"/s/{space_name}/api/observability/slos/{slo_id}/_reset", headers=headers)
            reset_res = conn.getresponse()
            reset_data = reset_res.read().decode("utf-8")
            print(f"Reset SLO ID {slo_id} in Space '{space_name}': {reset_res.status} - {reset_data}")
            conn.close()

