import threading, socket, json, time

HOST = "127.0.0.5"
PORT = 5050


serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, PORT))

def sendMsg2Peers(peers, msg):
    for peer in peers:
        try:
            peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peerSocket.connect((peer[0], peer[1]))
            peerSocket.send(msg.encode())
            peerSocket.close()
        except Exception as e:
            print(f"Error sending message to {peer}: {e}")

def receiveMsg():
    while True:
        try:
            data = serverSocket.recv(1024).decode()
            if data:
                try:
                    message = json.loads(data) # Parse JSON
                    print(message)
                except json.JSONDecodeError:
                    print(f"Invalid JSON: {data}")
            else:
                break  # Client disconnected
        except Exception as e:
            print(f"Error receiving message: {e}")
            break 