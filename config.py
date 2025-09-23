from os import environ
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base config"""



    # TODO: Separate based on environment
    AWS_ACCESS_KEY_ID = environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = environ.get("AWS_REGION")
    UNLEASH_ADMIN_SECRET = environ.get("UNLEASH_ADMIN_SECRET")
    UNLEASH_ADDRESS = "http://13.213.136.86:4242"
    UNLEASH_APP_NAME = "kumu-dataplatform-dev"


class DevelopmentConfig(Config):
    ENVIRONMENT = "DEV"

    EXP_MONGO_CLUSTER = "dev-exp-dedicated.q0znb.mongodb.net"



class TestingConfig(Config):
    ENVIRONMENT = "TEST"

    EXP_DB = "test_experimentation_platform"
    SEGP_DB = "test_segmentation_platform"

    EXP_MONGO_CLUSTER = "dev-exp-cluster.q0znb.mongodb.net"
   


class ProductionConfig(Config):
    ENVIRONMENT = "PROD"

    EXP_MONGO_CLUSTER = "live-exp.q0znb.mongodb.net"

