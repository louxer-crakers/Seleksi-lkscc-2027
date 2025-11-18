import boto3
import json
import os
from decimal import Decimal

# Inisialisasi DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Ambil nama tabel dari environment variable
CART_TABLE = os.environ.get('CART_TABLE')
table = dynamodb.Table(CART_TABLE)

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
        # Ambil userId dari path URL
        user_id = event['pathParameters']['userId']
    except KeyError:
        return create_response(400, {'message': 'Missing userId di path'})

    try:
        response = table.get_item(
            Key={'userId': user_id}
        )
        
        item = response.get('Item')
        
        if item:
            # Ditemukan, kembalikan data keranjang
            return create_response(200, item)
        else:
            # Keranjang pengguna ini belum ada, kembalikan keranjang kosong
            return create_response(200, {'userId': user_id, 'items': []})
            
    except Exception as e:
        print(e)
        return create_response(500, {'message': f"Error internal: {str(e)}"})