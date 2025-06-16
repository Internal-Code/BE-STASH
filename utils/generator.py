import random
import string
import os
import hashlib
from utils.logger import logging


class Generator:
    def _sha256_file(self, path: str) -> str:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _sha256_string(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def random_number(self, length: int = 1) -> str:
        if length < 1:
            raise ValueError("length parameter should be more than 0.")

        lower_bound = 10 ** (length - 1)
        upper_bound = 10**length - 1

        return str(random.randint(lower_bound, upper_bound))

    def random_word(self, length: int = 4) -> str:
        if length < 1:
            raise ValueError("length parameter should be more than 0.")

        alphabet = string.ascii_lowercase
        word = "".join(random.choice(alphabet) for _ in range(length))

        return word

    def model_wrapper(self):
        MODELS_PATH = "services/postgre/models"
        INIT_PATH = os.path.join(MODELS_PATH, "__init__.py")
        if not os.path.isfile(INIT_PATH):
            logging.info(f"Creating new {INIT_PATH} file.")
            with open(INIT_PATH, "w"):
                pass

        import_libs = []
        model_classes = []

        for model in os.listdir(MODELS_PATH):
            if model.endswith(".py") and model != "__init__.py":
                model_name = model.removesuffix(".py")
                class_name = model_name.title().replace("_", "")
                import_libs.append(
                    f"from {MODELS_PATH.replace('/', '.')}.{model_name} import {class_name}"
                )
                model_classes.append(class_name)

        content = "\n".join(import_libs) + f"\n\n__all__ = [{', '.join(model_classes)}]"

        hashed_init = self._sha256_file(INIT_PATH)
        hashed_content = self._sha256_string(content)

        if hashed_init == hashed_content:
            logging.info(f"Skip re-generate {INIT_PATH}. No changes detected.")
            return None

        with open(INIT_PATH, "w") as file:
            logging.info(
                f"Detected changes in {MODELS_PATH}. File {INIT_PATH} successfully re-generated."
            )
            file.write(content)
