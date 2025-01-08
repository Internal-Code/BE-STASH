from dotenv import load_dotenv


def pytest_configure(env: str):
    return load_dotenv(dotenv_path=env)
