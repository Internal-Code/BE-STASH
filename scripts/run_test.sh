#!/bin/bash

pytest --cov=src/tests/auth/ --cov-report=html --cov-report=term-missing src/tests/auth/
