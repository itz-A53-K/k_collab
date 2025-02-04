import tkinter as tk
from tkinter import ttk
import requests, json


class ChatApp:
    def __init__(self, root):
        print("app running ....")
        self.root = root
        self.root.title("Chat App")
        self.root.geometry("800x600")
        self.card_width = 200
        self.card_height = 200
        self.createNav()
        self.chats = None

        resp = requests.post(base_url + 'login/' , data={"email": "abi@kcollab.in", "password": "1234"})
        self.authToken = resp.json()['authToken']   
        self.getAPIdata()
        
    def getAPIdata(self):
        authDetail = {"authToken": self.authToken}
        chats = requests.get(base_url + 'chats/', headers= authDetail)
        print(chats.json())

    def update_columns(self):
        window_width = self.body.winfo_width()
        self.columns = window_width // self.card_width
        if self.columns == 0:  # To ensure at least one column is shown
            self.columns = 1

    def createNav(self):
        self.navbar = tk.Frame(root, width=300, bg="lightgray")
        self.navbar.pack(side="left", fill="y")

        self.body = tk.Frame(root, bg="white")
        self.body.pack(side="right", expand=True, fill="both")

        navLinks = ["dashboard", "chat", 'tasks']
        for link in navLinks:
            self.btn = ttk.Button(self.navbar, text=link, command=lambda link=link: self.show_content(link))
            self.btn.pack(fill="x", padx=15)

    def show_content(self, text):
        for widget in self.body.winfo_children():
            widget.destroy()
            
        if text == "dashboard":
            self.show_dashboard()
        elif text == "chat":
            self.show_chat()
        elif text == "tasks":
            self.update_columns()
            self.show_tasks()


    def show_dashboard(self):
        # dashboard content
        dashboard_label = tk.Label(self.body, text="Dashboard Content", font=("Arial", 14))
        dashboard_label.pack(pady=20)
    
    def show_chat(self):
        # request to api for data to show
        
        # Create frames for the sidebar and main chat area
        sidebar_frame = tk.Frame(self.body, width=200, bg="#2C3E50", height=600, relief="sunken")
        sidebar_frame.grid(row=0, column=0, sticky="ns")
        
        chat_frame = tk.Frame(self.body, bg="#ECF0F1", height=600, width=600)
        chat_frame.grid(row=0, column=1, sticky="nsew")
        
        # Chat List (Sidebar)
        chat_listbox = tk.Listbox(sidebar_frame, bg="#34495E", fg="white", font=("Arial", 12), height=30)
        chat_listbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add dummy chats to the sidebar
        chats = ["Chat 1", "Chat 2", "Chat 3"]
        for chat in chats:
            chat_listbox.insert(tk.END, chat)
        
        # Chat area (Main window)
        chat_area = tk.Text(chat_frame, bg="#ECF0F1", fg="black", font=("Arial", 12), wrap=tk.WORD, state=tk.DISABLED)
        chat_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create input area
        input_frame = tk.Frame(chat_frame, bg="#ECF0F1", height=50)
        input_frame.grid(row=1, column=0, sticky="ew", pady=10, padx=10)
        
        entry = tk.Entry(input_frame, bg="#BDC3C7", font=("Arial", 12))
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        send_button = tk.Button(input_frame, text="Send", font=("Arial", 12), bg="#2980B9", fg="white")
        send_button.grid(row=0, column=1)
        
        # Sidebar scroll functionality
        scrollbar = tk.Scrollbar(sidebar_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        chat_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=chat_listbox.yview)

        # Configure weight for resizing
        chat_frame.grid_rowconfigure(0, weight=1)  # Make chat_area expand vertically
        chat_frame.grid_columnconfigure(0, weight=1)  # Make chat_area expand horizontally
        sidebar_frame.grid_rowconfigure(0, weight=1)  # Allow sidebar to expand vertically

    




    def show_tasks(self):

        resp = requests.get(base_url + 'tasks/' , cookies={'authToken': self.authToken})

        if resp.status_code == 200:
            tasks = resp.json()
            for idx in range(20):
                row, col = divmod(idx, self.columns)
                card = tk.Frame(self.body, width=self.card_width, height=self.card_height, bg="pink", padx=10, pady=10)
                card.grid(row=row, column=col, padx=10, pady=10)

                # task_label = tk.Label(card, text=task['title'], font=("Arial", 12))
                # task_label.pack(pady=5)
        
        else:
            print(f"Error: {resp.status_code}")
                


                


        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("My Tkinter App")

    base_url = "http://127.0.0.1:8000/api/"
    app = ChatApp(root)

    # sidebar = tk.Frame(root, width=150, bg="gray")
    # sidebar.pack(side="left", fill="y")

    # # Create a main content frame
    # main_content = tk.Frame(root, bg="white")
    # main_content.pack(side="right", expand=True, fill="both")

    # # Add buttons to sidebar
    # def show_content(text):
    #     for widget in main_content.winfo_children():
    #         widget.destroy()
    #     label = tk.Label(main_content, text=text, font=("Arial", 14))
    #     label.pack(pady=20)

    # btn1 = tk.Button(sidebar, text="Home", command=lambda: show_content("Home Page"))
    # btn1.pack(pady=10, fill="x")

    # btn2 = tk.Button(sidebar, text="Profile", command=lambda: show_content("Profile Page"))
    # btn2.pack(pady=10, fill="x")

    # btn3 = tk.Button(sidebar, text="Settings", command=lambda: show_content("Settings Page"))
    # btn3.pack(pady=10, fill="x")



    root.mainloop()
