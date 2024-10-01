import json
import secretmanager
import os
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secretName = os.environ['Secret_Name']
secretJson = secretmanager.get_secret(secretName)
apiKey = secretJson['apiKey']

# call firebase api to login 
def authenticate_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={apiKey}"
    header = {"Content-Type": "application/json"}
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, headers=header, json=data)
    return response.json()

def handler(event, context):
    print(event)
    body = json.loads(event['body'])
    email = body.get('email')
    password = body.get('password')
    
    if not email or not password:
        return {
            'statusCode': 404,
            'body': json.dumps({"message": "email and password are required"})
        }
    
    try:
        auth_response = authenticate_user(email, password)
        logger.info(f'Auth Response: {auth_response}')
        if 'idToken' in auth_response and 'refreshToken' in auth_response:
            return {
            'statusCode': 200,
            'body': json.dumps({"idTiken": auth_response['idToken'], "refreshToken": auth_response["refreshToken"], "expiresIn": auth_response["expiresIn"]})
            }
        else:
            return {
            'statusCode': 401,
            'body': json.dumps({"message": "Authentication failed"})               
            }
    except Exception as e:
        logger.error(f'Error during authentication: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({"message": "Unknown error occured"})               
        }