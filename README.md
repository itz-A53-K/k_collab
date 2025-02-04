# K-Collab

K-Collab is a collaborative platform that includes features such as user management, team management, task management, and chat functionality. This project is built using Django and Django REST framework.

## Features

- User Authentication
- Team Management
- Task Management
- Chat Functionality

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/k_collab.git
    cd k_collab
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    venv/Scripts/activate # On Mac/Linux use `source venv/bin/activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Apply the migrations:
    ```sh
    python manage.py migrate
    ```

5. Create a superuser:
    ```sh
    python manage.py createsuperuser
    ```

6. Run the development server:
    ```sh
    python manage.py runserver
    ```

## API Endpoints

### Authentication

- **Login**: `POST /api/login/`
    - Request Body: `{ "email": "user@example.com", "password": "password" }`
    - Response: `{ "message": "Login successful", "authToken": "token" }`

### Teams

- **List/Create Teams**: `GET/POST /api/teams/`
    - Requires Authentication
    - Response: List of teams or created team details

- **Team Content**: `GET /api/teams/<uuid:team_id>/`
    - Requires Authentication
    - Response: Team details, tasks, and last message

### Chats

- **List Chats**: `GET /api/chats/`
    - Requires Authentication
    - Response: List of chats

- **List/Create Messages**: `GET/POST /api/chat/messages/`
    - Requires Authentication
    - Request Body (POST): `{ "chat_id": "chat_uuid", "receiver_id": "receiver_uuid", "content": "message content" }`
    - Response: List of messages or created message details

## Models

### User

- [`email`](api/models.py): EmailField (unique)
- [`name`](api/models.py): CharField
- [`phone`](api/models.py): CharField (optional)
- [`dp`](api/models.py): ImageField (optional)
- [`designation`](api/models.py): CharField (optional)

### Team

- [`name`](api/models.py): CharField
- [`description`](api/models.py): CharField (optional)
- [`icon`](api/models.py): ImageField (optional)
- [`members`](api/models.py): ManyToManyField (User)
- [`chat`](api/models.py): OneToOneField (Chat)

### Task

- [`title`](api/models.py): CharField
- [`description`](api/models.py): TextField
- [`assigned_user`](api/models.py): ForeignKey (User, optional)
- [`assigned_team`](api/models.py): ForeignKey (Team, optional)
- [`status`](api/models.py): CharField (choices: 'to do', 'in progress', 'completed')
- [`deadline`](api/models.py): DateField

### Chat

- [`members`](api/models.py): ManyToManyField (User)
- [`is_group_chat`](api/models.py): BooleanField

### Message

- [`sender`](api/models.py): ForeignKey (User)
- [`chat`](api/models.py): ForeignKey (Chat)
- [`content`](api/models.py): TextField
- [`timestamp`](api/models.py): DateTimeField

## License

