import tkinter as tk
from tkinter import ttk
import socket, threading, requests, json, re

class App:
    def __init__(self, root):
        print("App running ...")
        self.root = root
        self.root.geometry("1000x600")
        self.title = "K Collab"
        self.root.title(self.title)

        self.bgc_primary = "#1D6F4C"
        self.bgc1 = "#2c3e50"
        self.bgc2 = "#196C38"
        self.bgc3 = "#0FAE83"

        self.baseURL = "http://127.0.0.1:8000/api/"

        # Main layout
        self.main_container = tk.Frame(self.root, bg="#848786") 
        self.main_container.pack(fill=tk.BOTH, expand=True)


        self.showLoginPage()
    
    def showLoginPage(self):
        
        self.loginFrame = tk.Frame(self.main_container, bg = "#fff", padx=30, pady=30, bd = 3, relief="flat") 
        self.loginFrame.place(anchor="c", relx=.5, rely=.5)

        tk.Label(self.loginFrame, text=f"Welcome to {self.title}", font=('Arial', 26, 'bold'), bg=self.loginFrame.cget("bg"), fg="#1D6F4C").pack()

        tk.Label(self.loginFrame, text="Login to your account to continue.", font=('Arial', 13), bg=self.loginFrame.cget("bg"), fg="#111").pack()

        self.login_status = tk.Label(self.loginFrame, text="", fg="#b30c0c", font = ('Halvatika', 13), bg= self.loginFrame.cget("bg"))
        self.login_status.pack(pady=10)

        inputStyle = {"font": ('Arial', 12), "width": 40, "bg": "#BFE3D7", "bd": 1, "relief": "groove",}

        emailFrame = tk.Frame(self.loginFrame, bg=self.loginFrame.cget("bg"))
        emailFrame.pack(pady=10)
        tk.Label(emailFrame, text="Enter Email:", font=('Arial', 13, 'bold'), bg=emailFrame.cget("bg"), fg="#222").grid(row=0, column=0, padx=10)

        self.emailInput = tk.Entry(emailFrame, **inputStyle)
        self.emailInput.grid(row= 0, column= 1, padx= 10, ipady=5, ipadx=5)
        

        passwordFrame = tk.Frame(self.loginFrame, bg=self.loginFrame.cget("bg"))
        passwordFrame.pack(pady=10)
        tk.Label(passwordFrame, text= "Enter Password:", font= ('Arial', 13, 'bold'), bg= passwordFrame.cget("bg"), fg="#222").grid(row= 0, column= 0, padx= 10)

        self.passwordInput = tk.Entry(passwordFrame, show= "*", **inputStyle)
        self.passwordInput.grid(row= 0, column= 1, padx= 10, ipady=5, ipadx=5) 

        self.loginBtn = tk.Button(self.loginFrame, text="LOGIN", font=('Arial', 13), bg="#0FAE83", fg="white", pady=7, bd=0, width= 25, command=self.handleLogin)
        self.loginBtn.pack(pady=20)
        


    def handleLogin(self):

        def showError(msg):
            self.login_status.config(text=f"*{msg}")
            self.loginBtn.config(state="normal")
        

        self.loginBtn.config(state="disabled")
        email = self.emailInput.get()
        password = self.passwordInput.get()

        #input validation 
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if not re.match(regex, email):
            showError("Invalid email address")            
            return
        
        elif len(password) < 4:
            showError("Password must be at least 4 characters")
            return
        
        try:
            resp = requests.post(self.baseURL + 'login/', data = {"email": email, "password": password})
            if resp.status_code == 200:
                print("Login successful")
                resp = resp.json()
                self.authToken = resp.get('authToken')
                self.user_id = resp.get('user')['id']
                self.user_name = resp.get('user')['name']

                self.loginFrame.pack_forget()
                self.init_ui()
                
            else:
                showError(resp.json()['error'])
                return

        except Exception as e:
            showError("An error occured. Try again")
            print("Error : ", e)
            return

        # self.host_ip = "127.0.0.1"
        # self.host_port = 5000
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.bind((self.host_ip, self.host_port))
        # self.startThread()



    def createDashboardUI(self):
        """Create Dashboard UI."""
        frame = tk.Frame(self.content, bg="white")
        tk.Label(frame, text="Dashboard", font=('Arial', 24), bg="white").pack(pady=20)
        return frame



    def createChatsUI(self):
        frame = tk.Frame(self.content, bg="white")

        # Chat list panel
        chat_list = tk.Frame(frame, width=300, bg="#f5f6f7")
        chat_list.pack(side=tk.LEFT, fill=tk.Y)
        chat_list.pack_propagate(False)

        chat_canvas = tk.Canvas(chat_list, bg="#f5f6f7", width=300)
        chat_scrollbar = ttk.Scrollbar(chat_list, orient="vertical", command=chat_canvas.yview)
        chat_frame = tk.Frame(chat_canvas, bg="#f5f6f7")

        chat_frame.bind("<Configure>", lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all")))
        chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw", width=300)
        chat_canvas.configure(yscrollcommand=chat_scrollbar.set)

        # Add chats

        chats = requests.get(self.baseURL + 'chats/', headers= {"Authorization": f"Bearer {self.authToken}"}).json()
        
        for i in chats:
            chat_id = i['id']
            chat = tk.Frame(chat_frame, bg="white", pady=10, padx=5, cursor="hand2")
            chat.pack(fill=tk.X, pady=4)

            tk.Label(chat, text=f"Chat {chat_id}", bg="white").pack(anchor="w")
            tk.Label(chat, text="Last message...", fg="gray", bg="white").pack(anchor="w")
            chat.bind("<Button-1>", lambda e, i=chat_id: self.show_messages(i))

        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        chat_canvas.bind(
            "<Enter>", 
            lambda e: chat_canvas.bind_all("<MouseWheel>", 
            lambda e: chat_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        )
        chat_canvas.bind("<Leave>", lambda e: chat_canvas.unbind_all("<MouseWheel>"))

        # Message view
        message_view = tk.Frame(frame, bg="white")
        message_view.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        #top heaader
        msgHeader = tk.Frame(message_view, bg="#e6e6e6", height=40)
        msgHeader.pack(side=tk.TOP, fill=tk.X)
        msgHeader.pack_propagate(False)

        tk.Label(msgHeader, text= "Receiver 1", bg=msgHeader.cget("bg"), font= ('Arial', 12)).pack(pady=10, padx=10, anchor="w")

        messages_container = tk.Frame(message_view, bg="white")
        messages_container.pack(fill=tk.BOTH, expand=True)

        message_canvas = tk.Canvas(messages_container, bg="white")
        message_scrollbar = ttk.Scrollbar(
            messages_container, 
            orient="vertical", 
            command=message_canvas.yview
        )
        self.message_frame = tk.Frame(message_canvas, bg="white")

        self.message_window = message_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")

        def set_message_width(event=None):
            """Set the message frame width dynamically after rendering."""
            message_canvas.itemconfig(self.message_window, width=message_view.winfo_width() - 50)

        message_view.bind("<Configure>", set_message_width)

        self.message_frame.bind(
            "<Configure>", 
            lambda e: message_canvas.configure(scrollregion=message_canvas.bbox("all")),
        )
        message_canvas.configure(yscrollcommand=message_scrollbar.set)
        self.root.after(50, lambda: message_canvas.yview_moveto(1.0))

        message_canvas.pack(
            side=tk.LEFT, 
            fill=tk.BOTH, 
            expand=True, 
            pady=10,
            padx=10
        )
        message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        message_canvas.bind(
            "<Enter>", 
            lambda e: message_canvas.bind_all("<MouseWheel>", 
            lambda e: message_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        )
        message_canvas.bind("<Leave>", lambda e: message_canvas.unbind_all("<MouseWheel>"))

        # Message input
        input_frame = tk.Frame(message_view, bg="#e6e6e6", height=60)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X)
        input_frame.pack_propagate(False)

        self.message_input = tk.Entry(input_frame, bg="#ffffff", font=('Arial', 12), x=10, name="message_input")
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        send_btn = tk.Button(input_frame, text="Send", bg="#2c3e50", fg="white", font=('Arial', 10, 'bold'))
        send_btn.pack(side=tk.RIGHT, padx=10, pady=10)


        return frame
    


    def createTasksUI(self):
        """Create Tasks UI."""
        frame = tk.Frame(self.content, bg="white")
        tk.Label(frame, text="Tasks Section", font=('Arial', 24), bg="white").pack(pady=20)
        return frame




    def toggle_navbar(self):
        """Expand or collapse navbar."""
        if self.is_navbar_expanded:
            self.navbar.configure(width=50)
            for btn in self.nav_buttons:
                btn.pack_forget()
            for icon in self.nav_icons:
                icon.pack(pady=5)
        else:
            self.navbar.configure(width=200)
            for icon in self.nav_icons:
                icon.pack_forget()
            for btn in self.nav_buttons:
                btn.pack(pady=5, fill=tk.X)
        self.is_navbar_expanded = not self.is_navbar_expanded



    def init_ui(self):

        # Navbar
        self.navbar = tk.Frame(self.main_container, width=50, bg=self.bgc_primary)
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
            pady=10, 
            bd=0, 
            command=self.toggle_navbar
        )
        hamburger_btn.pack(pady=5, padx=5, anchor="w")

        # Navbar buttons
        navLinks = [("Dashboard", "📊"), ("Chats", "💬"), ("Tasks", "📋")]
        navLink_style = {
            'font': ('Arial', 14), 
            'bg': self.navbar.cget("bg"), 
            'fg': "white", 
            'pady': 10, 
            'bd': 0, 
            'padx': 10, 
            'anchor': "w", 
            'justify': "left"
        }
        self.nav_buttons = []
        self.nav_icons = []        
        
        for text, icon in navLinks:
            icon_btn = tk.Button(
                self.navbar, 
                text=icon, 
                command=lambda t=text: self.show_content(t), 
                **navLink_style
            )
            icon_btn.pack(pady=5)
            self.nav_icons.append(icon_btn)

            text_btn = tk.Button(
                self.navbar, 
                text=f"{icon} {text}", 
                command=lambda t=text: self.show_content(t), 
                **navLink_style
            )
            self.nav_buttons.append(text_btn)

        # Content area
        self.content = tk.Frame(self.main_container, bg="white")
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Initialize sections
        self.dashboard_frame = self.createDashboardUI()
        self.chats_frame = self.createChatsUI()
        self.tasks_frame = self.createTasksUI()

        # Show default section
        self.show_dashboard()






    def show_messages(self, chat_id):

        # Clear previous messages
        for widget in self.message_frame.winfo_children():
            widget.destroy()

        peers, messages = self.getChatDetails(chat_id)

        for sender, content, align, timestamp in messages:
            self.display_message({"sender": sender, "message": content}, align)
        

        def send():
            msg = ""

            if msg:
                self.send_message(peers, msg)
                # self.message_input.delete(0, tk.END)
            
   

    def show_content(self, section):
        """Show selected content section."""
        self.clear_content()
        if section.lower() == "dashboard":
            self.show_dashboard()
        elif section.lower() == "chats":
            self.show_chats()
        elif section.lower() == "tasks":
            self.show_tasks()

    def show_dashboard(self):
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
    

    def show_chats(self):
        self.chats_frame.pack(fill=tk.BOTH, expand=True)
    



    def show_tasks(self):
        self.tasks_frame.pack(fill=tk.BOTH, expand=True)
    

    def clear_content(self):
        """Clear current content before displaying new section."""
        for widget in self.content.winfo_children():
            widget.pack_forget()


    def getChatDetails(self, chat_id):
        resp = requests.get(self.baseURL + 'chat/messages/', headers= {"Authorization": f"Bearer {self.authToken}"}, data = {"chat_id": chat_id})

        if resp.status_code == 200:
            members =resp.json()['chat']['members']

            messages = resp.json()['messages']

            peers = [(m["ip_addr"], m["port"], m["name"]) for m in members]
            
            msgFormated = []
            for msg in messages:
                sender_id = msg["sender"]["id"]
                sender = msg["sender"]["name"] if sender_id != self.user_id else "You"
                align = "right" if sender_id == self.user_id else "left"

                msgFormated.append((sender, msg['content'], align, msg['timestamp']))
            
            return [peers, msgFormated]





    def startThread(self):
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def receive_messages(self):
        while True:
            try:
                message, _ = self.sock.recvfrom(1024)
                self.display_message(json.loads(message.decode()), "left")
            except:
                break

    def send_message(self, peers, message):
        for peer in peers:
            self.sock.sendto(json.dumps({"sender": "You", "message": message}).encode(), (peer[0], peer[1]))
        self.display_message({"sender": "You", "message": message}, "right")
    

    def display_message(self, msg, align):
        msg_frame = tk.Frame(self.message_frame, bg="white")
        msg_frame.pack(pady=5, padx=10, anchor="e" if align == "right" else "w")

        bubble_frame = tk.Frame(
            msg_frame,
            bg="#dcf8c6" if align == "right" else "#e6e6e6",
            bd=1,
            relief="solid"
        )
        bubble_frame.pack(side="right" if align == "right" else "left")

        tk.Label(bubble_frame, text=msg["sender"], bg=bubble_frame.cget("bg"), fg="blue", font=('Arial', 8), padx=5).pack(anchor="w")
        tk.Label(bubble_frame, text=msg["message"], wraplength=280, bg=bubble_frame.cget("bg"), font=('Arial', 11), padx=5, justify="left").pack()
    
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
