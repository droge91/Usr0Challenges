from dotenv import load_dotenv
import os
import discord
from pymongo import MongoClient
import boto3
import logging
class Connections():
    def __init__ (self, *args, **kwargs) -> None:
        try:
            load_dotenv()
            self.mongo = MongoClient(os.getenv("MONGODB_URI"))
            self.s3 = boto3.client('s3', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("AWS_SECRET_KEY"), region_name=os.getenv("AWS_REGION"))
            self.discord_key = os.getenv("DISCORD_KEY")
            self.users = self.mongo['Usr0Comp']['Users']
            self.challenges = self.mongo['Usr0Comp']['Challenges']
            logging.info('Connections initialized') 
        except Exception as e:
            logging.error(f'Error initializing connections: {e}')
            exit(1)

    # Function to upload a file to S3
    def uploadS3(self, file) -> None:
        s3 = self.s3
        bucket = 'challfiles'
        try:
            s3.upload_file(
                file,
                bucket, 
                file,
                ExtraArgs={
                    'ContentDisposition': 'attachment'
                }
            )
            logging.info(f'File {file} uploaded to S3 bucket {bucket}')
        except Exception as e:
            logging.error(f'Error uploading file {file} to S3: {e}')

    # Function to check if a file is in S3
    def checkS3(self, file):
        s3 = self.s3
        bucket = 'challfiles'
        try:
            s3.head_object(Bucket=bucket, Key=file)
            logging.info(f'File {file} exists in S3 bucket {bucket}')
            return True
        except Exception as e:
            logging.warning(f'File {file} does not exist in S3 bucket {bucket}: {e}')
            return False
