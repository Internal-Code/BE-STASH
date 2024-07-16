# README #
This is Proof of Concept (POC) for Finance Tracker Management. Established using FastAPI as a backend server for development stages.

###  What is tis repository for? ###
This repository built in using fastapi framework as a backend.

```
src\
├── auth\
│   ├── routers\            # Stored of list API during development.
│   │   ├── monthly_schema\ # Stored of list monthly_shcema router.
│   ├── schema\             # Stored of API responses schema serialized by pydantic.
│   ├── utils\              # Stored of list utilites based on project needs.
├── database\               # Stored of databases connection and table models.
│   ├── connection.py       # Stored of global database connection.
│   ├── models.py           # Stored for databases model mapped by SQLAlchemy.    
├── requirements\           # Dependencies project root directory.
│   ├── dev.txt             # Sample of development dependencies requirements.
├── tests\                  # Unit testing root directory.
│   ├── monthly_schema\     # Stored of list unit testing on montly_schema router.
main.py                     # Stored of main backend application.
secret.py                   # Stored of all secret on .env
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