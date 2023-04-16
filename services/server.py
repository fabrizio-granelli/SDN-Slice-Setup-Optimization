# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostName = "10.0.0.2"
serverPort = 8080

class WebServer(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("UNITN " * 100, "utf-8"))


if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), WebServer)
    
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")