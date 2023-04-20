# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys

class WebServer(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.wfile.write(bytes("UNITN " * 100, "utf-8"))


def main(hostname: str):
    port = 8080
    
    webServer = HTTPServer((hostname, port), WebServer)
    
    print(f'Server started http://{hostname}:{port}')

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()



if __name__ == "__main__":     
    # Parse arguments
    if len(sys.argv) < 2:
        exit()
    hostname = sys.argv[1]

    main(hostname)