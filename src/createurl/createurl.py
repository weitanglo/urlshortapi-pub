import json
import os   #lambda supported
import boto3 #lambda supported
import uuid
import random
import string
from datetime import datetime, timedelta

#table name and dynamo
tableName = os.environ['URLSHORTNERTABLE_TABLE_NAME'] #os.environ.get('')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(tableName)
domainNameParam = os.environ['DOMAIN_NAME_PARAM']

# later one, input checks to make sure this string isnt already in database
def generate_short_code(url, length=6):
    char_pool = string.ascii_letters + string.digits
    return ''.join(random.sample(char_pool, length))
# how url and varNumbers be connected ? need redirect function

def handler(event, context):
    print(event) # for CW log debug
    body= json.loads(event["body"]) #change to json structure
    print(f'Body from event: {body}') # for CW log debug
    originalUrl = body.get('originalUrl') # so need to POST this one
    shortUrlResponse = generate_short_code(originalUrl)
    domainName = event['requestContext']['domainName'] # add because recongize url
    stage = event['requestContext']['stage']  

    email = event['requestContext']['authorizer']['jwt']['claims']['email'] # know user who created by 

    if domainNameParam not in domainName: 
        print('dev')
        shortUrl = f'https://{event["headers"]["host"]}/{stage}/{shortUrlResponse}' #starting use apiUrl for dev stage testing and change after
    else: #prod with custom domain
        print('custon domain')
        shortUrl = f'https://{event["headers"]["host"]}/{shortUrlResponse}'
    
    DIFF_JST_FROM_UTC = 9

    data = {
        'id': str(uuid.uuid4()),
        'originalUrl': originalUrl,
        'shortCode': shortUrlResponse,
        'createdAt': (datetime.utcnow() + timedelta(hours=DIFF_JST_FROM_UTC)).isoformat(),
        'clicks': 0,
        'createdBy': email,
        # 'shortUrl': shortUrl
    }

    try:
        table.put_item(Item=data)
        return {
            'statusCode': 201,
            'body': json.dumps({
                'shortUrl': shortUrl
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    except Exception as e:
        return {
            'statusCode': 403,
            'body': json.dumps({"message":"error saving data"})
        }
