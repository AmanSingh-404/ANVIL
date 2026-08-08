import requests
import concurrent.futures

session_id = "rate-limit-test-session-2"
headers = {"Content-Type": "application/json", "X-Session-Id": session_id}


def send_request(i):
    r = requests.post(
        "http://localhost:5000/api/chat",
        json={"message": f"what is {i} plus {i}"},
        headers=headers,
    )
    return i, r.status_code


with concurrent.futures.ThreadPoolExecutor(max_workers=18) as executor:
    futures = [executor.submit(send_request, i) for i in range(18)]
    results = sorted((f.result() for f in futures), key=lambda x: x[0])

for i, status in results:
    print(f"Request {i+1}: status={status}")