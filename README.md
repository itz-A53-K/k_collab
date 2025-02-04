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
    git clone https://github.com/yourusername/k-collab.git
    cd k-collab
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    venv/Scripts/activate ( On Windows )
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

## Models

### User

- : EmailField (unique)
- : CharField
- : CharField (optional)
- : ImageField (optional)
- : CharField (optional)

### Team

- : CharField
- : CharField (optional)
- : ImageField (optional)
- : ManyToManyField (User)
- : OneToOneField (Chat)

### Task

- : CharField
- : TextField
- : ForeignKey (User, optional)
- : ForeignKey (Team, optional)
- : CharField (choices: 'to do', 'in progress', 'completed')
- : DateField

### Chat

- : ManyToManyField (User)
- : BooleanField

### Message

- : ForeignKey (User)
- : ForeignKey (Chat)
- : TextField
- : DateTimeField
