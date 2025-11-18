import boto3
import json
import os
import uuid
import datetime
from decimal import Decimal

# Inisialisasi DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Ambil nama tabel dari environment variable
ORDERS_TABLE = os.environ.get('ORDERS_TABLE')
table = dynamodb.Table(ORDERS_TABLE)

# --- Helper Functions ---

class DecimalEncoder(json.JSONEncoder):
    """ Helper untuk mengubah Decimal dari DynamoDB menjadi JSON """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def create_response(status_code, body):
    """ Helper untuk membuat respon API Gateway """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

# (Tambahkan kode Prasyarat dari atas di sini)

def handler(event, context):
    try:
        order_id = event['pathParameters']['orderId']
    except KeyError:
        return create_response(400, {'message': 'Missing orderId di path'})

    try:
        # Ambil status baru dari body
        data = json.loads(event['body'])
        new_status = data['status']
    except Exception:
        return create_response(400, {'message': 'Body JSON tidak valid atau field (status) hilang'})

    try:
        # Update hanya field 'status'
        response = table.update_item(
            Key={'orderId': order_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={
                '#s': 'status'  # 'status' bisa jadi reserved word
            },
            ExpressionAttributeValues={
                ':s': new_status
            },
            ReturnValues="ALL_NEW"  # Kembalikan item setelah di-update
        )
        
        return create_response(200, response.get('Attributes', {}))
        
    except Exception as e:
        print(e)
        return create_response(500, {'message': f"Error internal: {str(e)}"})