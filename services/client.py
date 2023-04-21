import requests
import time
import sys
import pickle


def main(target_srv: str) -> None:

    while True:
        try:
            # Get target srv ip address
            server_ip = ''
            with open('/home/services.obj', 'rb') as file:
                services = pickle.load(file)
                server_ip = services[target_srv]

            # Send HTTP request
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