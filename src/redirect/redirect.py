import json
import os
import boto3
from boto3.dynamodb.conditions import Key

tableName = os.environ['URLSHORTNERTABLE_TABLE_NAME'] 
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(tableName)

def handler(event, context):
    print(event)
    try:
        shortCode = event['pathParameters']['short_Code'] #from shortUrl(domain or api url/* ) path  
        response = table.query(
            IndexName = 'UniqueKeyIndex',
            KeyConditionExpression= Key('shortCode').eq(shortCode)  # from KeySchema
        )
        print(f'{response}') 
        # response may not only have  one item and also have some metadata, treat to array 
        items = response.get('Items', [])
        print(items)
        if items:
            item =items[0]
            # here we can get individual key
            originalUrl = item['originalUrl']
            primaryKey = {'id': item.get('id')}
            #increment the number of clicks, each time a url is visited
            table.update_item(
                Key= primaryKey,
                UpdateExpression= "ADD clicks :increment",
                ExpressionAttributeValues={
                    ':increment': 1
                }
            )
        return {
            'statusCode': 302, #redirect
            'headers': {
                'Location':  originalUrl
            },
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 404,
            'body': 'NO matching Url'
        }