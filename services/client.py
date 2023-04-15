import requests
import time

while True:
    res = requests.get("http://10.0.0.2:8080")
    print(res.text)

    time.sleep(1)