import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from PIL import Image, ImageTk
import threading, requests, json, re, os, time, datetime, asyncio, websockets



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
            "bg4_mid": "#55a992",
            "bg5": "#2D3E50",
            "bg6": "#848786",
            "bg7": "#007bff",
        }


        self.openedTaskID = None
        self.openedChatID = None

        self.chatOrder = []
        self.chatData = {}
        self.taskStack = []
        

        # self.isMsgUI_init = False
        self.baseURL = "http://127.0.0.1:8000/api/"
        self.ws_url = "ws://127.0.0.1:8000/ws/chat/"


        self.mainFrame = tk.Frame(self.root, bg= self.bgs["bg6"])
        self.mainFrame.pack(fill=tk.BOTH, expand=True)

        self.load_icons()
        self.authenticate()

    def authenticate(self):
        token = self.load_token()
        if token and self.get_userDetails(token):
            self.initMainUI()
        else:
            self.initLoginUI()


    def get_userDetails(self, token):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(self.baseURL + "user/details/", headers=headers)

            if resp.status_code == 200:
                self.authToken = token

                for key, val in resp.json().items():
                    setattr(self, f"user_{key}", val)

                return True
            else:
                print("Failed to get user details:", resp.json())
        except requests.exceptions.RequestException as e:
            print("Network error:", e)

        return False

    def connectToWs(self):
        """Connects to the WebSocket server in a separate thread."""

        def runLoop():
            try:
                asyncio.run(ws_handler())
            except Exception as e:
                print(f"WebSocket error: {e}")

        async def ws_handler():
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.ws = ws
                    print("WebSocket connection established.")

                    initialData = json.dumps({
                        'user_id': self.user_id,
                        'msg': "initial"
                    })

                    await self.ws.send(initialData)
                    await self.receiveMessage()
            
            except ConnectionRefusedError as e:
                print(f"WebSocket connection failed: {e}")
                self.ws = None
            except Exception as e:
                print(f"WebSocket error: {e}")
                self.ws = None
        
        wsThread = threading.Thread(target=runLoop, daemon=True)
        wsThread.start()


    async def receiveMessage(self):
        try:
            while True:
                msg = await self.ws.recv()
                self.process_message(msg)
        except websockets.exceptions.ConnectionClosedOK:
            print("WebSocket connection closed.")
        except Exception as e:
            print("Error receiving message:", e)


    def process_message(self, msg):
        """Process incoming WebSocket messages."""
        try:
            data = json.loads(msg)
            dataType = data.get('type')

            print(f"Received new message! (Type: {dataType})")

            if dataType == 'new_chatMsg':

                chat_data = data.get('chat_data')
                msg_data = data.get('msg_data')

                self._updateChatStack(chat_data)

                if chat_data['id'] == self.openedChatID:
                    self.addMessage2Canvas(msg_data)
                    self.msgCanvas.update_idletasks()
                    self.msgCanvas.yview_moveto(1)
                else:
                    # Notify user of new message ; like show a notification icon on respective chat and populateChat where latast msg chat is in top

                    pass
            elif dataType == 'new_task':
                # Notify user/team for new task assigned
                pass

        except json.JSONDecodeError:
            print(f"Invalid JSON received: {msg}")
        except Exception as e:
            print(f"Error processing message: {e}")

    def send_message(self):
        """Sends a message to the server via WebSocket."""
        msgInp = self.msgInput.get()
        if msgInp and self.ws and self.openedChatID:
            try:
                msgData = {
                    "msg": msgInp,
                    "chat_id": str(self.openedChatID),
                    "user_id": str(self.user_id),
                }
                asyncio.run(self.ws.send(json.dumps(msgData))) # Send message via WebSocket
                self.msgInput.delete(0, tk.END)

            except websockets.exceptions.ConnectionClosedOK:
                print("WebSocket connection closed.")
                self.ws = None
            except Exception as e:
                print(f"Error sending message: {e}")



