import tkinter as tk
from tkinter import ttk

class App:
    def __init__(self, root):
        print("App running ...")
        self.root = root
        self.root.geometry("1000x600")
        self.root.title("K_Collab")

        # Main layout
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Navbar
        self.navbar = tk.Frame(self.main_container, width=50, bg="#2c3e50")
        self.navbar.pack(side=tk.LEFT, fill=tk.Y)
        self.navbar.pack_propagate(False)

        # Hamburger button
        self.is_navbar_expanded = False
        hamburger_btn = tk.Button(
            self.navbar,
            text="☰", 
            font=('Arial', 16), 
            bg="#2c3e50", fg="white",
            pady=10, 
            bd=0, 
            command=self.toggle_navbar
        )
        hamburger_btn.pack(pady=5, padx=5, anchor="w")

        # Navbar buttons
        navLinks = [("Dashboard", "📊"), ("Chats", "💬"), ("Tasks", "📋")]
        navLink_style = {'font': ('Arial', 14), 'bg': "#2c3e50", 'fg': "white", 'pady': 10, 'bd': 0, 'padx': 10, 'anchor': "w", 'justify': "left"}
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
        self.dashboard_frame = self.create_dashboard()
        self.chats_frame = self.create_chats()
        self.tasks_frame = self.create_tasks()

        # Show default section
        self.show_dashboard()

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

    def create_dashboard(self):
        """Create Dashboard UI."""
        frame = tk.Frame(self.content, bg="white")
        tk.Label(frame, text="Dashboard", font=('Arial', 24), bg="white").pack(pady=20)
        return frame

    def create_chats(self):
        """Create Chats UI."""
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
        for i in range(20):
            chat_id = i + 1
            chat = tk.Frame(chat_frame, bg="white", pady=10, padx=5)
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
    
    def create_tasks(self):
        """Create Tasks UI."""
        frame = tk.Frame(self.content, bg="white")
        tk.Label(frame, text="Tasks Section", font=('Arial', 24), bg="white").pack(pady=20)
        return frame



    def show_messages(self, chat_id):
        print(f"Showing chat {chat_id}")

        # Clear previous messages
        for widget in self.message_frame.winfo_children():
            widget.destroy()

        # Sample messages
        chat_messages = {
            1: [
                ("👋 Welcome to the Project Discussion!", "left"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Thanks! Excited to be here", "right"),
                ("Let's discuss the new features", "left"),
                ("I've prepared some mockups", "right")
            ],
            2: [
                ("🎨 Design Team Updates", "left"),
                ("The new color scheme looks great!", "right"),
                ("Should we adjust the typography?", "left"),
                ("Yes, I think that would help", "right")
            ],
            3: [
                ("🚀 Sprint Planning", "left"),
                ("What's our velocity target?", "right"),
                ("Aiming for 20 story points", "left"),
                ("Sounds achievable", "right")
            ],
            4: [
                ("📊 Analytics Review", "left"),
                ("User engagement is up 25%", "right"),
                ("That's fantastic news! 🎉", "left"),
                ("What drove the increase?", "right")
            ],
            5: [
                ("🐛 Bug Reports", "left"),
                ("Found an issue in production", "right"),
                ("Can you share more details?", "left"),
                ("Sending screenshots now...", "right")
            ],
            6: [
                ("📱 Mobile App Discussion", "left"),
                ("iOS version is ready for testing", "right"),
                ("Great! When can we start?", "left"),
                ("I'll set up TestFlight today", "right")
            ],
            7: [
                ("🔒 Security Updates", "left"),
                ("New authentication flow", "right"),
                ("Is 2FA implemented?", "left"),
                ("Yes, testing complete", "right")
            ],
            8: [
                ("💡 Innovation Ideas", "left"),
                ("What about AI integration?", "right"),
                ("Interesting possibility!", "left"),
                ("I'll draft a proposal", "right")
            ],
            9: [
                ("📈 Performance Review", "left"),
                ("Load times improved by 40%", "right"),
                ("Excellent optimization!", "left"),
                ("More improvements coming", "right")
            ],
            10: [
                ("🤝 Team Collaboration", "left"),
                ("New team member joining", "right"),
                ("When do they start?", "left"),
                ("Next Monday! 📅", "right")
            ]
        }
        messages = chat_messages.get(chat_id, [
            ("No messages yet", "left"),
            ("Start a conversation!", "right")
        ])

        for msg, align in messages:
            msg_frame = tk.Frame(self.message_frame, bg="white")
            msg_frame.pack(pady=5, padx=10, anchor="w" if align == "left" else "e")

            bubble_frame = tk.Frame(
                msg_frame,
                bg="#e6e6e6" if align == "left" else "#dcf8c6",
                bd=1,
                relief="solid"
            )
            bubble_frame.pack(side="left" if align == "left" else "right")

            tk.Label(
                bubble_frame,
                text=msg,
                wraplength=280,
                bg=bubble_frame.cget("bg"),
                pady=8,
                padx=12
            ).pack()

   

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


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
