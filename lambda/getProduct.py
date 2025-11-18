import boto3
import json
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE')
table = dynamodb.Table(PRODUCTS_TABLE)

# --- Helper Functions (Salin dari yang lain) ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(body, cls=DecimalEncoder)
    }

# --- Handler Utama (YANG DIMODIFIKASI) ---
def handler(event, context):
    
    # JALUR 1: Mengambil SATU produk (panggilan ke /products/{productId})
    if 'pathParameters' in event and event['pathParameters'] and 'productId' in event['pathParameters']:
        try:
            product_id = event['pathParameters']['productId']
            response = table.get_item(Key={'productId': product_id})
            item = response.get('Item')
            
            if item:
                return create_response(200, item)
            else:
                return create_response(404, {'message': 'Produk tidak ditemukan'})
        except Exception as e:
            return create_response(500, {'message': f"Error internal: {str(e)}"})
            
    # JALUR 2: Mengambil SEMUA produk (panggilan ke /products)
    else:
        try:
            # PERINGATAN: Scan membaca seluruh tabel.
            # Untuk aplikasi besar, gunakan GSI atau query
            response = table.scan() 
            items = response.get('Items', [])
            return create_response(200, items)
        except Exception as e:
            return create_response(500, {'message': f"Gagal mengambil semua produk: {str(e)}"})