# initialization events
    def initMainUI(self):

        self.connectToWs()

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
        navLinks = [("Dashboard", "📊"), ("Tasks", "📋"), ("Teams", "🧑‍👨‍👦"), ("Chats", "💬")]
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


    def initAddTaskForm(self, addTaskBtn):
        formFrame = tk.Frame(self.mainFrame, bg=self.bgs["bg1"], padx=30, pady=30, bd=3, relief="flat")
        formFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        addTaskBtn.config(state="disabled")
        def closeForm():
            formFrame.destroy()
            addTaskBtn.config(state="normal")
   
        headerFrame = tk.Frame(formFrame, bg=formFrame.cget("bg"))
        headerFrame.pack(fill="x", pady=(0, 20))

        # Title
        tk.Label(headerFrame, text="Add Task", font=('Arial', 16, 'bold'), bg=headerFrame.cget("bg"), fg="#fff").pack(side="left", pady=5)

        # Close button
        closeBtn = tk.Button(headerFrame, text="✕", font=('Arial', 12, 'bold'), bg="red", fg="#fff", bd=0, padx=8, pady=4, command= closeForm)
        closeBtn.pack(side="right")


        inputStyle = {
            "font": ('Arial', 12),
            "width": 40,
            "bg": "#fff",
            "bd": 0,
            "relief": "groove",
        }
        labelStyle = {
            "font": ('Arial', 13),
            "bg": formFrame.cget("bg"),
            "fg": "#fff",
            "anchor": "w"
        }


        # Task Title
        tk.Label(formFrame, text="Task Title *", **labelStyle).pack(anchor="w")
        titleInput = tk.Entry(formFrame, **inputStyle)
        titleInput.pack(pady=(5, 15), ipadx=5, ipady=5)

        # Description
        tk.Label(formFrame, text="Description *", **labelStyle).pack(anchor="w")
        descInput = tk.Text(formFrame, height=4, **inputStyle)
        descInput.pack(pady=(5, 15))

        # Assignment Frame
        assignFrame = tk.Frame(formFrame, bg=formFrame.cget("bg"))
        assignFrame.pack(fill="x", pady=(0, 15))

        assignType = tk.StringVar(value="user")

        def toggle_assignment(*args):
            if assignType.get() == "user":                
                userCombo.set("Select User")
                teamCombo.set("Select Team")
                teamCombo.config(state="disabled")
                userCombo.config(state="readonly")
            else:                
                teamCombo.set("Select Team")
                userCombo.set("Select User")
                userCombo.config(state="disabled")
                teamCombo.config(state="readonly")

        radioStyle={
            "variable":assignType,
            "bg":formFrame.cget("bg"), 
            "fg":"#fff", 
            "font":('Arial', 12), 
            "command":toggle_assignment
        }

        tk.Label(assignFrame, text="Assign to:", **labelStyle).pack(anchor="w")

        tk.Radiobutton(assignFrame, text="User", value="user", **radioStyle).pack(side="left", padx=(2, 10))
        tk.Radiobutton(assignFrame, text="Team", value="team", **radioStyle).pack(side="left")


        comboFrame = tk.Frame(formFrame, bg=formFrame.cget("bg"))
        comboFrame.pack(fill="x", pady=(0, 15))

        # User Combobox
        userCombo = ttk.Combobox(comboFrame, font=inputStyle["font"], width=40, state="readonly")
        userCombo.pack(pady=5)
        userCombo.set("Select User")

        # Team Combobox
        teamCombo = ttk.Combobox(comboFrame, font=inputStyle["font"], width=40, state="disabled", height=12)
        teamCombo.pack(pady=5)
        teamCombo.set("Select Team")

        # Deadline
        tk.Label(formFrame, text="Deadline *", **labelStyle).pack(anchor="w")
        deadlineFrame = tk.Frame(formFrame, bg=formFrame.cget("bg"), width= 40)
        deadlineFrame.pack(fill="x", pady=(5, 15))

        # Date picker 
        dateInput = tk.Entry(deadlineFrame, **{**inputStyle, 'width': 36})
        dateInput.pack(side="left", ipady=5)
        dateInput.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        
        calendarBtn = tk.Button(deadlineFrame, text="📅", font=('Arial', 12), width= 4, bg="#fff", command=lambda: self.show_calendar(dateInput))
        calendarBtn.pack(side="left", padx=5)

        # Submit Button
        submitBtn = tk.Button(
            formFrame, 
            text="Create Task", 
            font=('Arial', 13),
            bg=self.bgs["bg5"], 
            fg="white", 
            pady=10, 
            bd=0, 
            width=25,
            command=lambda: self.createTask({
                'title': titleInput.get(),
                'desc': descInput.get("1.0", tk.END),
                'assigned_user': userCombo.get() if assignType.get() == "user" else None,
                'assigned_team': teamCombo.get() if assignType.get() == "team" else None,
                'deadline': dateInput.get()
            })
        )
        submitBtn.pack(pady=20)

        # Fetch users and teams data
        self.asyncGetRequest("users/", lambda data: userCombo.configure(values=[f"{u['name']} ({u['id']})" for u in data]))
        self.asyncGetRequest("teams/", lambda data: teamCombo.configure(values=[f"{t['name']} ({t['id']})" for t in data]))


    def initContactList(self, newChatBtn):
        bgColor = self.bgs["bg4"]
        
        frame = tk.Frame(self.content, bg=bgColor, padx=10, pady=10)
        frame.place(x = newChatBtn.winfo_x(), y = newChatBtn.winfo_y()+newChatBtn.winfo_height()+10, width=350, height=600)

        newChatBtn.config(state="disabled")
        def closeForm():
            frame.destroy()
            newChatBtn.config(state="normal")

        headerFrame = tk.Frame(frame, bg=frame.cget("bg"))
        headerFrame.pack(fill="x", pady=(0, 20))

        # Title
        tk.Label(headerFrame, text="New Chat", font=('Arial', 16, 'bold'), bg=headerFrame.cget("bg"), fg="#fff").pack(side="left", pady=5)

        closeBtn = tk.Button(headerFrame, text="✕", font=('Arial', 12, 'bold'), bg="red", fg="#fff", bd=0, padx=8, pady=4, command= closeForm)
        closeBtn.pack(side="right")


        canvas, canvasFrame = self.createScrollableCanvas(frame, bgColor)

        for i in range(100):
            chat_item = tk.Frame(canvasFrame, bg=bgColor, pady=10, padx=10)
            chat_item.pack(fill="x")

            lbl = tk.Label(chat_item, text=f"Chat {i+1}", font=('Arial', 12), bg=bgColor, fg="#fff")
            lbl.pack(side="left")
            

            chatBindings ={
                '<MouseWheel>': lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"),
                '<Enter>': lambda e, item=chat_item: self.mouseEnter_effect1(item, self.bgs["bg4_mid"]),
                '<Leave>': lambda e, item=chat_item: self.mouseLeave_effect1(item, bgColor),
                # '<Button-1>': lambda e,c_id = chat_id: 
                #             self.asyncGetRequest(
                #                 endpoint = f'chats/{c_id}/',
                #                 callback = self.handleChatClick
                #             ),
            }

            for event, func in chatBindings.items():
                chat_item.bind(event, func)
                lbl.bind(event, func)

        




