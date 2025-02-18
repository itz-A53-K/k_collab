import tkinter as tk
from tkinter import ttk
import socket, threading, requests, json, re, os, time


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
                hostIP = data.get("ip")
                hostPort = data.get("port")

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

        canvas = tk.Canvas(chatPanelFrame, bg= panelBG, width=chatPanelFrame.winfo_width())
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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

        scrollbar = ttk.Scrollbar(chatPanelFrame, orient="vertical", style="Vertical.TScrollbar", command=canvas.yview)


        chatFrame = tk.Frame(canvas, bg= panelBG, padx=5)
        chatFrame.bind(
            '<Configure>',
            lambda e: canvas.config(
                scrollregion=(0,0, chatFrame.winfo_reqwidth(), max(self.root.winfo_height() - 100 ,chatFrame.winfo_reqheight()))
            )
        )
        

        canvas.create_window(
            (-2, -2), 
            window=chatFrame, 
            anchor="nw", 
            width=340
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.bind(
            '<Enter>',
            lambda e: scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        )
        canvas.bind(
            '<Leave>',
            lambda e: scrollbar.pack_forget()
        )
        
        chats = requests.get(self.baseURL + "chats/", headers={"Authorization": f"Bearer {self.authToken}"})
        
        if chats.status_code != 200:
            tk.Label(chatFrame, bg = panelBG, text = "Error Loading Chats", fg ="red").pack(padx=5, pady=10)

            #reload btn
            tk.Button(chatFrame, text="Reload", command=lambda: self.reloadChats() ).pack(ipadx=5, ipady=5, pady=5, padx=5)

        else:
            for i in chats.json():
                chat_id = i['id']
                meta = i.get('metaData')
                chat = tk.Frame(chatFrame, bg= panelBG, cursor="hand2", pady=10, padx=10)
                # chat.pack(ipady=10,ipadx=10, fill="x")
                chat.pack(fill="x")

                chat.chat_id = chat_id
                
                tk.Label(chat, text=meta['name'], bg=panelBG, font=('Arial', 11)).pack(anchor="w")
                tk.Label(chat, text=meta['name'], bg=panelBG, font=('Arial', 8)).pack(anchor="w")

                chatBindings ={
                    '<MouseWheel>': lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"),
                    '<Button-1>': lambda e, id=chat_id, mData=meta, chat_widget = chat: self.handleChatClick(id, mData, chat_widget),
                    '<Enter>': lambda e, item=chat: self.chat_MouseEnter(item),
                    '<Leave>': lambda e, item=chat: self.chat_MouseLeave(item),
                }

                for event, func in chatBindings.items():
                    chat.bind(event, func)

                    
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
        
    def handleChatClick(self, chat_id, metaData, chat_widget):
        if self.openedChatID != chat_id:

            if hasattr(self, "activeChat"): 
                self.activeChat.config(bg=self.bgs["bg1_light"]) 
                [w.config(bg=self.bgs["bg1_light"])  for w in self.activeChat.winfo_children()]

            self.openedChatID = chat_id
            print(chat_id)

            chat_widget.config(bg=self.bgs["bg1_mid2"]) 
            [w.config(bg=self.bgs["bg1_mid2"])  for w in chat_widget.winfo_children()]
            self.activeChat = chat_widget 


            for widget in self.msgPanelFrame.winfo_children():
                widget.destroy()
                # widget.pack_forget()


            msgP_HeaderFrame = tk.Frame(self.msgPanelFrame, bg=self.bgs["bg1_light"], padx=5, pady=10)
            msgP_HeaderFrame.pack(fill="x",side=tk.TOP)

            tk.Label(msgP_HeaderFrame, text=metaData['name'], bg=msgP_HeaderFrame.cget('bg'), font=('Arial', 11, 'bold')).pack(anchor="w")

            
        
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


#RELOAD APP 
    def reloadChats(self):
        print("reloaded")
        self.clear_content()

        self.chats_frame = self.createChatsUI()
        self.initChats()





if __name__ == "__main__":
    root = tk.Tk()
    app = KCollabApp(root)
    root.mainloop()