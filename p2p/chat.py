import socket, threading, requests, json

API_BASE_URL = "http://127.0.0.1:8000/api/"
# AUTH_TOKEN = "65b67abb4be0dfe127869a7cf2f340a648b131f6" #abi@kcollab.in
# AUTH_TOKEN = "b160214a21b93e14c9556f203c8408ad68fbdb07" #abinash@kcnnect.in
AUTH_TOKEN = "d9da67c9c2325aa2db96c6b889f2390ea9dda75c" #abi@ab.in

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

def updateUserIP(hostIP, hostPort):
    data ={
        "ip_address": hostIP,
        "port": hostPort
    }

    resp = requests.post(API_BASE_URL + 'update_ip/', headers=headers, data = data)

    print(resp.json())
    if resp.status_code == 200:
        print("IP updated")
    else:
        print("Failed to update ip")


def getChatDetails(chat_id):

    print(chat_id)

    response = requests.get(API_BASE_URL + f'chat/messages/?chat_id={chat_id}', headers= headers)

    if response.status_code == 200:
        members = response.json()['chat']['members']
        
        messages = response.json()['messages']
        peers = []
        for member in members:
            peers.append((member["ip_addr"], member["port"], member["name"]))
        
        msgFormated = []
        for message in messages:
            msgFormated.append((message['sender']['name'], message['content']))
        return [peers, msgFormated]
    else:
        print("Failed to get Chat Member")
        return []

def getChatsID():
    resp = requests.get(API_BASE_URL + 'chats/', headers= headers)
    if resp.status_code == 200:
        chats = resp.json()
        chat_ids = []
        for chat in chats:
            chat_ids.append(chat['id'])

        return chat_ids
    else:
        print("Failed to fetch chats")
        return []

def receive_messages(sock):
    while True:
        try:
            message,_ = sock.recvfrom(1024)
            print("\nReceived:", message.decode())
        except:
            break

def send_messages(sock, peers):
    while True:
        message = input("You: ")
        for peer in peers:
            sock.sendto(message.encode(), peer)

def main():
    host_ip = input("Enter your IP: ")
    host_port = 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host_ip, host_port))

    updateUserIP(host_ip, host_port)

    chatIDs = getChatsID()
    options = [idx for idx,_ in enumerate(chatIDs)]
    while True:
        chatId = int(input(f"Select chat: (Options: {options} : "))
        if chatId not in options:
            print("Invalid choice")
        else:
            break

    peers,messages = getChatDetails(chatIDs[chatId])

    print(peers)

    for msg in messages:
        print(f"{msg[0]}: {msg[1]}")
    
    receive_thread = threading.Thread(target=receive_messages, args=(sock,))
    receive_thread.start()
    
    send_thread = threading.Thread(target=send_messages, args=(sock, peers))
    send_thread.start()
    
if __name__ == "__main__":
    main()
