# README #
This is Proof of Concept (POC) for Finance Tracker Management. Established using FastAPI as a backend server for development stages.

##  What is tis repository for? ##
This repository is for a personal full-stack development project.

```
src\                            # Root folder.
├── auth\                       # Root of all endpoints folder.
│   ├── routers\                # Stored of list API during development.
│   │   ├── monthly_schemas\    # Stored of list monthly_shcema router.
│   ├   ├   ...                 # Another list of routers folders.
│   ├── schema\                 # Stored of API responses schema serialized by pydantic.
│   │   ├── response.py         # Pydantic response model.
│   ├── exception.py            # Handling custom error for more convenient debug.
│   ├── health_check.py         # Root endpoint.
│   ├── utils\                  # Stored of list utilites based on project needs.
│   │   ├── databases\          # Stored of spesific utilities related to databases.
│   ├   ├   ...                 # Another list of utilities folders.
│   ├── generator.py            # Stored of utilities for generating data.
│   ├ ...                       # Another of general utilities files.
├── database\                   # Stored of databases connection and table models.
│   ├── connection.py           # Stored of global database connection.
│   ├── models.py               # Stored for databases model mapped by SQLAlchemy.
├── tests\                      # Unit testing root directory.
│   ├── monthly_schema\         # Stored of list unit testing on montly_schema router.
│   ├ ...                       # Another of unit testing folders.
├──main.py                      # Stored of main backend application.
├──secret.py                    # Stored of all secret on .env
pyproject.toml                  # Stored of all library based on project requirement.
run_server.sh                   # Shell script for starting fastapi server.
```
# Project Setup Instructions

This project is developed with Python v3.10.12. To get started, you'll need to install Docker and Poetry.

## Prerequisites

- **Python v3.10.12**
- **Docker**
- **Poetry**

For Windows users, you'll also need to install either MinGW or Cygwin to run the shell scripts.

## Setup Steps

1. **Run the Setup Script**
    ```
    sh scripts/setup.sh
    ```

2. **Start the Docker Containers**
    ```
    docker-compose up
    ```

3. **Start the server script**
    ```
    sh scripts/run_server.sh
    ```

4. **Access backend server via swagger**
    ```
    http://localhost:8000/api/v1/docs
    ```

## Notes
- Ensure that docker-compose are running on your system.
- The setup.sh script configures the virtual environment and installs all necessary dependencies.
- The run_server.sh script starts the uvicorn server in debug mode for development purposes.

# Repo Owner? #
* Bastian Armananta
