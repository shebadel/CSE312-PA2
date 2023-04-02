import socketserver
from hw1 import MyTCPHandler

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000
    print("working", flush = True)

    server1 = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    server1.serve_forever()