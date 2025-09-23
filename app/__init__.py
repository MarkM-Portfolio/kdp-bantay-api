"""
This contains the application factory for creating flask application instances.
Using the application factory allows for the creation of flask applications configured
for different environments based on the value of the CONFIG_TYPE environment variable
"""

from os import environ
from flask import Flask
from dotenv import load_dotenv
from app.extensions import awslambda

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration



load_dotenv()


def create_app(env=None):

    # Sentry
    SENTRY_DSN = environ.get("SENTRY_DSN")
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        environment="production",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        max_breadcrumbs=50,
        debug=True,
    )

    app = Flask(__name__)

    # Configure app instance
    if env is None:
        env = environ.get("ENV")

    if env == "TEST":
        app.config.from_object("config.TestingConfig")
        print("Using Test Environment")
    elif env == "PROD":
        app.config.from_object("config.ProductionConfig")
        print("Using Production Environment")
    else:
        app.config.from_object("config.DevelopmentConfig")
        print("Using Development Environment")

    # Initialize extensions
    awslambda.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Health check
    @app.route("/bantay/health")
    def bantay():
        return (
            "Welcome! You have successfully connected to Bantay Moderation Platform!"
        )

    return app


def register_blueprints(app):
    from app.bantay import bantay_api

    app.register_blueprint(bantay_api, url_prefix="/v1/bantay")
