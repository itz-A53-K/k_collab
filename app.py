import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import Calendar
from PIL import Image, ImageTk
from io import BytesIO
from django.utils.text import Truncator
import threading, requests, json, re, os, time, datetime, asyncio, websockets, base64


class KCollabApp:
    def __init__(self, root):
        print("App running ...")
        self.root = root
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)
        self.root.title("K Collab")
        self.TOKEN_FILE = "kcollab_auth_token.json"
        self.tokenExpireTime = 5 * 86400 # 5 days in seconds ( 1 day = 86400 secs)

        self.bgs = {
            "bg_pri": "#fff",
            "bg1": "#196C38",
            "bg1_mid": "#93e7b2",
            "bg1_mid2": "#7bcf9a",
            "bg1_light": "#a3efbf",
            "bg2": "#8ddfab",
            "bg3": "#1D6F4C",
            "bg4": "#0FAE83",
            "bg4_mid": "#55a992",
            "bg5": "#2D3E50",
            "gray_1": "#848786",
            "gray_2": "#dcdfde",
            "bg7": "#007bff",
            "green_1": "#dcf8c6"
        }


        self.openedTaskID = None
        self.openedChatID = None
        self.current_receiver_id = None

        self.chatOrder = []
        self.chatData = {}
        self.taskData ={}
        self.teamData = {}
        

        # self.isMsgUI_init = False
        self.baseURL = "http://127.0.0.1:8000"
        self.apiURL = f"{self.baseURL}/api/"
        self.ws_url = "ws://127.0.0.1:8000/ws/"


        self.mainFrame = tk.Frame(self.root, bg= self.bgs["gray_1"])
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
            resp = requests.get(self.apiURL + "user/details/", headers=headers)

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
        """Connect to WebSocket server in a seperate thread. And"""
        def runLoop():
            try:
                asyncio.run(ws_handler())
            except Exception as e:
                print(f"WebSocket error: {e}")

        async def ws_handler():
            try:
                async with websockets.connect(f"{self.ws_url}{self.user_id}/") as ws:
                    self.ws = ws
                    print("WebSocket connection established.")

                    initialData = json.dumps({
                        'type': "initial",
                        'user_id': self.user_id,
                    })

                    await self.ws.send(initialData)

                    while True:
                        msg = await self.ws.recv()
                        await self.process_ws_message(msg)
                    # await self.receiveMessage()
            
            except ConnectionRefusedError as e:
                print(f"WebSocket connection failed: {e}")
                self.ws = None
            except Exception as e:
                print(f"WebSocket error: {e}")
                self.ws = None
        
        wsThread = threading.Thread(target=runLoop, daemon=True)
        wsThread.start()


    async def disconnectfromWS(self):
        """Disconnect from the WebSocket server."""
        if self.ws:
            try:
                await self.ws.close()
                print("WebSocket connection closed.")
            except Exception as e:
                print(f"Error while closing WebSocket: {e}")
            finally:
                self.ws = None


    async def process_ws_message(self, msg):
        """Process incoming WebSocket messages."""
        try:
            data = json.loads(msg)
            msg_type = data.get('type')
            print(f"Received message type: {msg_type}")

            if msg_type == 'chat_notification':
                self.handle_chat_notification(data)

            elif msg_type == 'user_task_notification':
                task_data = data.get('task_data')
                self._updateTaskStack(task_data)

            elif msg_type == 'team_task_notification':
                self.handle_team_task_notification(data)

            elif msg_type == 'newTeam_notification':
                team_data = data.get('team_data')
                self._updateTeamStack(team_data)

            elif msg_type == 'task_create_confirmation':
                print(data)
            elif msg_type == 'team_create_confirmation':
                print(data)


        except json.JSONDecodeError:
            print(f"Invalid JSON received: {msg}")
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")


# WS response handlers

    def handle_chat_notification(self, data):
        """Handle chat notifications."""
        chat_data = data.get('chat_data')
        msg_data = data.get('msg_data')

        self._updateChatStack(chat_data)

        if self.active_navLink == 'Chats' and (chat_data['id'] == self.openedChatID or self.current_receiver_id):
            self.addMessage2Canvas(msg_data)
            self.msgCanvas.update_idletasks()
            self.msgCanvas.yview_moveto(1)
        else:
            # Notify user of new message ; like show a notification icon on respective chat and populateChat where latast msg chat is in top
            pass


    def handle_team_task_notification(self, data):
        """Handle task notifications."""
        print(data)
        pass



# WS create events
    def createMessage(self, event = None):
        """Create a new message via WebSocket."""
        if event and event.state & 0x1:  # Check if Shift key is pressed
            self.msgInput.insert(tk.INSERT, "\n")
            self.msgInput.configure(height=4)
        else:
            msgInp = self.msgInput.get("1.0", tk.END).strip()
            if msgInp and msgInp!="" and self.ws and (self.openedChatID or self.current_receiver_id):
                try:
                    dataToSend = {
                        'type': "message_create",
                        "msg": msgInp,
                        "chat_id": (self.openedChatID),
                        "user_id": (self.user_id),
                        "receiver_id" : (self.current_receiver_id)
                    }
                    asyncio.run(self.ws.send(json.dumps(dataToSend))) # Send message via WebSocket
                    self.msgInput.delete("1.0", tk.END)

                except Exception as e:
                    print(f"Error sending message: {e}")
            
        return 'break'  # Prevent default behavior of <Return> key


    def createTask(self, data):
        """Create a new task via WebSocket."""
        if data :
            try:
                dataToSend = {
                    'type': "task_create",
                    "task_data": data,
                    "user_id": (self.user_id),
                }
                asyncio.run(self.ws.send(json.dumps(dataToSend))) # Send message via WebSocket

            except Exception as e:
                print(f"Error creating task: {e}")


    def createTeam(self, data):
        if data :
            try:
                iconPath = data.get('icon')
                if iconPath not in ["", None]:
                    with open(iconPath, 'rb') as f:
                        icon_base64 = base64.b64encode(f.read()).decode('utf-8')

                    icon_data = {
                        "icon_base64": icon_base64,
                        "icon_ext": iconPath.split(".")[-1] 
                    }  
                else:
                    icon_data = None

                data['icon'] = icon_data

                dataToSend = {
                    'type': "team_create",
                    "team_data": data,
                    "user_id": (self.user_id),
                }
                asyncio.run(self.ws.send(json.dumps(dataToSend))) # Send message via WebSocket

            except Exception as e:
                print(f"Error creating task: {e}")


