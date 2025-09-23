from this import d
import boto3
import os
from flask import current_app

class AWSLambda:
    def __init__(self):
        self.client = None
        self.name = None

    def init_app(self, app):
        self.app = app
        self.create_conn()
        # self.create_segp_conn()


    def create_conn(self):
        """
        Triggers the Lambda function slack_alerts for sending sqs and slack messages
        Args:
            sqs_message: dictionary. contains the sqs message
            slack_message: string. contains the slack message
        """
        self.client = boto3.client("lambda", self.app.config["AWS_REGION"])
        self.name = ""
        if self.app.config["ENVIRONMENT"] == "DEV" or self.app.config["ENVIRONMENT"] == "TEST":
            self.name = "dev_slack_alert"
            self.moderation_channel = "#test_moderation_notifs"
            self.nonperson_channel = "#test_nonperson_notifs"
            self.sqs_model_id = "dev-moderation"
            
        else:
            
            self.name = "live_bantay_slack_alert"
            self.moderation_channel = "#kumu-moderation-nude"
            self.nonperson_channel = "#kumu-moderation-nonperson"
            self.sqs_model_id = "live-moderation"
   


        