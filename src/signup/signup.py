import json
import secretmanager
import firebase_admin
from firebase_admin import credentials, auth, exceptions
import boto3
import os
import logging
from datetime import datetime, timedelta
import sendemail

logger = logging.getLogger()
logger.setLevel(logging.INFO)

tableName = os.environ['USERTABLE_TABLE_NAME'] 
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(tableName)
secretName = os.environ['Secret_Name']
senderEmail = os.environ['SENDER_EMAIL']
DIFF_JST_FROM_UTC = 9

#Firebase Admin SDK の初期化
def initialize_firebase(secretName):
    try:
        if not firebase_admin._apps:
            # Firebase 認証情報の取得
            firebase_creds =secretmanager.get_secret(secretName)
            #initialize firebase admin
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        raise

def add_user(user_id, email):
    try:
        response = table.put_item(
            Item={
                'id': user_id,
                'email': email,
                'createAt':(datetime.utcnow() + timedelta(hours=DIFF_JST_FROM_UTC)).isoformat()
            }
        )
    except Exception as e:
        logger.error(f'Error creating user {e}')

def register_user(email, password, secretName):

    try:
        initialize_firebase(secretName)
        #using function from firebase
        user = auth.create_user(email=email, password=password)
        logger.info(f'User created: {user}')

        verficationLink = auth.generate_email_verification_link(email, action_code_settings=None, app=None)
        logger.info(f'verification link: {verficationLink}')
        emailMessage = f'To complete your registartion, please click the link included:{verficationLink}'
        emailResponse = sendemail.sendEmail(senderEmail, email, "verify your email", emailMessage)
        logger.info(f'Email Response: {emailResponse}')

        return {
            "message": "Successfully created user",
            "user_id": user.uid,
            "verficationLink": verficationLink
        }
    except auth.EmailAlreadyExistsError:             # Firebase except error
        return {"error": "user already exists"}

    except exceptions.FirebaseError as fe:           # Firebase regular error  
        return {"error": str(fe)}

    except Exception as e:                           # Python regular error
        return {"error": str(e)}

def handler(event, context):
    print(event)
    body = json.loads(event['body'])
    email = body.get('email')
    password = body.get('password')

    # vaildate email and password
    if not email or not password:
        return {
            'statusCode': 404,
            'body': json.dumps({"message": "email and password are required"})
        }

    # register user
    response = register_user(email, password, secretName)
    logger.info(f'Response from create user call: {response}')

    # store user to table
    if 'user_id' in response:
        add_user(response['user_id'], email)
        return {
            'statusCode': 200,
            'body': json.dumps({"message": "User created successfully", "user_id": response["user_id"]})
        }
    else:
        # from firebase User already exists error
        if 'error' in response and 'already exists' in response['error'].lower():
            return {
                'statusCode': 409,
                'body': json.dumps({"message": "User already exists"})
            }
        # general error
        return {
            'statusCode': 500,
            'body': json.dumps({"message": response.get('error', 'Unknown error occured')})
        }
        