# initialization events
    def initMainUI(self):

        self.connectToWs()
        print("Login Success")

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
        if getattr(self,"user_isAdmin"):
            navLinks = [
                ("Dashboard", ("dashboard_gray", "dashboard_red")),
                ("Tasks", ("tasks_gray", "tasks_red")),
                ("Teams", ("teams_gray", "teams_red")),
                ("Chats", ("chats_gray", "chats_red")),
                ("Create User", ("groupDP", "groupDP")),
                ("Broadcast", ("groupDP", "groupDP")),
                ("Logout", ("logout_gray", "logout_red"))
            ]
        else:
            navLinks = [
                ("Dashboard", ("dashboard_gray", "dashboard_red")), 
                ("Tasks", ("tasks_gray", "tasks_red")),
                ("Teams", ("teams_gray", "teams_red")),
                ("Chats", ("chats_gray", "chats_red")),
                ("Logout", ("", "logout_red"))
            ]

        navLink_style = {
            'font': ('Arial', 13), 
            'bg': self.navbar.cget("bg"), 
            'fg': "white",  
            'bd': 0, 
            'padx': 10,  
            'justify': "left",
            'height': 35,
        }

        self.active_navLink = "Dashboard"
        self.nav_buttons = []
        self.nav_icons = []        
        
        for text, (inactive_icon, active_icon) in navLinks:
            icon_btn = tk.Button(
                self.navbar, 
                anchor=tk.CENTER,
                width= 35,
                command=lambda t=text: self.handleNavlinkClick(t), 
                **navLink_style
            )
            icon_btn.pack(pady=10, padx=5, fill=None)
            self.createTooltip(icon_btn, text)
            
            text_btn = tk.Button(
                self.navbar,
                text=text, 
                compound=tk.LEFT,
                anchor=tk.W,
                command=lambda t=text: self.handleNavlinkClick(t), 
                **navLink_style
            )

            if text == self.active_navLink:
                icon = self.icons.get(active_icon)
                icon_btn.config(image = icon, bg= self.bgs["bg5"])
                text_btn.config(image = icon, bg= self.bgs["bg5"])
            else:
                if text == "Logout":
                    icon = self.icons.get(active_icon)
                else:
                    icon = self.icons.get(inactive_icon)
                icon_btn.config(image = icon)
                text_btn.config(image = icon)

            self.nav_icons.append((icon_btn, text, inactive_icon, active_icon))
            self.nav_buttons.append((text_btn, text, inactive_icon, active_icon))

        # profile button
        profilePic = self.load_and_resize_img("userDP", self.user_dp)
        self.navbar.dp = profilePic
        profile_icon_btn = tk.Button(
            self.navbar,
            image=profilePic,
            anchor=tk.CENTER,
        )
        profile_icon_btn.pack(pady=10, padx=5, side="bottom")
        # self.nav_icons.append((profile_icon_btn, "Profile", inactive_icon, active_icon))

        # Content area
        self.content = tk.Frame(self.mainFrame, bg= self.bgs["bg_pri"])
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Initialize sections
        self.dashboard_frame = self.createDashboardUI()
        self.chats_frame = self.createChatsUI()
        self.tasks_frame = self.createTasksUI()
        self.teams_frame = self.createTeamsUI()

        # Show default section
        self.initDashboardUI()

    def initLoginUI(self):
        self.loginFrame = tk.Frame(self.mainFrame, bg= self.bgs["bg_pri"], padx=30, pady=30, bd=3, relief="flat")
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
        self.emailInput.bind("<Return>", lambda _: self.handleLoginClick()) 
        

        passwordLabel = tk.Label(self.loginFrame, text="Enter Password:", font=('Arial', 13, 'bold'), bg=self.loginFrame.cget("bg"), fg="#222")
        passwordLabel.pack(pady=5, anchor="w")

        self.passwordInput = tk.Entry(self.loginFrame, show = "*", **inputStyle)
        self.passwordInput.pack(pady=5, ipadx=5, ipady=5)
        self.passwordInput.bind("<Return>", lambda _: self.handleLoginClick())

        self.loginBtn = tk.Button(self.loginFrame, text="LOGIN", font=('Arial', 13), bg=self.bgs["bg1"], fg="white", pady=10, bd=0, width= 25, command=self.handleLoginClick)
        self.loginBtn.pack(pady=20)


    def initDashboardUI(self):
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
    
    def initChatsUI(self):
        self.chats_frame.pack(fill=tk.BOTH, expand=True)

    def initTasksUI(self):
        self.tasks_frame.pack(fill=tk.BOTH, expand=True)

    def initTeamsUI(self):
        self.teams_frame.pack(fill=tk.BOTH, expand=True)


    def initAddTaskModal(self, addTaskBtn):
        bgColor = self.bgs["bg4"]
        formFrame = tk.Frame(self.mainFrame, bg=bgColor, padx=30, pady=20)
        formFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        addTaskBtn.config(state="disabled")
        def closeModal():
            formFrame.destroy()
            addTaskBtn.config(state="normal")
   
        headerFrame = tk.Frame(formFrame, bg=bgColor)
        headerFrame.pack(fill="x", pady=(0, 20))

        # Title
        tk.Label(headerFrame, text="Add Task", font=('Arial', 16, 'bold'), bg=bgColor, fg="#fff").pack(side="left", pady=5)

        # Close button
        closeBtn = tk.Button(headerFrame, text="✕", font=('Arial', 12, 'bold'), bg="red", fg="#fff", bd=0, padx=8, pady=4)
        closeBtn.pack(side="right")
        closeTooltip= self.createTooltip(closeBtn, "Close")
        closeBtn.config(command= lambda: [closeTooltip.place_forget(), closeModal()])

        inputStyle = {"font": ('Arial', 12), "width": 40, "bg": "#fff", "bd": 0, "relief": "groove"}
        labelStyle = {"font": ('Arial', 13), "bg": bgColor, "fg": "#fff", "anchor": "w" }


        # Task Title
        tk.Label(formFrame, text="Task Title *", **labelStyle).pack(anchor="w")
        titleInput = tk.Entry(formFrame, **inputStyle)
        titleInput.pack(pady=(5, 15), ipadx=5, ipady=5)

        # Description
        tk.Label(formFrame, text="Description *", **labelStyle).pack(anchor="w")
        descInput = tk.Text(formFrame, height=4, **inputStyle)
        descInput.pack(pady=(5, 15))

        # Assignment Frame
        assignFrame = tk.Frame(formFrame, bg=bgColor)
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


        comboFrame = tk.Frame(formFrame, bg=bgColor)
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
        deadlineFrame = tk.Frame(formFrame, bg=bgColor, width= 40)
        deadlineFrame.pack(fill="x", pady=(5, 15))

        # Date picker 
        dateInput = tk.Entry(deadlineFrame, **{**inputStyle, 'width': 36})
        dateInput.pack(side="left", ipady=5)
        dateInput.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        
        calendarBtn = tk.Button(deadlineFrame, text="📅", font=('Arial', 12), width= 4, bg= self.bgs["bg_pri"], command=lambda: self.show_calendar(dateInput))
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
            command=lambda: validateForm()
        )
        submitBtn.pack(pady=20)

        # Fetch users and teams data
        self.asyncGetRequest("users/", lambda data: userCombo.configure(values=[f"{u['name']} ({u['id']})" for u in data]))
        self.asyncGetRequest("teams/", lambda data: teamCombo.configure(values=[f"{t['name']} ({t['id']})" for t in data]))

        def validateForm():
            if not titleInput.get():
                messagebox.showerror("Error", "Task title is required")
            elif not descInput.get("1.0", tk.END).strip():
                messagebox.showerror("Error", "Task description is required")
            elif assignType.get() == "user" and userCombo.get() == "Select User":
                messagebox.showerror("Error", "User or Team is required")
            elif assignType.get() == "team" and teamCombo.get() == "Select Team":
                messagebox.showerror("Error", "Team or User is required")                
            elif not dateInput.get():
                messagebox.showerror("Error", "Deadline is required")                
            else:
                self.createTask({
                    'title': titleInput.get(),
                    'desc': descInput.get("1.0", tk.END),
                    'assigned_user': userCombo.get() if assignType.get() == "user" else None,
                    'assigned_team': teamCombo.get() if assignType.get() == "team" else None,
                    'deadline': dateInput.get()
                })
                closeModal()

    def initContactModal(self, newChatBtn):
        bgColor = self.bgs["bg4"]
        
        frame = tk.Frame(self.content, bg=bgColor, padx=10, pady=10)
        frame.place(x = newChatBtn.winfo_x(), y = newChatBtn.winfo_y()+newChatBtn.winfo_height()+10, width=350, height=600)
        # frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=350, height=600)

        newChatBtn.config(state="disabled")
        def closeModal():
            frame.destroy()
            newChatBtn.config(state="normal")
            

        headerFrame = tk.Frame(frame, bg=frame.cget("bg"))
        headerFrame.pack(fill="x", pady=(0, 20))

        # Title
        tk.Label(headerFrame, text="New Chat", font=('Arial', 16, 'bold'), bg=headerFrame.cget("bg"), fg="#fff").pack(side="left", pady=5)

        closeBtn = tk.Button(headerFrame, text="✕", font=('Arial', 12, 'bold'), bg="red", fg="#fff", bd=0, padx=8, pady=4)
        closeBtn.pack(side="right")
        closeTooltip= self.createTooltip(closeBtn, "Close")
        closeBtn.config(command= lambda: [closeTooltip.place_forget(), closeModal()])

        canvas, canvasFrame = self.createScrollableCanvas(frame, bgColor)

        def populateContacts(data):
            for user in data:
                if user['id'] != self.user_id:
                    userFrame = tk.Frame(canvasFrame, bg=bgColor, cursor="hand2", pady=10, padx=10)
                    userFrame.pack(fill="x")

                    photo = self.load_and_resize_img("userDP", user.get('dp', None))         
                    userFrame.dp = photo  #Keep reference to prevent garbage collection
                    
                    dp_label = tk.Label(userFrame, image=photo, bg=bgColor, bd= 1, relief='solid', height=35, width=35)
                    dp_label.pack(side="left", padx=(0, 10))

                    fr = tk.Frame(userFrame, bg=bgColor)
                    fr.pack(side="left")

                    name = tk.Label(fr, text=user['name'], font=('Arial', 12), bg=bgColor, fg="#fff")
                    name.pack(side="top", anchor='w')

                    email = tk.Label(fr, text=user['email'], font=('Arial', 12), bg=bgColor, fg="#fff")
                    email.pack(side="bottom", anchor='w')

                    bindings ={
                        '<Enter>': lambda e, item=userFrame: self.hov_enter(item, self.bgs["bg4_mid"]),
                        '<Leave>': lambda e, item=userFrame: self.hov_leave(item, bgColor),
                        '<Button-1>': lambda e,u_id = user['id'], name = user['name'], icon = user['dp']: [closeModal(), self.handleChatClick({'receiver_id': u_id, 'name': name, 'icon': icon }, newChat = True)], 
                    }                    
                    self.applyBinding_recursively(userFrame, bindings)

        self.asyncGetRequest("users/", populateContacts)


    def initAddTeamModal(self, addTeamBtn):
        bgColor = self.bgs["bg4"]
        selected_users = set()
        
        formFrame = tk.Frame(self.content, bg=bgColor, padx=30, pady=20)
        formFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        addTeamBtn.config(state="disabled")
        def closeModal():
            formFrame.destroy()
            addTeamBtn.config(state="normal")
            

        headerFrame = tk.Frame(formFrame, bg=bgColor)
        headerFrame.pack(fill="x", pady=(0, 20))

        # Title
        tk.Label(headerFrame, text="Add Team", font=('Arial', 16, 'bold'), bg=bgColor, fg="#fff").pack(side="left", pady=5)

        closeBtn = tk.Button(headerFrame, text="✕", font=('Arial', 12, 'bold'), bg="red", fg="#fff", bd=0, padx=8, pady=4)
        closeBtn.pack(side="right")
        closeTooltip= self.createTooltip(closeBtn, "Close")
        closeBtn.config(command= lambda: [closeTooltip.place_forget(), closeModal()])

        inputStyle = {"font": ('Arial', 12), "width": 40, "bg": "#fff", "bd": 0, "relief": "groove"}
        labelStyle = {"font": ('Arial', 13), "bg": bgColor, "fg": "#fff", "anchor": "w" }


        # Task Title
        tk.Label(formFrame, text="Team Name *", **labelStyle).pack(anchor="w")
        nameInput = tk.Entry(formFrame, **inputStyle)
        nameInput.pack(pady=(5, 15), ipadx=5, ipady=5)

        # Description
        tk.Label(formFrame, text="Description *", **labelStyle).pack(anchor="w")
        descInput = tk.Text(formFrame, height=4, **inputStyle)
        descInput.pack(pady=(5, 15))

        #profile photo
        tk.Label(formFrame, text="Team Icon", **labelStyle).pack(anchor="w")
        iconInput = tk.Button(formFrame, text="Select Photo", command=lambda: select_image(iconInput), **inputStyle)
        iconInput.pack(pady=(5, 15))
        iconInput.filePath = None


        membersFrame = tk.Frame(formFrame, bg=formFrame.cget("bg"), height=200)
        membersFrame.pack(fill="x", pady=(5, 15))
        membersFrame.pack_propagate(False)

        tk.Label(membersFrame, text="Select Team Members", **labelStyle).pack(anchor="w")

        canvas, canvasFrame = self.createScrollableCanvas(membersFrame, bgColor)

        submitBtn = tk.Button(
            formFrame, 
            text="Create Team", 
            font=('Arial', 13),
            bg=self.bgs["bg5"], 
            fg="white", 
            pady=10, 
            bd=0, 
            width=25,
            command=lambda: validateForm()
        )
        submitBtn.pack(pady=20)

        def populateUsers(data):
            for user in data:
                userFrame = tk.Frame(canvasFrame, bg=bgColor, cursor="hand2", pady=5, padx=10)
                userFrame.pack(fill="x")
                userFrame.selected = False

                photo = self.load_and_resize_img("userDP", user.get('dp', None), (30, 30))         
                userFrame.dp = photo

                dp_label = tk.Label(userFrame, image=photo, bg=bgColor, bd= 1, relief='solid', height=30, width=30)
                dp_label.pack(side="left", padx=(0, 10))

                fr = tk.Frame(userFrame, bg=bgColor)
                fr.pack(side="left")

                name = tk.Label(fr, text=user['name'], font=('Arial', 11), bg=bgColor, fg="#fff")
                name.pack(side="top", anchor='w')

                email = tk.Label(fr, text=user['email'], font=('Arial', 11), bg=bgColor, fg="#fff")
                email.pack(side="bottom", anchor='w')

                bindings ={
                    '<Button-1>': lambda e,u_id = user['id'], fr= userFrame: toggle_selection(u_id, fr), 
                }                    
                self.applyBinding_recursively(userFrame, bindings)

        self.asyncGetRequest("users/", populateUsers, {"admin_include": True})


        def select_image(button):
            file_path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
            if file_path:
                button.config(text=self.truncate_chars(file_path, 30, placeholder="....", returnEnd = True))                
                button.filePath=file_path

        def toggle_selection(user_id, frame):
            def setBG(widget, bgc):
                widget.config(bg=bgc)
                [setBG(child, bgc) for child in widget.winfo_children()]

            if user_id in selected_users:
                selected_users.remove(user_id)
                frame.selected = True
                setBG(frame, bgColor)
                
            else:
                selected_users.add(user_id)
                frame.selected = False 
                setBG(frame, self.bgs["bg5"])

        def validateForm():
            if not nameInput.get():
                messagebox.showerror("Error", "Team Name is required")
            elif not descInput.get("1.0", tk.END).strip():
                messagebox.showerror("Error", "Description is required")
            elif not selected_users:
                messagebox.showerror("Error", "Please select at least one team member")
            else:
                self.createTeam({
                    'name': nameInput.get(),
                    'desc': descInput.get("1.0", tk.END),
                    'icon': iconInput.filePath,
                    'member_ids': list(selected_users),  
                })
                closeModal() 


