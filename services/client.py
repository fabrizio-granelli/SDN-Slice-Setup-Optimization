import requests
import time

while True:
    res = requests.get("http://10.0.0.2:8080")
    
    print(f"Got response code {res.status_code} in {res.elapsed}")

    time.sleep(1)