#UI create events

    def createDashboardUI(self):
        """Create Dashboard UI."""
        frame = tk.Frame(self.content, bg="white")
        tk.Label(frame, text="Dashboard", font=('Arial', 24), bg="white").pack(pady=20)
        return frame


    def createChatsUI(self):
        content = {
            "title": "Chats",
            "variablePrefix": "chat",
            "filters": ["ALL", "GROUPS"],
            "api":{
                "endpoint": "chats/",
                "filter": "all",
                "callback": "_updateChatStack",
            },
            "defaultMsg": "Click on a chat to start messaging.",
        }
        frame = tk.Frame(self.content, bg="white")
        self.layout1(frame, json.dumps(content))
        return frame


    def createTasksUI(self):
        content = {
            "title": "Tasks",
            "variablePrefix": "task",
            "filters":["TO DO", "IN PROGRESS", "COMPLETED"],
            "api":{
                "endpoint": "tasks/",
                "filter": "to do",
                "callback": "populateTasks",
            },
            "defaultMsg": "Click on a task to view details.",
        }
        frame = tk.Frame(self.content, bg="white")
        self.layout1(frame, json.dumps(content))
        return frame


    def createScrollableCanvas(self, parentFrame, bgColor):
        """
        Creates a scrollable canvas with automatic scrollbar hiding
        
        Args:
            parentFrame: Parent frame to contain the canvas
            bgColor: Background color for canvas and inner frame
        
        Returns:
            tuple: (canvas, canvasFrame) - The canvas and its inner frame
        """
        canvas = tk.Canvas(parentFrame, bg=bgColor)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Configure scrollbar style
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Vertical.TScrollbar",
            background=self.bgs["bg4"],
            arrowcolor=self.bgs["bg4"],
            troughcolor=bgColor,
            arrowsize=0,
            borderwidth=0,
            width=3
        )
        style.map(
            "Vertical.TScrollbar",
            background=[('active', self.bgs["bg4"])],
        )

        scrollbar = ttk.Scrollbar(canvas, orient="vertical", style="Vertical.TScrollbar", command=canvas.yview)

        canvasFrame = tk.Frame(canvas, bg=bgColor)
        canvasWindow = canvas.create_window((0, 0), window=canvasFrame, anchor="nw")

        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvasWindow, width=canvas.winfo_width() - 5))

        # Configure canvas frame
        canvasFrame.bind(
            "<Configure>",
            lambda e: canvas.config(
                scrollregion=(0, 0, canvasFrame.winfo_reqwidth(), 
                            max(self.root.winfo_height() - 100, canvasFrame.winfo_reqheight()))
            )
        )

        # Auto-hide scrollbar
        canvas.bind('<Enter>', lambda e: scrollbar.pack(side=tk.RIGHT, fill=tk.Y))
        canvas.bind('<Leave>', lambda e: scrollbar.pack_forget())

        return canvas, canvasFrame

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
                if self.get_userDetails(token):
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
        
    def handleChatClick(self, data):

        chat_id = data.get('chat')['id']
        if self.openedChatID != chat_id:

            chatMeta = data.get('chat').get('metaData')
            messages = data.get('messages')

            if hasattr(self, "activeChat"): 
                # Remove the previous active chat's bgcolor
                self.activeChat.config(bg=self.bgs["bg1_light"]) 
                [w.config(bg=self.bgs["bg1_light"]) for w in self.activeChat.winfo_children()]

            self.openedChatID = chat_id
            msgPanelFrame = getattr(self,"chat_rightPanelFrame")

            # chat_widget.config(bg=self.bgs["bg1_mid2"]) 
            # [w.config(bg=self.bgs["bg1_mid2"]) for w in chat_widget.winfo_children()]
            # self.activeChat = chat_widget 


            for widget in msgPanelFrame.winfo_children():
                widget.destroy()
                # widget.pack_forget()


            msgP_HeaderFrame = tk.Frame(msgPanelFrame, bg=self.bgs["bg1_light"], padx=5, pady=10)
            msgP_HeaderFrame.pack(fill="x", side=tk.TOP)

            tk.Label(msgP_HeaderFrame, text=chatMeta.get('name'), bg=msgP_HeaderFrame.cget('bg'), font=('Arial', 11, 'bold')).pack(anchor="w")

            #msg canvas
            self.msgCanvas = tk.Canvas(msgPanelFrame)
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
            msgInputFrame = tk.Frame(msgPanelFrame, bg=self.bgs["bg1_light"], padx=5, pady=5, height=60)
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
                command= self.send_message
            ).pack(side=tk.RIGHT, padx=3, pady=5)


            #populate messages
            for msg in messages:
                self.addMessage2Canvas(msg)

    def handleTaskClick(self, data, updateTask = False):
        task_id = data.get('id')
        if self.openedTaskID != task_id or updateTask :

            self.openedTaskID = task_id

            status = data.get('status')

            taskDetailFrame = getattr(self,"task_rightPanelFrame")
            bgc = taskDetailFrame.cget('bg')

            for widget in taskDetailFrame.winfo_children():
                widget.destroy()
                # widget.pack_forget()

            taskDetailFrame.config(padx= 10, pady= 15)
            tk.Label(taskDetailFrame, text=f"Task #{task_id}", bg= bgc, font=('Arial', 16, 'bold italic underline')).pack(anchor="w", pady=10)

            dataFrame = tk.Frame(taskDetailFrame, bg=bgc)
            dataFrame.pack(fill="x", side=tk.TOP, pady=15, ipadx=5)

            f1 = tk.Frame(dataFrame, bg=bgc, pady= 5)
            f1.pack(anchor="w", fill="x")

            tk.Label(f1, text = 'Title: ', bg = bgc, font = ('Arial', 13, 'bold')).grid(row=0, column=0, sticky='nw')
            tk.Label(f1, text = data.get('title').capitalize(), bg = bgc, font = ('Arial', 13)).grid(row=0, column=1, sticky='nw')


            f2 = tk.Frame(dataFrame, bg=bgc, pady=5)
            f2.pack(anchor="w", fill="x")

            tk.Label(f2, text='Description:', bg=bgc, font=('Arial', 13, 'bold')).grid(row=0, column=0, sticky='nw')
            descLabel = tk.Label(f2, text=data.get('description').capitalize(), bg=bgc, font=('Arial', 13), justify="left")
            descLabel.grid(row=0, column=1, sticky='nw')


            f3 = tk.Frame(dataFrame, bg= bgc, pady= 5)
            f3.pack(anchor="w", fill="x")

            tk.Label(f3, text = 'Deadline: ', bg = bgc, font = ('Arial', 13, 'bold'), pady=5).grid(row=0, column=0, sticky='nw')
            tk.Label(f3, text = data.get('deadline'), bg = bgc, font = ('Arial', 13), pady=5).grid(row=0, column=1, sticky='nw')


            f4 = tk.Frame(dataFrame, bg= bgc, pady= 5)
            f4.pack(anchor="w", fill="x")

            tk.Label(f4, text = 'Status: ', bg = bgc, font = ('Arial', 13, 'bold'), pady=5).grid(row=0, column=0, sticky='nw')
            tk.Label(f4, text = str(status).upper(), bg = bgc, font = ('Arial', 13), pady=5).grid(row=0, column=1, sticky='nw')


            overdue = data.get('overdue')
            btnStyle ={
                "fg": "#fff",
                "font": ('Arial', 12, 'bold'),
                "pady": 5, 
                "cursor": 'hand2',
                "bd": 1
            }

            if status == "completed":
                btn = tk.Label(dataFrame, text="Completed", bg="green", **btnStyle)
            elif overdue:
                btn = tk.Label(dataFrame, text="Overdue", bg="red", **btnStyle)
            else:
                if status == 'to do': txt = "Start Task" 
                elif status == 'in progress': txt ="Mark as Complete" 

                btn = tk.Button(dataFrame, text=txt, bg=self.bgs['bg4'], command= lambda s = status, isSubtask = data.get('is_subtask'): self._updateTaskStatus(s, isSubtask) , **btnStyle)

            btn.pack(anchor="e", pady=10, padx=25, ipadx=10, ipady=5)



            def setDescWraplength(e, desc_label):                
                desc_label.config(wraplength= taskDetailFrame.winfo_width() / 1.27)     

            setDescWraplength(None, descLabel)

            taskDetailFrame.bind("<Configure>", lambda event: setDescWraplength(event, descLabel))


    def createTask(self, data):
        print(data)
        headers = {"Authorization": f"Bearer {self.authToken}"}
        resp = requests.post(f"{self.baseURL}task/c/", json=data, headers=headers)