#UI create events

    def createDashboardUI(self):
        """Create Dashboard UI."""
        bgPri = self.bgs["bg_pri"]    
        frame = tk.Frame(self.content, bg= bgPri)

        mainFrame = tk.Frame(frame, bg= "green", padx=10, pady=5)
        mainFrame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(mainFrame, text= "Dashboard", bg= bgPri, font=("Arial", 16, "bold")).pack(anchor=tk.W)


        notificationFrame = tk.Frame(frame, bg="red", padx=10, pady=5, width=400)
        notificationFrame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(notificationFrame, text= "Notifications", bg=bgPri, font=("Arial", 16, "bold")).pack(anchor=tk.W)

        canvas, canvasFrame =self.createScrollableCanvas(notificationFrame, "gray")
        


        def updateMainFrameWidth():
            frame_width = self.content.winfo_width() - 400
            mainFrame.configure(width=frame_width)

        self.content.bind("<Configure>", lambda e:updateMainFrameWidth())
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
        frame = tk.Frame(self.content, bg= self.bgs["bg_pri"])
        self.layout_1(frame, json.dumps(content))
        return frame


    def createTeamsUI(self):
        """Create Teams UI."""
        content = {
            "title": "Teams",
            "variablePrefix": "team",
            "api":{
                "endpoint": "teams/",
                # "callback": "populateTeams",
                "callback": "_updateTeamStack",
            },
            "defaultMsg": "Click on a team to see details.",
        }
        frame = tk.Frame(self.content, bg= self.bgs["bg_pri"])
        self.layout_1(frame, json.dumps(content))
        return frame


    def createTasksUI(self):
        content = {
            "title": "Tasks",
            "variablePrefix": "task",
            "filters":["TO DO", "IN PROGRESS", "COMPLETED"],
            "api":{
                "endpoint": "tasks/",
                "filter": "to do",
                # "callback": "populateTasks",
                "callback": "_updateTaskStack",
            },
            "defaultMsg": "Click on a task to view details.",
        }
        frame = tk.Frame(self.content, bg= self.bgs["bg_pri"])
        self.layout_1(frame, json.dumps(content))
        return frame


    def createScrollableCanvas(self, parentFrame, bgColor):
        """Creates a scrollable canvas with an inner frame.        
        Args:
            parentFrame: Parent frame to contain the canvas
            bgColor: Background color for canvas and inner frame        
        Returns:
            tuple: (canvas, canvasFrame) - The canvas, its inner frame 
        """
        canvas = tk.Canvas(parentFrame, bg=bgColor)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(10, 0))

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
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvasWindow, width=canvas.winfo_width() - 8))

        # Configure canvas frame 
        canvasFrame.bind(
            "<Configure>",
            lambda e: canvas.config(
                scrollregion=(0, 0, canvasFrame.winfo_reqwidth(), 
                            max(canvas.winfo_height(), canvasFrame.winfo_reqheight()))
            )
        )

        def hide_scrollbar_after_delay():
            if hasattr(canvas, '_scrollbar_timer'):
                canvas.after_cancel(canvas._scrollbar_timer)
            canvas._scrollbar_timer = canvas.after(1000, lambda: self.hideScrollbar(scrollbar))

        def on_mousewheel(event):            
            self.showScrollbar(scrollbar),
            hide_scrollbar_after_delay(),
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_scroll_to_widget(widget):
            widget.bind('<MouseWheel>', lambda e: on_mousewheel(e))

            for child in widget.winfo_children():
                bind_scroll_to_widget(child)

        canvas.bind('<MouseWheel>', lambda e: on_mousewheel(e))
        canvasFrame.bind('<Map>', lambda e: bind_scroll_to_widget(e.widget) )
        

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
            resp = requests.post(self.apiURL + 'login/', data = {"email": email, "password": password})
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


    def handleLogoutClick(self):
        async def _sessionCleanup():
            try:
                ## may not required to disconnect from ws for background notification
                # await self.disconnectfromWS() # WebSocket cleanup

                self.authToken = None
                self.ws = None
                self.user_id = None
                self.chatOrder = []
                self.chatData = {}
                self.taskStack = []
                self.openedTaskID = None

                if os.path.exists(self.TOKEN_FILE):
                    os.unlink(self.TOKEN_FILE) # Delete the token file

                return True
            
            except Exception as e:
                print(f"Error during session cleanup: {e}")
                return False
            
            
        if messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self.root, icon="warning"):
            try:
                resp = requests.post(self.apiURL + 'logout/', headers={"Authorization": f"Bearer {self.authToken}"})

                if resp.status_code == 200 and asyncio.run(_sessionCleanup()):
                    print("logout success")
                else:
                    raise Exception()


            except Exception as e:
                print("Error during logout: ", e)
                messagebox.showerror("Logout Failed", "An error occured. Please Try again")

            finally:
                [w.destroy() for w in self.root.winfo_children()] # Clear the UI

                # Reinitialize login screen
                self.mainFrame = tk.Frame(self.root, bg= self.bgs["gray_1"])
                self.mainFrame.pack(fill=tk.BOTH, expand=True)            
                self.authenticate()
    

    def handleNavlinkClick(self, section):
        if section.lower() != "logout":
            self.clear_content()

            for icon_btn, text, inactive_icon, active_icon in self.nav_icons:
                if section.lower() == text.lower():
                    icon_btn.config(image=self.icons.get(active_icon), bg=self.bgs["bg5"])
                else:
                    icon_btn.config(image=self.icons.get(inactive_icon), bg=self.bgs["bg1"])

            for text_btn, text, inactive_icon, active_icon in self.nav_buttons:
                if section.lower() == text.lower():
                    text_btn.config(image=self.icons.get(active_icon), bg=self.bgs["bg5"])
                else:
                    text_btn.config(image=self.icons.get(inactive_icon), bg=self.bgs["bg1"])        

        if section.lower() == "dashboard":
            self.initDashboardUI()
        elif section.lower() == "chats":
            self.initChatsUI()
        elif section.lower() == "tasks":
            self.initTasksUI()
        elif section.lower() == "teams":
            self.initTeamsUI()
        elif section.lower() == "logout":
            self.handleLogoutClick()
        
        self.active_navLink= section
        

    def handleChatClick(self, data, newChat = False):
        """Handle chat click event.
        Args:
            data (dict): Chat data.
            newChat (bool, optional): Whether the chat is new. Defaults to False.        
        """

        if newChat:
            chat_id = None
            chatMeta = {
                "name": data.get('name'),
                "icon": data.get('icon')
            }
            messages = None
            self.current_receiver_id = data.get('receiver_id')           
        else:
            chat_id = data.get('chat').get('id')
            chatMeta = data.get('chat').get('metaData')
            messages = data.get('messages')
            self.current_receiver_id = None


        if newChat or self.openedChatID != chat_id:

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

            bg1_light = self.bgs["bg1_light"]

            headerFrame = tk.Frame(msgPanelFrame, bg=bg1_light, padx=5, pady=10)
            headerFrame.pack(fill="x", side=tk.TOP)

            photo = self.load_and_resize_img("userDP", chatMeta.get('icon', None))         
            headerFrame.dp = photo  #Keep reference to prevent garbage collection
            
            dp_label = tk.Label(headerFrame, image=photo, bg=bg1_light, bd= 1, relief='solid', height=35, width=35)
            dp_label.pack(side="left", padx=(0, 10))

            infoFrame = tk.Frame(headerFrame, bg=bg1_light)
            infoFrame.pack(side="left")

            tk.Label(infoFrame, text=chatMeta.get('name'), bg=bg1_light, font=('Arial', 11, 'bold')).pack(anchor="w")
            

            self.msgCanvas, self.msgCanvasFrame = self.createScrollableCanvas(msgPanelFrame, "#fff")

            #msg input
            msgInputFrame = tk.Frame(msgPanelFrame, bg=self.bgs["bg1_light"], padx=5, pady=5, height=60)
            msgInputFrame.pack(fill="x",side=tk.BOTTOM)

            self.msgInput = tk.Text(msgInputFrame, bg= self.bgs["bg_pri"], font=('Arial', 12), name = "msgInput", height=1) 
            self.msgInput.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)

            self.msgInput.bind("<Return>", self.createMessage)

            tk.Button(
                msgInputFrame, 
                text="Send", 
                bg=self.bgs['bg3'], 
                fg="#fff", 
                font=('Arial', 12),
                cursor= 'hand2',
                command= self.createMessage
            ).pack(side=tk.RIGHT, padx=3, pady=5)


            #populate messages
            if messages:
                for msg in messages:
                    self.addMessage2Canvas(msg)                    
                self.msgCanvas.after(100, lambda: self.msgCanvas.yview_moveto(1))
                

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


    def handleTeamClick(self, data):
        teamDetailFrame = getattr(self,"team_rightPanelFrame")
        teamData = data.get('team')
        taskData = data.get('tasks')
        lastMsg = data.get('last_message')
        bg1_light = self.bgs["bg1_light"]

        for widget in teamDetailFrame.winfo_children():
            widget.destroy()


        headerFrame = tk.Frame(teamDetailFrame, bg=bg1_light, padx=5, pady=10)
        headerFrame.pack(fill="x", side=tk.TOP)

        photo = self.load_and_resize_img("teams_red", teamData.get('icon', None))
        headerFrame.dp = photo
         
        dp_label = tk.Label(headerFrame, image=photo, bg=bg1_light, bd= 1, relief='solid', height=35, width=35)
        dp_label.pack(side="left", padx=(0, 10))

        infoFrame = tk.Frame(headerFrame, bg=bg1_light)
        infoFrame.pack(side="left")

        tk.Label(infoFrame, text=teamData.get('name'), bg=bg1_light, font=('Arial', 11, 'bold')).pack(anchor="w")

        #member name string        
        text = ', '.join(member.get('name') for member in teamData.get('members'))
        text = self.truncate_chars(text, 160)
        tk.Label(infoFrame, text= text, bg=bg1_light, font=('Arial', 9)).pack(anchor="w")



        descFrame = tk.Frame(teamDetailFrame, bg=self.bgs['gray_2'], padx=10, pady=10)
        descFrame.pack(fill="x", side=tk.TOP)

        desc_label= tk.Label(descFrame, text=teamData.get('description') , bg=descFrame.cget('bg'), font=('Arial', 11))
        desc_label.pack(anchor="w")


        canvas, canvasFrame = self.createScrollableCanvas(teamDetailFrame, self.bgs["bg_pri"])

        if taskData:
            # clear canvasFrame
            for widget in canvasFrame.winfo_children():
                widget.destroy()

            for task in taskData:
                taskBG = self.bgs["bg1_mid"]

                taskFrame = tk.Frame(canvasFrame, bg= taskBG, padx=10, pady=10, bd=1, relief="solid", width=350)
                taskFrame.pack(anchor="e", expand=True, pady=8)

                f1 = tk.Frame(taskFrame, bg=taskBG, pady=5)
                f1.pack(anchor="w", fill="x")

                tk.Label(f1, text = 'Title: ', bg = taskBG, font = ('Arial', 12, 'bold')).pack(side=tk.LEFT, anchor="nw")
                tk.Label(f1, text = task.get('title').capitalize(), bg = taskBG, font = ('Arial', 12)).pack(side=tk.LEFT)


                f2 = tk.Frame(taskFrame, bg=taskBG, pady=3)
                f2.pack(anchor="w", fill="x")

                tk.Label(f2, text='Description:', bg=taskBG, font=('Arial', 12, 'bold')).pack(side=tk.LEFT, anchor="nw")
                tk.Label(f2, text=task.get('description').capitalize(), bg=taskBG, font=('Arial', 12), justify="left", wraplength= taskFrame.winfo_reqwidth() / 0.7).pack(side=tk.LEFT)


                f3 = tk.Frame(taskFrame, bg= taskBG, pady=3)
                f3.pack(anchor="w", fill="x")

                tk.Label(f3, text = 'Deadline: ', bg = taskBG, font = ('Arial', 12, 'bold'), pady=5).pack(side=tk.LEFT, anchor="nw")
                tk.Label(f3, text = task.get('deadline'), bg = taskBG, font = ('Arial', 12), pady=5).pack(side=tk.LEFT)


                f4 = tk.Frame(taskFrame, bg= taskBG, pady=3)
                f4.pack(anchor="w", fill="x")

                tk.Label(f4, text = 'Status: ', bg = taskBG, font = ('Arial', 12, 'bold'), pady=5).pack(side=tk.LEFT, anchor="nw")
                tk.Label(f4, text = task.get('status').upper(), bg = taskBG, font = ('Arial', 12), pady=5).pack(side=tk.LEFT)
                

                fr5= tk.Frame(taskFrame, bg=taskBG, pady=3)
                fr5.pack(anchor="w", fill="x")

                tk.Label(fr5, text = 'No of SubTask: ', bg = taskBG, font = ('Arial', 12, 'bold'), pady=5).pack(side=tk.LEFT, anchor="nw")
                tk.Label(fr5, text = task.get('subtaskCount'), bg = taskBG, font = ('Arial', 12), pady=5).pack(side=tk.LEFT)


                fr6= tk.Frame(taskFrame, bg=taskBG, pady=3)
                fr6.pack(anchor="w", fill="x")

                tk.Label(fr6, text = 'Progress: ', bg = taskBG, font = ('Arial', 12, 'bold'), pady=5).pack(side=tk.LEFT)
                ttk.Progressbar(
                    fr6, 
                    maximum=100, 
                    mode="determinate",
                    value=task.get('progress', 00), 
                    length=taskFrame.winfo_reqwidth() / 0.95
                ).pack(side=tk.LEFT, pady=5, padx=5)
                tk.Label(fr6, text=f"{task.get('progress', 00)}%", bg=taskBG, fg=self.bgs['bg5'], font=('Arial', 11, 'bold')).pack(side=tk.LEFT, pady=5)

            canvas.after(100, lambda: canvas.yview_moveto(1))
                
        else:
            tk.Label(canvasFrame, text="No tasks available", bg=canvasFrame.cget('bg'), font=('Arial', 12), pady=10).pack(anchor="center")





        lastMsgFrame = tk.Frame(teamDetailFrame, height=60, padx=5, pady=5, bg= self.bgs["gray_1"])
        lastMsgFrame.pack(fill="x", side=tk.BOTTOM, pady=(5, 0))

        tk.Label(lastMsgFrame, text="Last Message", bg=lastMsgFrame.cget('bg'), font=('Arial', 14, "bold")).pack(anchor="center")

        bubbleFrame = tk.Frame(lastMsgFrame, bg=self.bgs["green_1"], padx=5, pady=5, bd=1, relief="solid")
        bubbleFrame.pack(fill="x", expand=True, side="left", pady=5)

        if lastMsg:
            senderData = lastMsg.get('sender')
            photo = self.load_and_resize_img("userDP", senderData.get('dp'))
            bubbleFrame.dp = photo

            dp_label = tk.Label(bubbleFrame, image=photo, bg=bubbleFrame.cget('bg'), bd= 1, relief='solid', height=35, width=35)
            dp_label.pack(side="left", anchor="nw")

            fr = tk.Frame(bubbleFrame, bg=bubbleFrame.cget('bg'))
            fr.pack(fill="x", side="top")

            tk.Label(fr, text=senderData.get('name'), bg=bubbleFrame.cget('bg'), font=('Arial', 11, 'bold')).pack(anchor="w", side="left", padx=(5, 10))

            tk.Label(fr, text=lastMsg.get('timestamp'), bg=bubbleFrame.cget('bg'), font=('Arial', 10, 'italic')).pack(anchor="w", side="left")


            msgTxt = self.truncate_chars(lastMsg.get('content'), 180, ".....") 

        else:
            msgTxt = "No messages yet"

        msg_label= tk.Label(bubbleFrame, text=msgTxt, bg=bubbleFrame.cget('bg'), font=('Arial', 11))
        msg_label.pack( side="left", padx=5)
        
        def update_desc_and_msg_wraplength(event = None):
            width = teamDetailFrame.winfo_width() - 70
            desc_label.config(wraplength=width)
            msg_label.config(wraplength=width)
            
        teamDetailFrame.bind("<Configure>", update_desc_and_msg_wraplength)
        update_desc_and_msg_wraplength()



        


