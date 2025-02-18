# K-Collab

K-Collab is a collaborative platform with a Django REST backend and Tkinter desktop client that includes user management, team management, task management, and real-time chat functionality.

## Features

- User Authentication with JWT Tokens
- Team Management with Group Chat Integration
- Task & Subtask Management 
- Individual & Group Chat Functionality
- Desktop Client UI with Tkinter

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/k_collab.git
    ```

2. Create and activate virtual environment:
    ```bash
    python -m venv venv
    ```
    ```bash
    venv/Scripts/activate
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

6. Start the server:
    ```bash
    python manage.py runserver
    ```

7. Launch desktop client:
    ```bash
    python app.py
    ```

## API Endpoints

### Authentication
- **Login**: `POST /api/login/`
  - Request: `{"email": "user@example.com", "password": "password"}`
  - Response: `{"message": "Login successful", "authToken": "token", "user": {...}}`

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

- **Messages**: `GET/POST /api/chat/messages/`
  - GET: Retrieves chat messages with chat_id parameter
  - POST: Creates message with either chat_id or receiver_id

## Models

### User
- Custom user model with email authentication
- Fields: email, name, phone, dp, designation, ip_addr, port

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
- Supports both individual and group chats
- UUID primary key
- Fields: members (M2M with User), is_group_chat

### Message
- Timestamped chat messages
- Fields: sender, chat, content, timestamp

## Desktop Client Features

- Login with token persistence
- Collapsible navigation sidebar
- Real-time chat interface
- Dashboard, Chat, and Task sections
- Modern UI with custom theme colors

## License
