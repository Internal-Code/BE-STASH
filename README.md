# README #
This is Proof of Concept (POC) for Finance Tracker Management. Established using FastAPI as a backend server for development stages.

##  What is tis repository for? ##
This repository is for a personal full-stack development project.

# Project Structure
```
├── docs\               # Contains design notes, architectural documentation, and additional project-related documents.
├── errors\             # Custom error classes and exception handlers
├── examples\           # Sample files or scripts showcasing how to use project features.
├── helpers\            # Miscellaneous helper functions
├── scripts\            # Shell script folder.
├── services\           # External service integrations
│    ├── postgre\       # PostgreSQL database integration (connections, migrations, queries)
│    ├── smtp\          # Email service (SMTP client, templates, and utilities)
│    ├── whatsapp\      # WhatsApp API integration (registration OTP, notifications, etc.)
├── src\                # Main application source code
│   ├── auth\           # Authentication & authorization logic
|   |   ├── routers\    # FastAPI routers for login, registration, OTP, token management
│   ├── common\         # Common utilities/endpoints shared across the app
|   |   ├── routers\    # Shared routes (health check, system status, etc.)
│   ├── schema\         # Pydantic/SQLModel schemas for request & response validation
│   ├── users\          # User domain (business logic & routers)
|   |   ├── routers\    # User-related API routes (profile, reset PIN, etc.)
│   ├── main.py         # FastAPI application entrypoint
│   ├── secret.py       # Environment secrets/config loader
├── templates\          # Jinja2 or HTML templates (if needed for emails, frontend rendering, etc.).
├── tests\              # Test suite
│   ├── unit\           # Unit tests (smallest scope: functions, services, models)
│   ├── api\            # API tests (FastAPI endpoints using TestClient/HTTPX)
│   ├── e2e\            # End-to-end tests (full workflow: auth → DB → external services)
├── utils\              # Cross-cutting utilities (logger, generator, network utils, etc.)
├── pyproject.toml      # Python project configuration and dependency management.
```
# Database Architecture
The database schema for this project is designed and maintained using **dbdiagram.io**.
You can explore the full diagram here:

[![View Database Architecture](https://img.shields.io/badge/DBDiagram-View%20Schema-blue?style=for-the-badge&logo=databricks)](https://dbdocs.io/armanantabastian/STASH-Database-Architecture)

This diagram provides a clear overview of the relationships between entities, including:
- **User authentication & authorization** tables (users, roles, tokens, OTPs, etc.)
- **Budgeting & transaction** tables (monthly budgets, categories, transactions, etc.)
- Supporting tables such as countries and login histories.

The schema is continuously updated as the project evolves to reflect new features and requirements.


# Project Setup Instructions
This project is developed with Python v3.12. To get started, you'll need to install Docker and Poetry.

## Prerequisites
- **Python v3.12**
- **Docker**
- **Poetry**
For Windows users, you'll also need to install either MinGW or Cygwin to run the shell scripts.

## Setup Steps
1. **Run the setup script**
    ```
    sh scripts/setup.sh
    ```

2. **Start docker containers**
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
- The run_test.sh script initiates end-to-end unit testing using pytest to verify that the endpoints function correctly according to the business processes.

# Repo Owner? #
* Bastian Armananta
* Andika Dwi Santoso