#populate function
    def populateChat(self):
        panelBG = self.bgs["bg1_light"]
        canvasFrame = getattr(self,"chat_canvasFrame")
        
        for widget in canvasFrame.winfo_children():
            widget.destroy()
        
        
        if not self.chatOrder:
            tk.Label(canvasFrame, bg = panelBG, text = "Your Chatlist is Empty.", font=('Arial', 13)).pack(padx=5, pady=10)
            return

        for chat_id in self.chatOrder:
            chat = self.chatData[chat_id]
            meta = chat.get('metaData')
            lastMsg = chat.get('last_msg')
            msgTxt = ""

            # print(meta)
            chatFrame = tk.Frame(canvasFrame, bg= panelBG, cursor="hand2", pady=10, padx=10)
            chatFrame.pack(fill="x")
            
            default_img = "groupDP" if chat['is_group_chat'] else "userDP"
            photo = self.load_and_resize_img(default_img, meta.get('icon', None))
            chatFrame.dp = photo # reference to prevent garbage collection
            
            dp_label = tk.Label(chatFrame, image=photo, bg=panelBG, bd= 1, relief='solid', height=35, width=35)
            dp_label.pack(side="left", padx=(0, 10))
        
            info_frame = tk.Frame(chatFrame, bg=panelBG)
            info_frame.pack(fill="x")

            name_label = tk.Label(info_frame, text=self.truncate_chars(meta['name'], 20), bg=panelBG, font=('Arial', 12))
            name_label.pack(anchor="w", side="left")
            timestamp_label = tk.Label(info_frame, text=lastMsg.get('timestamp'), bg=panelBG, font=('Arial', 8))
            timestamp_label.pack(anchor="w", side="right")

            if 'sender' in lastMsg:
                msgTxt = f"{lastMsg.get('sender')['name']}: {lastMsg.get('content')}" if chat['is_group_chat'] else lastMsg.get('content')
                msgTxt = self.truncate_chars(msgTxt, 40)

            lastMsg_label = tk.Label(chatFrame, text= msgTxt, bg=panelBG, font=('Arial', 9))
            lastMsg_label.pack(anchor="w")

            bindings ={
                '<Enter>': lambda e, frame=chatFrame: self.hov_enter(frame, self.bgs["bg1_mid"]),
                '<Leave>': lambda e, frame=chatFrame: self.hov_leave(frame, panelBG),
                '<Button-1>': lambda e,c_id = chat_id: 
                            self.asyncGetRequest(
                                endpoint = f'chats/{c_id}/',
                                callback = self.handleChatClick
                            ),
            }

            self.applyBinding_recursively(chatFrame, bindings)          
            
    def populateTasks(self):  
        panelBG = self.bgs["bg1_light"]
        canvasFrame = getattr(self,"task_canvasFrame")

        for widget in canvasFrame.winfo_children():
            widget.destroy()
        
        if len(self.taskData) == 0:
            tk.Label(canvasFrame, text="No Tasks Available.", bg=panelBG, font=('Arial', 13)).pack(anchor="center", pady=10)
            return
        
        for task in self.taskData:
            print(type(task))
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
            tk.Label(taskFrame, text=task.get('title'), bg=panelBG, font=('Arial', 12)).pack(anchor="w")
            tk.Label(taskFrame, text=f"Deadline: {deadline}", bg=panelBG, fg = color, font=('Arial', 9)).pack(anchor="w")


            bindings ={               
                '<Enter>': lambda e, frame=taskFrame: [self.hov_enter(frame, self.bgs["bg1_mid"])],
                '<Leave>': lambda e, frame=taskFrame: [self.hov_leave(frame, panelBG)],
                '<Button-1>': lambda e,t_id = task_id, isSubtask = task.get('is_subtask'):
                            self.asyncGetRequest(
                                endpoint=f'tasks/{t_id}', callback=self.handleTaskClick, params={"isSubtask": isSubtask}
                            ),
            }

            self.applyBinding_recursively(taskFrame, bindings)
    
    def populateTeams(self): 
        panelBG = self.bgs["bg1_light"]
        canvasFrame = getattr(self,"team_canvasFrame")

        for widget in canvasFrame.winfo_children():
            widget.destroy()

        if len(self.teamData) == 0:
            tk.Label(canvasFrame, text="You are not a team member yet.", bg=panelBG, font=('Arial', 13)).pack(anchor="center", pady=10)
            return
        
        for team in self.teamData:
            team_id = team['id']
            teamFrame = tk.Frame(canvasFrame, bg= panelBG, cursor="hand2", pady=10, padx=10)
            teamFrame.pack(fill="x")

            photo = self.load_and_resize_img("teams_red", team.get('icon', None))
            teamFrame.dp = photo # reference to prevent garbage collection
            
            dp_label = tk.Label(teamFrame, image=photo, bg=panelBG, bd= 1, relief='solid', height=35, width=35)
            dp_label.pack(side="left", padx=(0, 10))
        
            info_frame = tk.Frame(teamFrame, bg=panelBG)
            info_frame.pack(fill="x")
            
            tk.Label(info_frame, text=team.get('name'), bg=panelBG, font=('Arial', 12)).pack(anchor="w")
            
            tk.Label(info_frame, text=f"Members: {len(team.get('members'))}", bg=panelBG, font=('Arial', 9)).pack(anchor="w")

            bindings ={
                '<Enter>': lambda e, frame=teamFrame: self.hov_enter(frame, self.bgs["bg1_mid"]),
                '<Leave>': lambda e, frame=teamFrame: self.hov_leave(frame, panelBG),
                '<Button-1>': lambda e, t_id= team.get('id'): self.asyncGetRequest(
                                endpoint = f'teams/{t_id}/',
                                callback = self.handleTeamClick
                            ),
            }

            self.applyBinding_recursively(teamFrame, bindings)          


