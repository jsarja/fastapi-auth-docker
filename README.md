# fastapi-auth-docker

## Table of Contents
- [Project Overview](#project-overview)
- [Usage](#usage)
- [Implementation details](#implementation-details)
- [Run Project Locally](#run-project-locally)
- [TODO Items](#todo-items)

## Project Overview

This project demonstrates the deployment of some key web API components using FastAPI, incorporating JWT for secure authentication, Docker for containerization, and MongoDB for robust data persistence.

- **FastAPI Framework:** At the heart of our application lies FastAPI, a high-performance web framework for building APIs with Python 3.7+ based on standard Python type hints. The framework facilitates the creation of quickly scalable endpoints, with a special emphasis on speed and ease of use.

- **JWT Based Authentication System:** Authentication is a fundamental aspect of many modern web applications. This project demonstrates a basic JWT (JSON Web Tokens) authentication and authorization flow. The implementation supports both traditional username-password authentication methods and modern OAuth2 with Google, providing a flexible and secure way to handle user authentication.

- **Docker Integration:** To ensure that our application is easy to deploy and run on any system, we utilize Docker and Docker Compose. This allows for the FastAPI application and MongoDB to be containerized, simplifying dependencies management and ensuring that the environment is consistent across different machines. Users can effortlessly spin up the entire stack with just a few commands, making local development and testing a breeze.

- **Persistence with MongoDB:** The data persistence with MongoDB and FastAPI authorization are demonstrated with an exemplary note-management endpoints.

## Usage

This section outlines how to interact with the project's API, demonstrating the fundamental user journey, from registration to manipulating notes, all secured by authentication. The `test_end_to_end` function within `tests/test_notes.py` provides a practical overview of these operations.

1. **Authentication Requirement for Note Operations:** To ensure data privacy, accessing note endpoints necessitates user authentication. Attempting to interact with these endpoints without valid credentials results in a `401 UNAUTHORIZED` response:

```python
# Try to create a new note without authentication
response = client.post(
    "/note",
    json=NOTE_JSON,
)
assert response.status_code == 401
```

2. **User Registration:** Users can create an account using an email and password combination. Simplifying the flow for demonstration purposes, this project omits additional steps like email verification, allowing immediate use of the new account:

```python
# Register a new user with email and password
register_response = client.post(
    "/auth/register",
    data={"username": "test@email.com", "password": "password"},
)
assert register_response.status_code == 200
```

3. **User Sign-In:** Registered users can sign in using their email and password. This step is crucial for obtaining the JWT token required for subsequent requests:

```python
# Sign in with email and password
signin_response = client.post(
    "/auth/token",
    data={"username": "test@email.com", "password": "password"},
)
assert signin_response.status_code == 200
assert signin_response.json().get("access_token")
```

4. **Accessing Protected Endpoints:** After signing in, the received JWT token must be included in the `Authorization` header for requests to protected endpoints. This enables authenticated operations like creating a new note:

```python
# Create a new note with Authorization header
jwt_token = signin_response.json()["access_token"]
response = client.post(
    "/note",
    json=NOTE_JSON,
    headers={
        "Authorization": f"Bearer {jwt_token}",
    },
)
assert response.status_code == 200
```

5. **Fetching Notes:** Authenticated users can retrieve all their notes or specific ones by utilizing the appropriate endpoints. This functionality demonstrates the seamless integration of authentication with user-specific data access:

```python
# Get list of user notes.
response = client.get(
    "/note",
    headers={
        "Authorization": f"Bearer {jwt_token}",
    },
)
assert response.status_code == 200
response_data = response.json()
assert len(response_data) == 1
assert response_data[0]["title"] == "Title"
assert response_data[0]["content"] == "Note content"
```

```python
# Get note for id.
note_id = response_data[0]["id"]
response = client.get(
    f"/note/{note_id}",
    headers={
        "Authorization": f"Bearer {jwt_token}",
    },
)
assert response.status_code == 200
response_data = response.json()
assert response_data["title"] == "Title"
assert response_data["content"] == "Note content"
```

6. **Updating and Deleting Notes:** The API also supports modifying existing notes and removing them, showcasing the full spectrum of CRUD operations within a secure context:

```python
# Update note's title
response = client.put(
    f"/note/{note_id}",
    headers={
        "Authorization": f"Bearer {jwt_token}",
    },
    json=NOTE_JSON | {"title": "New title"},
)
assert response.status_code == 200

# Fetch note data to test the title change
response = client.get(
    f"/note/{note_id}",
    headers={
        "Authorization": f"Bearer {jwt_token}",
    },
)
response_data = response.json()
assert response_data["title"] == "New title"
assert response_data["content"] == "Note content"
```

```python
# Delete notes
response = client.delete(
    f"/note/{note_id}",
    headers={
        "Authorization": f"Bearer {jwt_token}",
    },
)
assert response.status_code == 200

# Fetch all notes to test that the note was deleted
response = client.get(
    "/note",
    headers={
        "Authorization": f"Bearer {jwt_token}",
    },
)
assert response.status_code == 200
response_data = response.json()
assert len(response_data) == 0
```

## Implementation Details

### Database Abstraction Layer

The project employs a database abstraction layers to ensure versatility and scalability across different database systems. At the core of this architecture is abstract base classes which define standard interfaces for database operations. This design allows for seamless integration of various database implementations, enhancing the project's adaptability to different storage solutions. Here's a glimpse into the `UserDBClient` class:

```python

class UserDBClient(ABC):
    @abstractmethod
    def get_user(self, user_id: UUID4) -> UserModel | None:
        pass

    @abstractmethod
    def get_google_user(self, google_user_id: str) -> UserModel | None:
        pass

    @abstractmethod
    def get_user_for_email(self, email: str) -> UserModel | None:
        pass

    @abstractmethod
    def save_user(self, user: UserModel):
        pass
```

The `get_user_db_client` function in `app.dependencies.py` determines which concrete implementation of `UserDBClient` is used at runtime. This method simplifies switching between database clients, promoting easy testing and scalability:

```python
def get_user_db_client() -> UserDBClient:
    return UserMongoDBClient()
```

FastAPI endpoints requiring database interactions can seamlessly integrate the database client through dependency injection in the function arguments, ensuring loose coupling:

```python
@router.get("/")
async def endpoint(user_db_client: Annotated[UserDBClient, Depends(get_user_db_client)])
```

This architecture also eases the process of unit testing by allowing the substitution of the database client with a mock implementation. This capability ensures that tests can run independently of the actual database, providing reliable and consistent results:

```python
from app.dependencies import get_user_db_client
from app.main import app
from tests.db_client_mock import UserTestDBClient

def test_register():
    test_db = UserTestDBClient()
    app.dependency_overrides[get_user_db_client] = lambda: test_db
    ...
```

### JWT access token
JWT (JSON Web Tokens) serve as a compact and self-contained method for securely transmitting information between parties as a JSON object. This information can be verified and trusted because it is digitally signed. JWT access tokens are particularly useful in authentication and authorization processes, where they enable servers to recognize and validate the identity of users without needing to repeatedly query the database.

The creation of an access token in the project is facilitated by the `create_access_token` function, which resides in `app.internal.user_management.py`. This function utilizes the TokenPayload model to encapsulate the data that we want to encode to the JWT token. In this case the payload includes the subject of the token (=user ID) and the token's expiry timestamp. The jose library is then employed to encode these details into the JWT, using a secret key and a specified algorithm. Here is how the access token is generated:

```python
def create_access_token(user_id: UUID4):
    token_data = TokenPayload(
        sub=user_id.hex,
        expires=datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    encoded_jwt = jwt.encode(
        token_data.model_dump(mode="json"),
        settings.AUTH_SECRET,
        algorithm=DECODE_ALGORITHM,
    )
    return encoded_jwt
```

### Authentication methods
The project provides two distinct methods for user authentication: traditional email/password and Google OAuth2 sign-in.

#### Email and Password Authentication:
During the sign-up process, users provide their email and a password, which is securely hashed and stored in the database. To authenticate, the application retrieves the user by email and compares the provided password with the hashed password stored in the database:

```python
def authenticate_password_user(email: str, password: str, db_client: UserDBClient):
    user = db_client.get_user_for_email(email=email)

    if not user:
        raise CREDENTIALS_EXCEPTION

    if not pwd_context.verify(password, user.password):
        raise CREDENTIALS_EXCEPTION

    return user
```

#### Google OAuth2 Authentication:
To enable Google OAuth2 authentication in your application, start by creating a `.env` file in the project's root directory and [obtaining the Google OAuth client ID from the Google Cloud Console](https://developers.google.com/identity/protocols/oauth2#1.-obtain-oauth-2.0-credentials-from-the-dynamic_data.setvar.console_name-.). Add the client ID to your `.env` file as `GOOGLE_OAUTH_CLIENT_ID`. If the the client id environment variable is not defined, the application defaults to supporting only email/password authentication.


For users signing in with their Google accounts, our application accepts an OAuth2 token from the client. This token is then validated with Google's servers. Upon successful validation, Google returns a payload including the user's ID and email. The application then searches the database for a user linked to the provided Google ID. If found, the user is authenticated:

```python
def verify_google_oauth2_token(oauth2_token: Annotated[str, Form()]):
    try:
        return id_token.verify_oauth2_token(
            oauth2_token, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
        )
    except ValueError:
        raise CREDENTIALS_EXCEPTION

def authenticate_google_user(google_user_id: str, db_client: UserDBClient):
    if user := db_client.get_google_user(google_user_id):
        return user

    raise CREDENTIALS_EXCEPTION

@router.post("/token/google")
async def sign_in_google(
    oauth2_token: Annotated[str, Form()],
    user_db_client: Annotated[UserDBClient, Depends(get_user_db_client)],
) -> Token:
    idinfo = verify_google_oauth2_token(oauth2_token)
    user = authenticate_google_user(
        google_user_id=idinfo["sub"],
        db_client=user_db_client,
    )

    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token, token_type="bearer")
```

## Run Project Locally
This guide will walk you through setting up and running the project on your local machine using Docker, running tests, and managing Python package dependencies efficiently.

### Run in docer-compose
Running the application with docker-compose requires docker and docker-compose to be installed on your machine. You can get them by e.g. by installing [Docker Desktop](https://www.docker.com/products/docker-desktop/).

#### Build the Docker Image
To create a Docker image for the project, execute the following command in the terminal:

```shell
docker build -t fastapi-auth-docker .
```
This command builds a Docker image named `fastapi-auth-docker` based on the instructions in your Dockerfile.

#### Starting the Application with Docker Compose
Once the image is built, you can start the application with Docker Compose:
```shell
docker-compose up
```
This command reads the `docker-compose.yml` file and starts all the services defined within it, including your FastAPI application and any databases or other dependencies configured.

### Running Tests in Docker
You can run the tests with docker-compose:
```shell
docker-compose run fastapi-auth-docker python -m pytest
```

### Adding New PyPI Packages
Managing Python dependencies is crucial for the reproducibility and consistency of your application. Here's how to add new packages and ensure they're included in your Docker environment.

#### Initialize Local Environment
Before adding new packages, set up a local virtual environment and install existing dependencies:
```shell
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

#### Install a New Package and Rebuild the Docker Image
Make sure virtual environment is active:
```shell
source env/bin/activate
```

After activating your virtual environment, install the new package:

```shell
pip install package-name
```

Update your requirements.txt file to reflect the new dependency:
```shell
pip freeze > requirements.txt
```

Finally, rebuild your Docker image to include the new package:
```shell
docker build -t fastapi-auth-docker .
```

### CI/CD
#### pre-commit
Project uses pre-commit to check code styling when creating commits. Initilize pre-commit with command:
```shell
pre-commit install
```
Runs:
- **Formatting:** black
- **Sorting imports:** isort
- **Linting:** flake8

The pre-commit runs on changed files on commits. You can also manually check all the files:
```shell
pre-commit run --all-files
```
More info: [https://pre-commit.com/](https://pre-commit.com/)

#### Github actions
When creating a Pull Request in GitHub, automatic GitHub actions are run on:
- Unit tests
- Code formatting

## TODO Items
- **Lifecycle of Email-Password Registration:**
    - Implementing an email verification flow to confirm user email addresses.
    - Adding features for users to update their passwords securely.
    - Providing a mechanism for users to delete their accounts.

- **Refresh Token Implementation:**
    - Developing a system for refresh tokens to allow users to remain signed in securely and manage session validity more effectively.
