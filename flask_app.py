

#! /var/www/html/kdp-malacanang-api/venv/bin/python3.6
from app import create_app


application = create_app()

if __name__ == "__main__":
    application.run()