# helper functions
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
            # Collapse navbar
            self.navbar.configure(width=50)
            for text_btn, _, _, _ in self.nav_buttons:
                text_btn.pack_forget()
            for icon_btn, _, _, _ in self.nav_icons:
                icon_btn.pack(pady=10, padx=5, fill= None)
        else:
            # Expand navbar
            self.navbar.configure(width=200)
            for icon_btn, _, _, _ in self.nav_icons:
                icon_btn.pack_forget()
            for text_btn, _, _, _ in self.nav_buttons:
                text_btn.pack(pady=10, padx=5, fill=tk.X)

        self.is_navbar_expanded = not self.is_navbar_expanded


    def hov_enter(self, chat_widget, bgc):
        def add_config(widget):
            widget.config(bg=bgc)
            for w in widget.winfo_children():
                add_config(w)

        if not hasattr(self, "activeChat") or chat_widget != self.activeChat:
            add_config(chat_widget)


    def hov_leave(self, chat_widget, bgc):
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
            
        msgFrame = tk.Frame(self.msgCanvasFrame, bg= self.bgs["bg_pri"])
        msgFrame.pack(pady=5, padx=10, anchor="e" if align == "right" else "w")

        bubble_frame = tk.Frame(
            msgFrame,
            bg=self.bgs['green_1'] if align == "right" else self.bgs['gray_2'],
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
            # justify= "left",
            wraplength= getattr(self,"chat_rightPanelFrame").winfo_width()*0.7
        )
        message_label.pack(anchor="w")

        time_label = tk.Label(bubble_frame, text= msgData["timestamp"], bg=bubble_frame.cget("bg"), fg="#374747", font=('Arial', 8, 'italic'), padx=5)
        time_label.pack(anchor="e")

        getattr(self, "chat_rightPanelFrame").bind("<Configure>", self._update_message_label_wraplength)
    

    def asyncGetRequest(self, endpoint: str, callback, params=None):
        """ Asynchronous GET request to the API. Calls the provided callback function with the response data.

        Args:
            endpoint (str): API endpoint.
            callback (function): Callback function to handle the response data.
            params (dict, optional): Parameters for the GET request.
        """
        def run():
            header = {"Authorization": f"Bearer {self.authToken}"}
            try:
                resp = requests.get(self.apiURL + endpoint, headers=header, params=params)
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
            'newTeam': 'icons/newTeam.png',
            'groupDP': 'icons/people.png',
            'userDP': 'icons/person.png',
            'dashboard_red': 'icons/dashboard_red.png',
            'dashboard_gray': 'icons/dashboard_gray.png',
            'tasks_red': 'icons/task_red.png',
            'tasks_gray': 'icons/task_gray.png',
            'teams_red': 'icons/team_red.png',
            'teams_gray': 'icons/team_gray.png',
            'chats_red': 'icons/chat_red.png',
            'chats_gray': 'icons/chat_gray.png',
            'logout_red': 'icons/logout_red.png',
            # Add more icons here as needed
        }
        
        try:
            for icon_name, icon_path in icon_files.items():
                if os.path.exists(icon_path):
                    self.icons[icon_name] = ImageTk.PhotoImage(Image.open(icon_path))
        except Exception as e:
            print(f"Error loading icons: {e}")


    def load_and_resize_img(self, default_img, path=None, size=(35,35)):
        """Load and resize an image from a URL or use a default image.
        Args:
            default_img (str): Default image name.
            path (str, optional): Path to the image. Defaults to None.
            size (tuple, optional): Size to resize the image. Defaults to (35, 35).
        Returns:
            ImageTk.PhotoImage: Resized image.
        """
        try:
            if path :
                response = requests.get(f"{self.baseURL}{path}")
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    image = image.resize(size, Image.Resampling.LANCZOS)  # Resize image
                    photo = ImageTk.PhotoImage(image)
            else:
                photo = self.icons.get(default_img)
            return photo

        except Exception as e:
            print(f"Error processing img: {e}")
            return None

    def showScrollbar(self, scrollbar):
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def hideScrollbar(self, scrollbar):
        scrollbar.pack_forget()


    def truncate_chars(self, text:str, no_of_char:int = 40, placeholder="…", remove_newlines=True, returnEnd = False):
        """Truncates a string to a specified number of characters.
        Args:
            text (str): The input text.
            no_of_char (int, optional): The maximum number of characters to include. Defaults to 40.
            placeholder (str, optional): The placeholder to indicate truncation. Defaults to "…".   
            remove_newlines (bool, optional): Whether to remove newlines from the text. Defaults to True.
            returnEnd (bool, optional): Whether to return the end of the string. Defaults to False.
        Returns:
            str: The truncated text.
        """
        if remove_newlines:
            text = text.replace("\n", " ")

        if len(text) <= no_of_char:
            return text
        if returnEnd:
            return placeholder + text[-no_of_char:]
        return text[:no_of_char - len(placeholder)] + placeholder
        

    def applyBinding_recursively(self, widget, bindings: dict):
        """Recursively applies key bindings to a widget and its children.."""
        for event, func in bindings.items():
            widget.bind(event, func)
            for child in widget.winfo_children():
                self.applyBinding_recursively(child, bindings)


    def createTooltip(self, widget, text, bgColor = "#333"):
        """Creates a tooltip for a widget.
        Args:
            widget (tk.Widget): The widget to which the tooltip will be applied.
            text (str): The text to display in the tooltip.
            bgColor (str, optional): The background color of the tooltip. Defaults to "#333".
        """
            
        tooltip = tk.Label(
            self.root,
            text=text,
            bg=bgColor,
            fg="white",
            font=('Arial', 10),
            padx=5,
            pady=2,
            borderwidth=1,
            relief="solid"
        )

        def show_tooltip(event, label=tooltip, button=widget):
            x = button.winfo_rootx() - self.root.winfo_rootx() + button.winfo_width()
            y = button.winfo_rooty() - self.root.winfo_rooty() + button.winfo_height() + 3
            label.place(x=x, y=y, anchor="n")

        def hide_tooltip(event, label=tooltip):
            label.place_forget()
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

        return tooltip


