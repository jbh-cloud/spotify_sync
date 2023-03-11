from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import threading
import time
class MessageServer(BaseHTTPRequestHandler):
    message = ""

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        message = MessageServer.message
        self.response =""
        html = f"""
        <html>
            <body>
                <h1>{message}</h1>
                <form method="post">
                    <input type="text" name="input_text">
                    <input type="submit" value="Submit">
                </form>
            </body>
        </html>
        """
        self.wfile.write(html.encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        input_text = params['input_text'][0]
        self.response = input_text
        self.send_response(301)
        self.send_header('Location', '/')
        self.end_headers()

class MessageWebServer:
    def __init__(self, message):
        MessageServer.message = message
        self.server = HTTPServer(('localhost', 8002), MessageServer)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.staticText = message

    def get_input_text(self):
        return self.response

    def waitInput(self):
        server  = MessageWebServer("Hello, world!")
        tempRes = server.response()
        while tempRes == self.staticText:
            time.sleep(10)
            tempRes = server.response()
        return tempRes
    
    def stop(self):
        self.server.shutdown()
        self.server.server_close()
