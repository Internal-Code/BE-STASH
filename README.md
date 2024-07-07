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
This project is developed with python v3.10.12

* Create virtual environment (assuming you have installed anaconda)
```
conda create -n venv_name python==3.10.12
```

* Activate virtual environment
```
source bin/activate (Linux OS based)
```
or
```
conda activate venv_name (Windows OS based)
```

* Run backend server application
```
sh run_server.sh
```

* Access backend server via swagger
```
http://localhost:8000/api/v1/docs
```

### Repo Owner? ###
* Bastian Armananta