#RELOAD function 



#UI layout

    def layout_1(self, frame, content):
        content = json.loads(content)
        endpoint = content.get("api").get("endpoint")
        callback_name = content.get("api").get("callback")
        filter_val = content.get("api").get("filter", None)

        titleTxt = content.get("title")

        panelBG = self.bgs["bg1_light"]

        leftPanalFrame = tk.Frame(frame, bg=panelBG, width=350, padx=5, pady=5)
        leftPanalFrame.pack(side=tk.LEFT, fill=tk.Y)
        leftPanalFrame.pack_propagate(False)

        fr = tk.Frame(leftPanalFrame, bg=panelBG)
        fr.pack(side=tk.TOP, anchor=tk.W, fill=tk.X, padx=10, pady=(0,10))
        
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
            btn.config(command= lambda b=btn: self.initAddTaskModal(b))
            btn.pack(side=tk.RIGHT, anchor=tk.W, ipadx= 6, ipady = 6)
            self.createTooltip(btn, "New Task")
            
        elif titleTxt.lower() in ["team", "teams"] and self.user_isAdmin == True:
            btn = tk.Button(
                fr,
                image= self.icons.get("newTeam"),
                bg=self.bgs["bg4"],
                activebackground=self.bgs['bg1_mid2'],
                bd=0,
                pady=4,
                cursor="hand2",
            )

            btn.pack(side=tk.RIGHT, anchor=tk.W, ipadx= 6, ipady = 6)
            btn.config(command= lambda b=btn: self.initAddTeamModal(b))
            self.createTooltip(btn, "New Team")

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
            btn.config(command= lambda b=btn: self.initContactModal(b))
            self.createTooltip(btn, "New Chat")


        filterBtns = []
        if content.get("filters"):
            filterFrame = tk.Frame(leftPanalFrame, bg=panelBG, pady=5, padx=5)
            filterFrame.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)

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

        rightPanelFrame = tk.Frame(frame, bg= self.bgs["bg_pri"], padx=5, pady=5)
        rightPanelFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        defaultFrame = tk.Frame(rightPanelFrame)
        defaultFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(defaultFrame, text="K Collab", bg=defaultFrame.cget('bg'), font=('Arial', 18, 'bold')).pack()

        tk.Label(defaultFrame, text=content.get("defaultMsg"), bg=defaultFrame.cget('bg'), font=('Arial', 12)).pack()

        # creating dynamic global variables
        prefix = content.get("variablePrefix")
        setattr(self, f"{prefix}_canvas", canvas)
        setattr(self, f"{prefix}_canvasFrame", canvasFrame)
        setattr(self, f"{prefix}_rightPanelFrame", rightPanelFrame)
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

        resp = requests.put(f"{self.apiURL}tasks/{task_id}/", headers= {"Authorization": f"Bearer {self.authToken}"}, data = data)

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
            params = {"filter": filter_val}
            for btn in filterBtns:
                # update active filter btn
                if btn.cget("text").lower() == filter_val:
                    btn.config(bg=self.bgs["bg5"])
                else:
                    btn.config(bg=self.bgs["bg4"])
        else:
            params = {}

        if callback_name and endpoint:
            callback_func = getattr(self, callback_name, None) 
            if callable(callback_func):
                self.asyncGetRequest(endpoint, callback_func, params)
        

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

    
    
    def _updateTaskStack(self, task_data):
        if isinstance(task_data, list):
            self.taskData =[]
            for task in task_data:
                self.taskData.append(task)
        else:
            # Single chat update
            self.taskData.insert(0, task_data)

        self.populateTasks()

    def _updateTeamStack(self, team_data):
        if isinstance(team_data, list):
            self.teamData =[]
            for team in team_data:
                self.teamData.append(team)
        else:
            # Single chat update
            self.teamData.insert(0, team_data)

        self.populateTeams()



    def _update_message_label_wraplength(self, event = None):
        """Update the wraplength of the message labels in the chat."""
        if hasattr(self, "msgCanvasFrame"):
            width = getattr(self, 'chat_rightPanelFrame').winfo_width() * 0.7
            for msg_frame in self.msgCanvasFrame.winfo_children():
                bubble_frame = msg_frame.winfo_children()[0]
                if bubble_frame.winfo_width() >200:
                    for widget in bubble_frame.winfo_children():
                        widget.config(wraplength=width)


if __name__ == "__main__":
    root = tk.Tk()
    app = KCollabApp(root)
    root.mainloop()