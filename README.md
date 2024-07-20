# README #
This is Proof of Concept (POC) for Finance Tracker Management. Established using FastAPI as a backend server for development stages.

###  What is tis repository for? ###
This repository built in using fastapi framework as a backend.

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
### How do I get set up? ###
This project is developed with python v3.10.12, you need to install docker and poetry in order to utilize this project.

* Change configuration for installing venv inside the project.
```
poetry config virtualenvs.in-project true
```

* Create virtual environment and install all dependencies.
```
poetry install --no-root
```

* Run docker container
```
docker-compose up
```

* Run backend server application.
```
./run_server.sh
```

* Access backend server via swagger.
```
http://localhost:8000/api/v1/docs
```

### Repo Owner? ###
* Bastian Armananta