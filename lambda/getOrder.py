import boto3
import json
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr # Impor Attr untuk FilterExpression

# Inisialisasi DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Ambil nama tabel dari environment variable
ORDERS_TABLE = os.environ.get('ORDERS_TABLE')
table = dynamodb.Table(ORDERS_TABLE)

# --- Helper Functions (Sama seperti sebelumnya) ---

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

# --- Fungsi Handler Utama (YANG DIMODIFIKASI) ---

def get_handler(event, context):
    
    # Periksa apakah 'pathParameters' ada DAN 'orderId' ada di dalamnya
    if 'pathParameters' in event and event['pathParameters'] and 'orderId' in event['pathParameters']:
        # ----------------------------------------------------
        # JALUR 1: FUNGSI LAMA (Get By ID)
        # Ini adalah panggilan ke /orders/{orderId}
        # ----------------------------------------------------
        try:
            order_id = event['pathParameters']['orderId']
            response = table.get_item(
                Key={'orderId': order_id}
            )
            item = response.get('Item')
            
            if item:
                return create_response(200, item)
            else:
                return create_response(404, {'message': 'Pesanan tidak ditemukan'})
        
        except Exception as e:
            return create_response(500, {'message': f"Error internal: {str(e)}"})
            
    else:
        # ----------------------------------------------------
        # JALUR 2: FUNGSI BARU (Scan By Status)
        # Ini adalah panggilan ke /orders?status=...
        # ----------------------------------------------------
        
        # Ambil 'status' dari query string
        query_params = event.get('queryStringParameters')
        status_to_query = None
        
        if query_params and 'status' in query_params:
            status_to_query = query_params['status']
            
        try:
            if status_to_query:
                # ----- JIKA ADA STATUS, LAKUKAN SCAN DENGAN FILTER -----
                # PERINGATAN: Ini membaca SELURUH tabel lalu memfilter
                response = table.scan(
                    FilterExpression=Attr('status').eq(status_to_query)
                )
            else:
                # ----- JIKA TIDAK ADA STATUS, KEMBALIKAN SEMUA -----
                # PERINGATAN: Ini membaca SELURUH tabel
                response = table.scan()
            
            items = response.get('Items', [])
            return create_response(200, items)
            
        except Exception as e:
            print(f"ERROR: Gagal melakukan Scan: {e}")
            return create_response(500, {'message': f"Gagal mengambil data: {str(e)}"})