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
    venv/Scripts/activate #( On Windows )
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

- email : EmailField (unique)
- name : CharField
- phone : CharField (optional)
- dp : ImageField (optional)
- designation : CharField (optional)

### Team

- name : CharField
- description : CharField (optional)
- icon : ImageField (optional)
- members : ManyToManyField (User)
- chat : OneToOneField (Chat)

### Task

- title : CharField
- description : TextField
- assigned_user : ForeignKey (User, optional)
- assigned_team : ForeignKey (Team, optional)
- status : CharField (choices: 'to do', 'in progress', 'completed')
- deadline : DateField

### Chat

- members : ManyToManyField (User)
- is_group_chat : BooleanField

### Message

- sender : ForeignKey (User)
- chat : ForeignKey (Chat)
- content : TextField
- timestamp : DateTimeField
