import tkinter as tk
from tkinter import ttk
import socket, threading, requests, json, re, os, time, datetime



class KCollabApp:
    def __init__(self, root):
        print("App running ...")
        self.root = root
        self.root.geometry("1000x600")
        self.root.minsize(700, 400)
        self.root.title("K Collab")
        self.TOKEN_FILE = "kcollab_auth_token.json"
        self.tokenExpireTime = 5 * 86400 # 5 days in seconds ( 1 day = 86400 secs)

        self.bgs = {
            "bg1": "#196C38",
            "bg1_mid": "#93e7b2",
            "bg1_mid2": "#7bcf9a",
            "bg1_light": "#a3efbf",
            "bg2": "#8ddfab",
            "bg3": "#1D6F4C",
            "bg4": "#0FAE83",
            "bg5": "#2D3E50",
            "bg6": "#848786",
            "bg7": "#007bff",
        }

        

        # self.isMsgUI_init = False
        self.baseURL = "http://127.0.0.1:8000/api/"

        self.openedChatID = None

        self.mainFrame = tk.Frame(self.root, bg= self.bgs["bg6"])
        self.mainFrame.pack(fill=tk.BOTH, expand=True)

        self.authenticate()

    def authenticate(self):
        token = self.load_token()
        if token and self.updateIP(token):
            self.initMainUI()
            self.startP2PServer()
        else:
            self.initLoginUI()


    def updateIP(self, token):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.post(self.baseURL + "update_ip/", headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                self.authToken = token
                self.user_id = data.get("uID")
                self.user_name = data.get("uName")
                self.hostIP = data.get("ip")
                self.hostPort = data.get("port")

                return True
            else:
                print("Failed to update IP:", resp.json())
        except requests.exceptions.RequestException as e:
            print("Network error:", e)

        return False


# initialization events
    def initMainUI(self):

        # Navbar
        self.navbar = tk.Frame(self.mainFrame, width=50, bg=self.bgs["bg1"])
        self.navbar.pack(side=tk.LEFT, fill=tk.Y)
        self.navbar.pack_propagate(False) 

        # Hamburger button
        self.is_navbar_expanded = False
        hamburger_btn = tk.Button(
            self.navbar,
            text="☰", 
            font=('Arial', 16), 
            bg=self.navbar.cget("bg"),
            fg="white", 
            bd=0, 
            command=self.toggle_navbar
        )
        hamburger_btn.pack(pady=10, padx=5, anchor="w")

        # Navbar buttons
        navLinks = [("Dashboard", "📊"), ("Chats", "💬"), ("Tasks", "📋")]
        navLink_style = {
            'font': ('Arial', 14), 
            'bg': self.navbar.cget("bg"), 
            'fg': "white", 
            'pady': 3, 
            'bd': 0, 
            'padx': 3, 
            'anchor': "w", 
            'justify': "left",
            #"cursor":"hand2"
        }
        self.nav_buttons = []
        self.nav_icons = []        
        
        for text, icon in navLinks:
            icon_btn = tk.Button(
                self.navbar, 
                text=icon, 
                command=lambda t=text: self.handleNavlinkClick(t), 
                **navLink_style
            )
            icon_btn.pack(pady=5, padx=5)
            self.nav_icons.append(icon_btn)

            text_btn = tk.Button(
                self.navbar, 
                text=f"{icon} {text}", 
                command=lambda t=text: self.handleNavlinkClick(t), 
                **navLink_style
            )
            self.nav_buttons.append(text_btn)

        # Content area
        self.content = tk.Frame(self.mainFrame, bg="white")
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Initialize sections
        self.dashboard_frame = self.createDashboardUI()
        self.chats_frame = self.createChatsUI()
        self.tasks_frame = self.createTasksUI()

        # Show default section
        self.initDashboard()

    def initLoginUI(self):
        self.loginFrame = tk.Frame(self.mainFrame, bg="#fff", padx=30, pady=30, bd=3, relief="flat")
        self.loginFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(self.loginFrame, text="Welcome to K Collab", font=("Arial", 26, "bold"), bg=self.loginFrame.cget("bg"), fg="#1D6F4C").pack()

        tk.Label(self.loginFrame, text="Login to your account to continue.", font=('Arial', 13), bg=self.loginFrame.cget("bg"), fg="#111").pack()

        self.login_status = tk.Label(self.loginFrame, text="", fg="#b30c0c", font = ('Halvatika', 13), bg= self.loginFrame.cget("bg"))
        self.login_status.pack(pady=5)

        inputStyle = {"font": ('Arial', 12), "width": 40, "bg": self.bgs["bg1_light"], "bd": 1, "relief": "groove",}

        emailLabel = tk.Label(self.loginFrame, text="Enter Email:", font=('Arial', 13, 'bold'), bg=self.loginFrame.cget("bg"), fg="#222")
        emailLabel.pack(pady=5, anchor="w")

        self.emailInput = tk.Entry(self.loginFrame, **inputStyle)
        self.emailInput.pack(pady=5, ipadx=5, ipady=5)
        

        passwordLabel = tk.Label(self.loginFrame, text="Enter Password:", font=('Arial', 13, 'bold'), bg=self.loginFrame.cget("bg"), fg="#222")
        passwordLabel.pack(pady=5, anchor="w")

        self.passwordInput = tk.Entry(self.loginFrame, show = "*", **inputStyle)
        self.passwordInput.pack(pady=5, ipadx=5, ipady=5)

        self.loginBtn = tk.Button(self.loginFrame, text="LOGIN", font=('Arial', 13), bg=self.bgs["bg1"], fg="white", pady=10, bd=0, width= 25, command=self.handleLoginClick)
        self.loginBtn.pack(pady=20)

    def initDashboard(self):
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
    
    def initChats(self):
        self.chats_frame.pack(fill=tk.BOTH, expand=True)

    def initTasks(self):
        self.tasks_frame.pack(fill=tk.BOTH, expand=True)


#UI create events

    def createDashboardUI(self):
        """Create Dashboard UI."""
        frame = tk.Frame(self.content, bg="white")
        tk.Label(frame, text="Dashboard", font=('Arial', 24), bg="white").pack(pady=20)
        return frame


    def createChatsUI(self):
        frame = tk.Frame(self.content, bg="white")

        # chats panel 
        panelBG = self.bgs["bg1_light"]

        chatPanelFrame = tk.Frame(frame, width=350, bg=panelBG, pady=5, padx=5)
        chatPanelFrame.pack(side=tk.LEFT, fill=tk.Y)
        chatPanelFrame.pack_propagate(False)

        chatsFrameHeader = tk.Label(chatPanelFrame, text="Chats", bg= panelBG, font=('Arial', 16, 'bold')).pack(side=tk.TOP, anchor='w', padx=10)

        filterFrame = tk.Frame(chatPanelFrame, bg=panelBG, pady=5, padx=5)
        filterFrame.pack(side=tk.TOP, anchor='w' , fill=tk.X, pady=10)

        filterBtnStyle = {
            'font': ('Arial', 11),
            'bg': self.bgs["bg4"],
            'fg': "#fff",
            "activebackground": self.bgs['bg5'],
            'activeforeground': "#fff",
            'pady': 1,
            'bd': 0,
            'padx': 15,
            'cursor': 'hand2'
        }
        
        tk.Button(filterFrame, text="ALL", **filterBtnStyle).pack(side=tk.LEFT, padx=5)
        tk.Button(filterFrame, text="GROUPS", **filterBtnStyle).pack(side=tk.LEFT, padx=5)

        self.chatCanvas = tk.Canvas(chatPanelFrame, bg= panelBG)
        self.chatCanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Vertical.TScrollbar",
            background=self.bgs["bg4"],
            arrowcolor=self.bgs["bg4"],
            troughcolor=panelBG,
            arrowsize=0,
            borderwidth= 0,
            width = 3
        )
        style.map(
            "Vertical.TScrollbar",
            background=[('active', self.bgs["bg4"])],
        )

        scrollbar = ttk.Scrollbar(self.chatCanvas, orient="vertical", style="Vertical.TScrollbar", command=self.chatCanvas.yview)


        self.chatFrame = tk.Frame(self.chatCanvas, bg= panelBG, padx=5)

        canvasWindow = self.chatCanvas.create_window((0, 0), window=self.chatFrame, anchor="nw")

        self.chatCanvas.configure(yscrollcommand=scrollbar.set)
        self.chatCanvas.bind("<Configure>", lambda e: self.chatCanvas.itemconfig(canvasWindow, width = self.chatCanvas.winfo_width() - 5))
        

        self.chatFrame.bind(
            '<Configure>',
            lambda e: self.chatCanvas.config(
                scrollregion=(0,0, self.chatFrame.winfo_reqwidth(), max(self.root.winfo_height() - 100 ,self.chatFrame.winfo_reqheight()))
            )
        )
    
        self.chatCanvas.bind(
            '<Enter>',
            lambda e: scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        )
        self.chatCanvas.bind(
            '<Leave>',
            lambda e: scrollbar.pack_forget()
        )
        
        # if self.chat_cache and (time.time() - self.chat_cache_time < CACHE_EXPIRY):
        #     self.populateChat()
        # else:
        self.asyncGetRequest('chats/', self.populateChat)            
                    
        #messages panel
        self.msgPanelFrame = tk.Frame(frame, pady=5, padx=5)
        self.msgPanelFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        #default contents inside msg panel if no chat selected
        msgDefaultFrame = tk.Frame(self.msgPanelFrame)
        msgDefaultFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(msgDefaultFrame, text="K Collab", bg=msgDefaultFrame.cget('bg'), font=('Arial', 18, 'bold')).pack()

        tk.Label(msgDefaultFrame, text="Click on a chat to start messaging.", bg=msgDefaultFrame.cget('bg'), font=('Arial', 12)).pack()      

        return frame



    def createTasksUI(self):
        """Create Tasks UI."""
        frame = tk.Frame(self.content, bg="white")
        tk.Label(frame, text="Tasks Section", font=('Arial', 24), bg="white").pack(pady=20)
        return frame





