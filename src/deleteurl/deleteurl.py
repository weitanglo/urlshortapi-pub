import json
import os   
import boto3
from boto3.dynamodb.conditions import Attr

tableName = os.environ['URLSHORTNERTABLE_TABLE_NAME'] 
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(tableName)

def handler(event, context):
    print(event)
    try:
        email = event['requestContext']['authorizer']['jwt']['claims']['email']
        # delete/{id} define from api route
        recoedId = event['pathParameters']['id']
        # delete our matching id
        table.delete_item(
            Key = {
                'id': recoedId
            },
            ConditionExpression=Attr('createdBy').eq(email)
        )

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Successfully delete record'}),
            'headers': {'Content-Type': 'application/json'}
        }

    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return {
            'statusCode': 403,
            'body': json.dumps({'message': 'Not authorized to delete this url'}),
            'headers': {'Content-Type': 'application/json'}
        }            
    except KeyError:
        return{
            'statusCode': 400,
            'body': json.dumps({'message': 'failed delete record'}),
            'headers': {'Content-Type': 'application/json'}
        }