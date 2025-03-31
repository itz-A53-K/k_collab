# K-Collab

K-Collab is a collaborative platform with a Django REST backend and Tkinter desktop client that includes user management, team management, task management, and real-time chat functionality using WebSockets.

## Features

- User Authentication with Token-based Authentication
- Team Management with Integrated Group Chats
- Task & Subtask Management System
- Real-time Individual & Group Chat functionality using WebSockets
- Desktop Client UI with Tkinter
- Real-time Message Updates and Notifications

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/k_collab.git
    ```

2. Create and activate virtual environment:
    ```bash
    python -m venv venv
    venv/Scripts/activate  # Windows
    source venv/bin/activate  # Linux/Mac
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Run migrations:
    ```bash
    python manage.py migrate
    ```

5. Create superuser:
    ```bash
    python manage.py createsuperuser
    ```

6. Start the Daphne server (for WebSocket support):
    ```bash
    set DJANGO_SETTINGS_MODULE=k_collab.settings
    daphne k_collab.asgi:application
    <!-- daphne k_collab.asgi:application --bind 0.0.0.0 --port 8000 -->
    ```

7. Launch desktop client:
    ```bash
    python app.py
    ```

## WebSocket Features

- Real-time message delivery
- Automatic chat group management
- New chat notifications
- Live message updates
- WebSocket endpoint: `ws://localhost:8000/ws/chat/`

## API Endpoints

### Authentication
- **Login**: `POST /api/login/`
  - Request: `{"email": "user@example.com", "password": "password"}`
  - Response: `{"message": "Login successful", "authToken": "token"}`

- **Logout**: `POST /api/logout/`
  - Requires Authentication
  - Invalidates current token

### Teams
- **List/Create Teams**: `GET/POST /api/teams/`
  - Requires Authentication
  - GET: Returns user's teams ordered by creation date
  - POST: Creates new team with auto-created group chat

- **Team Details**: `GET /api/teams/<uuid:team_id>/`
  - Returns team details, tasks, and latest message

### Chats
- **List Chats**: `GET /api/chats/`
  - Returns chats ordered by last message time
  - Includes metadata for both individual and group chats

- **Chat Details**: `GET /api/chats/<uuid:chat_id>/`
  - Retrieves chat details and messages

### Tasks
- **List Tasks**: `GET /api/tasks/`
  - Returns user's tasks filtered by status
  - Includes both tasks and subtasks

- **Task Details**: `GET/PUT /api/tasks/<int:task_id>/`
  - GET: Retrieves task details
  - PUT: Updates task status

## Models

### User
- Custom user model with email authentication
- Fields: email, name, phone, dp, designation, ip_addr, port, isAdmin

### Team
- UUID primary key
- Auto-creates associated group chat
- Fields: name, description, icon, members (M2M with User)

### Task
- Assignable to user or team (exclusive)
- Status choices: 'to do', 'in progress', 'completed'
- Fields: title, description, deadline, status

### SubTask
- Only available for team tasks
- Inherits deadline from parent task if not specified
- Fields: title, description, assigned_user, status, deadline

### Chat
- Supports individual and group chats
- UUID primary key
- Fields: members (M2M with User), is_group_chat

### Message
- Timestamped chat messages. Real-time message delivery via WebSockets
- Fields: sender, chat, content, timestamp

## Desktop Client Features

- Login with token persistence
- Real-time chat interface with WebSocket integration
- Dashboard, Chat, and Task sections
- Filters in tasks and chats for better organization
- Modern UI with custom theme colors
- Collapsible navigation sidebar

## Dependencies

- Django
- Django REST Framework
- Channels (for WebSocket support)
- Daphne (ASGI server)
- Tkinter (for desktop client)