#populate function
    def populateChat(self):
        panelBG = self.bgs["bg1_light"]
        canvas = getattr(self,"chat_canvas")
        canvasFrame = getattr(self,"chat_canvasFrame")
        
        for widget in canvasFrame.winfo_children():
            widget.destroy()
        
        
        if not self.chatOrder:
            tk.Label(canvasFrame, bg = panelBG, text = "Your Chatlist is Empty.", font=('Arial', 13)).pack(padx=5, pady=10)

            tk.Button(canvasFrame, text="Start a Chat", bg=self.bgs['bg4'], fg="#fff", font=('Arial', 11)).pack(ipadx=5, ipady=5, pady=5, padx=5)
            return

        for chat_id in self.chatOrder:
            chat = self.chatData[chat_id]
            meta = chat.get('metaData')
            lastMsg = chat.get('last_msg')
            msgTxt = ""
            
            chatFrame = tk.Frame(canvasFrame, bg= panelBG, cursor="hand2", pady=10, padx=10)
            chatFrame.pack(fill="x")
            
            fr = tk.Frame(chatFrame, bg=panelBG)
            fr.pack(fill="x")
            name = tk.Label(fr, text=meta['name'], bg=panelBG, font=('Arial', 11))
            name.pack(anchor="w", side="left")
            timestamp = tk.Label(fr, text=lastMsg.get('timestamp'), bg=panelBG, font=('Arial', 8))
            timestamp.pack(anchor="w", side="right")

            if 'sender' in lastMsg:
                msgTxt = f"{lastMsg.get('sender')['name']}: {lastMsg.get('content')}" if chat['is_group_chat'] else lastMsg.get('content')
            msg = tk.Label(chatFrame, text= msgTxt, bg=panelBG, font=('Arial', 9))
            msg.pack(anchor="w")

            chatBindings ={
                '<MouseWheel>': lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"),
                '<Enter>': lambda e, item=chatFrame: self.mouseEnter_effect1(item, self.bgs["bg1_mid"]),
                '<Leave>': lambda e, item=chatFrame: self.mouseLeave_effect1(item, self.bgs["bg1_light"]),
                '<Button-1>': lambda e,c_id = chat_id: 
                            self.asyncGetRequest(
                                endpoint = f'chats/{c_id}/',
                                callback = self.handleChatClick
                            ),
            }

            for event, func in chatBindings.items():
                chatFrame.bind(event, func)
                fr.bind(event, func)
                name.bind(event, func)
                timestamp.bind(event, func)
                msg.bind(event, func)


    def populateMsgs(self, messages):        
        for msg in messages :
            sender_id = msg['sender']['id']

            if sender_id != self.user_id:
                sender = msg['sender']['name'] 
                align = 'left'
            else:
                sender ='You'
                align = 'right'

            self.addMessage2Canvas(msg)



    def populateTasks(self, tasks):  
        panelBG = self.bgs["bg1_light"]
        canvas = getattr(self,"task_canvas")
        canvasFrame = getattr(self,"task_canvasFrame")

        for widget in canvasFrame.winfo_children():
            widget.destroy()
        
        if len(tasks) == 0:
            tk.Label(canvasFrame, text="No Tasks Available.", bg=panelBG, font=('Arial', 13)).pack(anchor="center", pady=10)
            return
        
        for task in tasks:
            task_id = task['id']
            deadline = task.get('deadline')
            
            today = datetime.date.today()
            time_diff = (datetime.datetime.strptime(deadline, '%Y-%m-%d').date() - today).days

            if time_diff < 0:
                color= '#8B0000'  # Overdue
            elif time_diff == 0:
                color= 'red'  # Today
            elif time_diff <= 3:
                color= '#ff6600'  # Under 3 days
            else:
                color= 'green'

            taskFrame = tk.Frame(canvasFrame, bg= panelBG, cursor="hand2", pady=10, padx=10)
            taskFrame.pack(fill="x")
            
            tk.Label(taskFrame, text=f"Task #{task_id}", bg=panelBG, font=('Arial', 10, "bold italic underline")).pack(anchor="w")
            tk.Label(taskFrame, text=task.get('title'), bg=panelBG, font=('Arial', 13)).pack(anchor="w")
            tk.Label(taskFrame, text=f"Deadline: {deadline}", bg=panelBG, fg = color, font=('Arial', 9)).pack(anchor="w")


            bindings ={
                '<MouseWheel>': lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"),
                '<Button-1>': lambda e,t_id = task_id, isSubtask = task.get('is_subtask'): 
                                    self.asyncGetRequest(
                                        endpoint=f'tasks/{t_id}',
                                        callback=self.handleTaskClick,
                                        params={"isSubtask": isSubtask}
                                    ),
                '<Enter>': lambda e, item=taskFrame: self.mouseEnter_effect1(item, self.bgs["bg1_mid"]),
                '<Leave>': lambda e, item=taskFrame: self.mouseLeave_effect1(item. self.bgs["bg1_light"]),
            }

            for event, func in bindings.items():
                taskFrame.bind(event, func)   
    
    
