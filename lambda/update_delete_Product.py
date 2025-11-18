import boto3
import json
import os
import uuid
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE')
table = dynamodb.Table(PRODUCTS_TABLE)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def prod_handler(event, context):
    method = event.get('httpMethod')

    # --- Ambil productId ---
    try:
        product_id = event['pathParameters']['productId']
    except KeyError:
        return create_response(400, {'message': 'Missing productId di path'})

    if method == 'PUT':
        try:
            data = json.loads(event['body'])
        except json.JSONDecodeError:
            return create_response(400, {'message': 'Body JSON tidak valid'})

        try:
            response = table.update_item(
                Key={'productId': product_id},
                UpdateExpression="SET #nm = :n, description = :d, price = :p",
                ExpressionAttributeNames={'#nm': 'name'},
                ExpressionAttributeValues={
                    ':n': data.get('name'),
                    ':d': data.get('description', ''),
                    ':p': Decimal(str(data.get('price'))),
                    ':i': data.get('imageUrl', '')
                },
                ReturnValues="ALL_NEW"
            )
            return create_response(200, response.get('Attributes', {}))

        except Exception as e:
            print(e)
            return create_response(500, {'message': f"Error internal: {str(e)}"})

    if method == 'DELETE':
        try:
            table.delete_item(Key={'productId': product_id})
            return create_response(200, {'message': 'Produk berhasil dihapus'})
        except Exception as e:
            print(e)
            return create_response(500, {'message': f"Error internal: {str(e)}"})

    return create_response(405, {'message': f"Method {method} tidak didukung"})
