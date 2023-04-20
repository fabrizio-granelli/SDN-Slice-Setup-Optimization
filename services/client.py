import requests
import time
import sys


def main(server_ip: str) -> None:

    while True:
        try:
            res = requests.get(f'http://{server_ip}:8080', timeout=5)
            print(f'Got response code {res.status_code} in {res.elapsed}')
        except requests.exceptions.Timeout:
            print('Request timed out')
        except Exception as ex:
            print(ex)

        time.sleep(1)


if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        exit()

    main(sys.argv[1])