# helper events
    def clear_content(self):
        for widget in self.content.winfo_children():
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

    def mouseEnter_effect1(self, chat_widget, bgc):
        def add_config(widget):
            widget.config(bg=bgc)
            for w in widget.winfo_children():
                add_config(w)

        if not hasattr(self, "activeChat") or chat_widget != self.activeChat:
            add_config(chat_widget)

    def mouseLeave_effect1(self, chat_widget, bgc):
        def remove_config(widget):
            widget.config(bg=bgc)
            for w in widget.winfo_children():
                remove_config(w)

        if not hasattr(self, "activeChat") or chat_widget != self.activeChat:
            remove_config(chat_widget)

    def addMessage2Canvas(self, msgData):
        sender_id = msgData['sender']['id']

        if sender_id != self.user_id:
            sender = msgData['sender']['name'] 
            align = 'left'
        else:
            sender ='You'
            align = 'right'
            
        msgFrame = tk.Frame(self.msgsFrame, bg="white")
        msgFrame.pack(pady=5, padx=10, anchor="e" if align == "right" else "w")

        bubble_frame = tk.Frame(
            msgFrame,
            bg="#dcf8c6" if align == "right" else "#e6e6e6",
            bd=1,
            relief="solid"
        )
        bubble_frame.pack(side="right" if align == "right" else "left")

        sender_label = tk.Label(bubble_frame, text=sender, bg=bubble_frame.cget("bg"), fg="blue", font=('Arial', 8), padx=5)
        sender_label.pack(anchor="w")

        message_label = tk.Label(
            bubble_frame, 
            text= msgData["content"], 
            bg= bubble_frame.cget("bg"), 
            font= ('Arial', 11), 
            padx= 5, 
            justify= "left"
        )
        message_label.pack(anchor="w")

        time_label = tk.Label(bubble_frame, text= msgData["timestamp"], bg=bubble_frame.cget("bg"), fg="#374747", font=('Arial', 8, 'italic'), padx=5)
        time_label.pack(anchor="e")

        def update_message_label_wraplength(event = None):
            if message_label and message_label.winfo_exists():
                message_label.config(wraplength= getattr(self,"chat_rightPanelFrame").winfo_width()*0.7)
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
    

    def asyncGetRequest(self, endpoint: str, callback, params=None):
        def run():
            header = {"Authorization": f"Bearer {self.authToken}"}

            try:
                resp = requests.get(self.baseURL + endpoint, headers=header, params=params)
                if resp.status_code == 200:
                    respData = resp.json()
                    self.root.after(0, lambda: callback(respData))
            except requests.exceptions.RequestException as e:
                print("Request error:", e)

        threading.Thread(target=run, daemon=True).start()


    def show_calendar(self, entry_widget):
        def set_date():
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, cal.selection_get().strftime('%Y-%m-%d'))
            top.destroy()

        top = tk.Toplevel()
        top.grab_set()  # Make the dialog modal
        
        cal = Calendar(top, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(padx=10, pady=10)
        
        tk.Button(top, text="Select", command=set_date).pack(pady=5)


    def load_icons(self):
        self.icons = {}
        icon_files = {
            'newChat': 'icons/newChat.png',
            'newTask': 'icons/newTask.png',
            # Add more icons here as needed
        }
        
        try:
            for icon_name, icon_path in icon_files.items():
                if os.path.exists(icon_path):
                    self.icons[icon_name] = ImageTk.PhotoImage(Image.open(icon_path))
        except Exception as e:
            print(f"Error loading icons: {e}")


#RELOAD function 
    def reloadChats(self):
        self.clear_content()

        self.chats_frame = self.createChatsUI()
        self.initChats()




#UI layout


    def layout1(self, frame, content):
        content = json.loads(content)
        endpoint = content.get("api").get("endpoint")
        callback_name = content.get("api").get("callback")
        filter_val = content.get("api").get("filter")

        titleTxt = content.get("title")

        panelBG = self.bgs["bg1_light"]

        leftPanalFrame = tk.Frame(frame, bg=panelBG, width=350, padx=5, pady=5)
        leftPanalFrame.pack(side=tk.LEFT, fill=tk.Y)
        leftPanalFrame.pack_propagate(False)

        fr = tk.Frame(leftPanalFrame, bg=panelBG)
        fr.pack(side=tk.TOP, anchor=tk.W, fill=tk.X, padx=10)
        
        title = tk.Label(fr, text= titleTxt, bg=panelBG, font=("Arial", 16, "bold")).pack(side=tk.LEFT, anchor=tk.W)

        if titleTxt.lower() in ["task", "tasks"] and self.user_isAdmin == True:
            btn = tk.Button(
                fr,
                image= self.icons.get("newTask"),
                bg=self.bgs["bg4"],
                activebackground=self.bgs['bg1_mid2'],
                bd=0,
                pady=4,
                cursor="hand2",
            )
            btn.config(command= lambda b=btn: self.initAddTaskForm(b))
            btn.pack(side=tk.RIGHT, anchor=tk.W, ipadx= 6, ipady = 6)

        elif titleTxt.lower() in ["chat", "chats"]:

            btn = tk.Button(
                fr,
                image= self.icons.get("newChat"),
                bg=self.bgs["bg4"],
                activebackground=self.bgs['bg1_mid2'],
                bd=0,
                pady=4,
                cursor="hand2",
            )

            btn.pack(side=tk.RIGHT, anchor=tk.W, ipadx= 6, ipady = 6)
            btn.config(command= lambda b=btn: self.initContactList(b))

        filterFrame = tk.Frame(leftPanalFrame, bg=panelBG, pady=5, padx=5)
        filterFrame.pack(side=tk.TOP, anchor=tk.W, fill=tk.X, pady=10)

        filterBtnStyle = {
            'font': ('Arial', 10),
            'bg': self.bgs["bg4"],
            'fg': "#fff",
            "activebackground": self.bgs['bg5'],
            'activeforeground': "#fff",
            'pady': 1,
            'bd': 0,
            'padx': 15,
            'cursor': 'hand2'
        }
        filterBtns = []
        for filter in content.get("filters"):
            btn = tk.Button(
                filterFrame, 
                text=filter, 
                command= lambda f=filter: self._updateL1_leftPanel(endpoint, callback_name, filterBtns, f) , **filterBtnStyle)
            btn.pack(side=tk.LEFT, padx=5)
            filterBtns.append(btn)
            
        filterBtns[0].config(bg=self.bgs["bg5"])

        # create scrollable canvas
        canvas, canvasFrame = self.createScrollableCanvas(leftPanalFrame, panelBG)

        # populate items in laft panel
        self._updateL1_leftPanel(endpoint, callback_name, filterBtns, filter_val)

        rightPanelFrame = tk.Frame(frame, bg="white", padx=5, pady=5)
        rightPanelFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        defaultFrame = tk.Frame(rightPanelFrame)
        defaultFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(defaultFrame, text="K Collab", bg=defaultFrame.cget('bg'), font=('Arial', 18, 'bold')).pack()

        tk.Label(defaultFrame, text=content.get("defaultMsg"), bg=defaultFrame.cget('bg'), font=('Arial', 12)).pack()

        # creating dynamic global variables
        prefix = content.get("variablePrefix")
        setattr(self, f"{prefix}_canvas", canvas)
        setattr(self, f"{prefix}_rightPanelFrame", rightPanelFrame)
        setattr(self, f"{prefix}_canvasFrame", canvasFrame)
        setattr(self, f"{prefix}_filterBtns", filterBtns)


#update functions

    def _updateTaskStatus(self, statusTxt, isSubtask):
        statusTxt = statusTxt.lower()
        task_id = self.openedTaskID

        if statusTxt == "to do":
            newStatus = "in progress"
        elif statusTxt == "in progress":
            newStatus = "completed"
        else:
            return
        
        data = {
            "newStatus": newStatus,
            "isSubtask": isSubtask,
        }

        resp = requests.put(f"{self.baseURL}tasks/{task_id}/", headers= {"Authorization": f"Bearer {self.authToken}"}, data = data)

        if resp.status_code == 200:
            self.handleTaskClick(resp.json(), updateTask = True)

            filterBtns = getattr(self, f"task_filterBtns")

            for btn in filterBtns:
                if btn.cget('bg') == self.bgs["bg5"]:
                    filter_val = btn.cget("text")
            
            self._updateL1_leftPanel("tasks/", "populateTasks", filterBtns, filter_val.lower())
        else:
            print("Failed to update task status")
        

        

    def _updateL1_leftPanel(self, endpoint, callback_name, filterBtns, filter_val = None):

        if filter_val is not None:
            filter_val = filter_val.lower()
            params = {
                "filter": filter_val
            }
            if callback_name and endpoint:
                callback_func = getattr(self, callback_name, None) 

                if callable(callback_func):
                    self.asyncGetRequest(endpoint, callback_func, params)
            
            for btn in filterBtns:
                # update active filter btn
                if btn.cget("text").lower() == filter_val:
                    btn.config(bg=self.bgs["bg5"])
                else:
                    btn.config(bg=self.bgs["bg4"])



    def _updateChatStack(self, chat_data):
        
        if isinstance(chat_data, list):
        # Clear existing data when receiving full list
            self.chatOrder = []
            self.chatData = {}
            
            for chat in chat_data:
                chat_id = chat['id']
                self.chatData[chat_id] = chat
                self.chatOrder.append(chat_id)
        else:
            # Single chat update
            chat_id = chat_data['id']
            self.chatData[chat_id] = chat_data
            
            # Remove if already in order
            if chat_id in self.chatOrder:
                self.chatOrder.remove(chat_id)
            
            # Add to front of order
            self.chatOrder.insert(0, chat_id)
        
        # Repopulate chat list
        self.populateChat()




if __name__ == "__main__":
    root = tk.Tk()
    app = KCollabApp(root)
    root.mainloop()