#click handle events
    def handleLoginClick(self):
        def showError(msg):
            self.login_status.config(text=f"*{msg}")
            self.loginBtn.config(state="normal")
        

        self.loginBtn.config(state="disabled")

        email = self.emailInput.get().strip()
        password = self.passwordInput.get().strip()

        #input validation 
        regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}$'
        if not re.match(regex, email):
            showError("Invalid email address")            
            return
        
        elif len(password) < 4:
            showError("Password must be at least 4 characters")
            return
        
        try:
            resp = requests.post(self.baseURL + 'login/', data = {"email": email, "password": password})
            if resp.status_code == 200:
                token = resp.json().get('authToken')

                self.save_token(token)
                if self.updateIP(token):
                    self.loginFrame.destroy() # Remove login UI
                    self.initMainUI()
                else:
                    showError("An error occurred. Try again")
                
            else:
                showError(resp.json().get('error', "Login failed"))

        except Exception as e:
            showError("An error occured. Try again")
            print("Error : ", e)

    def handleNavlinkClick(self, section):
        self.clear_content()
        if section.lower() == "dashboard":
            self.initDashboard()
        elif section.lower() == "chats":
            self.initChats()
        elif section.lower() == "tasks":
            self.initTasks()
        
    def handleChatClick(self, chat_widget):
        chat_id = chat_widget.chat_id
        if self.openedChatID != chat_id:

            if hasattr(self, "activeChat"): 
                # Remove the previous active chat's bgcolor
                self.activeChat.config(bg=self.bgs["bg1_light"]) 
                [w.config(bg=self.bgs["bg1_light"]) for w in self.activeChat.winfo_children()]

            self.openedChatID = chat_id
            self.currentPeers = chat_widget.othersMembers
            metaData = chat_widget.meta
            print(chat_id)

            chat_widget.config(bg=self.bgs["bg1_mid2"]) 
            [w.config(bg=self.bgs["bg1_mid2"]) for w in chat_widget.winfo_children()]
            self.activeChat = chat_widget 


            for widget in self.msgPanelFrame.winfo_children():
                widget.destroy()
                # widget.pack_forget()


            msgP_HeaderFrame = tk.Frame(self.msgPanelFrame, bg=self.bgs["bg1_light"], padx=5, pady=10)
            msgP_HeaderFrame.pack(fill="x", side=tk.TOP)

            tk.Label(msgP_HeaderFrame, text=metaData['name'], bg=msgP_HeaderFrame.cget('bg'), font=('Arial', 11, 'bold')).pack(anchor="w")

            #msg canvas
            self.msgCanvas = tk.Canvas(self.msgPanelFrame)
            self.msgCanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            msgP_Scrollbar = ttk.Scrollbar(self.msgCanvas, orient="vertical", command=self.msgCanvas.yview)
            msgP_Scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.msgCanvas.configure(yscrollcommand=msgP_Scrollbar.set)

            self.msgsFrame = tk.Frame(self.msgCanvas, padx=10)

            msgCanvas_window = self.msgCanvas.create_window((0,0), window=self.msgsFrame, anchor="nw")

            def update_width(event):
                canvas_width = self.msgCanvas.winfo_width()
                scrollbar_width = msgP_Scrollbar.winfo_width()
                self.msgCanvas.itemconfig(msgCanvas_window, width=canvas_width- scrollbar_width -5)
            
            self.msgCanvas.bind('<Configure>', update_width)

            self.msgsFrame.bind(
                "<Configure>", 
                lambda e: self.msgCanvas.configure(
                    scrollregion= (0, 0, self.msgsFrame.winfo_reqwidth(), max(self.msgCanvas.winfo_height() -5, self.msgsFrame.winfo_reqheight()))
                )
            )
            
            msgP_HeaderFrame.after(100, lambda: self.msgCanvas.yview_moveto(1))

           
            #msg input
            msgInputFrame = tk.Frame(self.msgPanelFrame, bg=self.bgs["bg1_light"], padx=5, pady=5, height=60)
            msgInputFrame.pack(fill="x",side=tk.BOTTOM)

            self.msgInput = tk.Entry(msgInputFrame, bg="#fff", font=('Arial', 12), name = "msgInput") 
            self.msgInput.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)

            tk.Button(
                msgInputFrame, 
                text="Send", 
                bg=self.bgs['bg3'], 
                fg="#fff", 
                font=('Arial', 12),
                cursor= 'hand2',
                command= self.sendMessage
            ).pack(side=tk.RIGHT, padx=3, pady=5)


            #populate messages
            self.asyncGetRequest('chat/messages/', self.populateMsgs, data= {"chat_id": chat_id})

           


            
    def sendMessage(self):
        msgInp = self.msgInput.get()
        if msgInp != "":
            msgData = {
                "sender": self.user_name, 
                "msg": msgInp, 
                "time": datetime.datetime.now().strftime("%d-%m-%y %I:%M %p")
            }

            self.add_message(msgData, "right")

            self.msgInput.delete(0, tk.END)
            self.msgCanvas.update_idletasks()
            self.msgCanvas.yview_moveto(1)
            
            self.sendP2PMessage(msgData)
            self.saveMsg2DB(msgData, msgTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

#populate function
    def populateChat(self, chats):
            panelBG = self.bgs["bg1_light"]
        # chats = requests.get(self.baseURL + "chats/", headers={"Authorization": f"Bearer {self.authToken}"})
        
        # if chats.status_code != 200:
        #     tk.Label(self.chatFrame, bg = panelBG, text = "Error Loading Chats", fg ="red").pack(padx=5, pady=10)

        #     #reload btn
        #     tk.Button(self.chatFrame, text="Reload", command=lambda: self.reloadChats() ).pack(ipadx=5, ipady=5, pady=5, padx=5)

        # else:
            for i in chats:
                chat_id = i['id']
                meta = i.get('metaData')
                chat = tk.Frame(self.chatFrame, bg= panelBG, cursor="hand2", pady=10, padx=10)
                # chat.pack(ipady=10,ipadx=10, fill="x")
                chat.pack(fill="x")

                chat.chat_id = chat_id
                chat.meta = meta
                chat.othersMembers = i.get('members')
                
                tk.Label(chat, text=meta['name'], bg=panelBG, font=('Arial', 11)).pack(anchor="w")
                tk.Label(chat, text=meta['name'], bg=panelBG, font=('Arial', 8)).pack(anchor="w")

                chatBindings ={
                    '<MouseWheel>': lambda e: self.chatCanvas.yview_scroll(int(-1*(e.delta/120)), "units"),
                    '<Button-1>': lambda e,chat_widget = chat: self.handleChatClick(chat_widget),
                    '<Enter>': lambda e, item=chat: self.chat_MouseEnter(item),
                    '<Leave>': lambda e, item=chat: self.chat_MouseLeave(item),
                }

                for event, func in chatBindings.items():
                    chat.bind(event, func)


    def populateMsgs(self, messages):
        for msg in messages :
            sender_id = msg['sender']['id']

            if sender_id != self.user_id:
                sender = msg['sender']['name'] 
                align = 'left'
            else:
                sender ='You'
                align = 'right'

            self.add_message({"sender":sender, "msg":msg['content'], "time": msg['timestamp']}, align)



# helper events
    def clear_content(self):
        for widget in self.content.winfo_children():
            # widget.destroy()
            widget.pack_forget()

    def load_token(self):
        """Load token from a local file"""
        if not os.path.exists(self.TOKEN_FILE):
            return None

        with open(self.TOKEN_FILE, "r") as f:
            data = json.load(f)
        token = data.get("token")
        timestamp = data.get("timestamp", 0)

        if time.time() - timestamp > self.tokenExpireTime:
            os.unlink(self.TOKEN_FILE) # Delete expired token file
            return None
        return token

    def save_token(self, token):
        """Save token to a local file"""
        token_data = {"token": token, "timestamp": time.time()}
        with open(self.TOKEN_FILE, "w") as f:
            json.dump(token_data, f)

    def toggle_navbar(self):
        """Expand or collapse navbar."""
        if self.is_navbar_expanded:
            self.navbar.configure(width=50)
            for btn in self.nav_buttons:
                btn.pack_forget()
            for icon in self.nav_icons:
                icon.pack(pady=5, padx=5)
        else:
            self.navbar.configure(width=200)
            for icon in self.nav_icons:
                icon.pack_forget()
            for btn in self.nav_buttons:
                btn.pack(pady=5, padx=5, fill=tk.X)
        self.is_navbar_expanded = not self.is_navbar_expanded

    def chat_MouseEnter(self, chat_widget):
        if not hasattr(self, "activeChat") or chat_widget != self.activeChat:
            chat_widget.config(bg=self.bgs["bg1_mid"])
            [w.config(bg=self.bgs["bg1_mid"])  for w in chat_widget.winfo_children()]

    def chat_MouseLeave(self, chat_widget):
        if not hasattr(self, "activeChat") or chat_widget != self.activeChat:
            chat_widget.config(bg=self.bgs["bg1_light"])
            [w.config(bg=self.bgs["bg1_light"])  for w in chat_widget.winfo_children()]


    def add_message(self, data, align):
        sender = "You" if data['sender'] == self.user_name else data['sender']
        msg = tk.Frame(self.msgsFrame, bg="white")
        msg.pack(pady=5, padx=10, anchor="e" if align == "right" else "w")

        bubble_frame = tk.Frame(
            msg,
            bg="#dcf8c6" if align == "right" else "#e6e6e6",
            bd=1,
            relief="solid"
        )
        bubble_frame.pack(side="right" if align == "right" else "left")

        sender_label = tk.Label(bubble_frame, text=sender, bg=bubble_frame.cget("bg"), fg="blue", font=('Arial', 8), padx=5)
        sender_label.pack(anchor="w")

        message_label = tk.Label(
            bubble_frame, 
            text=data["msg"], 
            bg=bubble_frame.cget("bg"), 
            font=('Arial', 11), 
            padx=5, 
            justify="left"
        )
        message_label.pack(anchor="w")

        time_label = tk.Label(bubble_frame, text=data["time"], bg=bubble_frame.cget("bg"), fg="#374747", font=('Arial', 8, 'italic'), padx=5)
        time_label.pack(anchor="e")

        def update_message_label_wraplength(event = None):
            if message_label and message_label.winfo_exists():
                message_label.config(wraplength= self.msgPanelFrame.winfo_width()*0.7)
                self.msgCanvas.yview_moveto(1)


        def scroll_handler(event):
            self.msgCanvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        bubble_frame.bind("<MouseWheel>", scroll_handler)
        sender_label.bind("<MouseWheel>", scroll_handler)
        message_label.bind("<MouseWheel>", scroll_handler)
        time_label.bind("<MouseWheel>", scroll_handler)
        self.msgsFrame.bind("<MouseWheel>", scroll_handler)

        self.root.bind("<Configure>", update_message_label_wraplength)

        update_message_label_wraplength()
    

    def asyncGetRequest(self, endpoint:str, callback, data = None):
        def run():
            header =  {"Authorization": f"Bearer {self.authToken}"}
            try:
                resp = requests.get(self.baseURL + endpoint, headers = header, data = data)
                if resp.status_code == 200:
                    respData = resp.json()
                    root.after(0, lambda: callback(respData))
            except requests.exceptions.RequestException as e:
                print("Request error:", e)
        
        threading.Thread(target=run, daemon=True).start()

       

#RELOAD function 
    def reloadChats(self):
        print("reloaded")
        self.clear_content()

        self.chats_frame = self.createChatsUI()
        self.initChats()


#p2p functions

    def startP2PServer(self):
        # self.activeConnections = {}  # Dictionary to store connections (thread-safe)
        # self.connections_lock = threading.Lock() # Lock for activeConnections
        def serverThread():
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.hostIP, self.hostPort))
            server_socket.listen(100)  # allow multiple connections. 1 = 1 connection, 100 = 100 connections
            print(f"P2P Server listening on {self.hostIP}:{self.hostPort}")

            while True:  # Accept connections in a loop
                try:
                    client_socket, addr = server_socket.accept()
                    # with self.connections_lock:
                    #     self.activeConnections[addr] = client_socket
                    print(f"Connection from {addr}")
                    threading.Thread(target=self.receivePeerMessage, args=(client_socket, addr), daemon=True).start()
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    # break # or handle the error appropriately
                    continue
            # server_socket.close() # Close when the loop breaks
        
        threading.Thread(target=serverThread, daemon= True).start()

    def receivePeerMessage(self, clientSocket, addr):
        while True:
            try:
                data = clientSocket.recv(1024).decode()
                if data:
                    try:
                        message = json.loads(data) # Parse JSON
                        self.add_message(message, "left")
                        self.msgCanvas.update_idletasks()
                        self.msgCanvas.yview_moveto(1)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON from {addr}: {data}")
                else:
                    break  # Client disconnected
            except Exception as e:
                print(f"Error receiving from {addr}: {e}")
                break

        # with self.connections_lock:
        #     del self.activeConnections[addr]
        clientSocket.close()

    def sendP2PMessage(self, data):
        jsonMsg = json.dumps(data)
        
        # with self.connections_lock:
        for peer in self.currentPeers:
            ip = peer['ip_addr']
            port = peer['port']
            try:
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientSocket.connect((ip,port))
                clientSocket.sendall(jsonMsg.encode())
                clientSocket.close()
            except Exception as e:
                print(f"Failed to send message", e)

#DB write functions

    def saveMsg2DB(self, msgData, msgTime):
        data = {
            "chat_id" : self.openedChatID,
            "content" : msgData.get("msg"),
            "timestamp" : msgTime
        }
        resp = requests.post(f"{self.baseURL}chat/messages/", headers= {"Authorization": f"Bearer {self.authToken}"}, data = data)
        print("msg saved to DB")


if __name__ == "__main__":
    root = tk.Tk()
    app = KCollabApp(root)
    root.mainloop()