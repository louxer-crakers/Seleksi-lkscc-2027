import boto3
import json
import os
import uuid
from decimal import Decimal

# Inisialisasi DynamoDB resource menggunakan Boto3
# 'resource' adalah high-level API yang lebih mudah dipakai daripada 'client'
dynamodb = boto3.resource('dynamodb')

# Ambil nama tabel dari environment variable yang Anda set di Lambda
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE')
table = dynamodb.Table(PRODUCTS_TABLE)

# --- Helper Functions ---

class DecimalEncoder(json.JSONEncoder):
    """
    Helper class untuk mengubah tipe data Decimal dari DynamoDB
    menjadi float/int agar bisa di-serialize oleh json.dumps()
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Konversi ke int jika tidak ada koma, jika tidak, ke float
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def create_response(status_code, body):
    """
    Fungsi helper untuk membuat respon standar 
    yang dimengerti oleh API Gateway (Lambda Proxy Integration)
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # Aktifkan CORS untuk pengembangan
        },
        # Gunakan encoder khusus kita untuk menangani tipe Decimal
        'body': json.dumps(body, cls=DecimalEncoder)
    }

# (Tambahkan kode Prasyarat dari atas di sini)

def handler(event, context):
    try:
        # Ambil data produk dari body permintaan
        # event['body'] adalah string JSON
        data = json.loads(event['body'])
    except json.JSONDecodeError:
        return create_response(400, {'message': 'Body JSON tidak valid'})

    # Validasi input sederhana
    if 'name' not in data or 'price' not in data:
        return create_response(400, {'message': "Field 'name' dan 'price' wajib diisi"})

    # Buat ID unik menggunakan uuid
    product_id = str(uuid.uuid4())
    
    item = {
        'productId': product_id,
        'name': data['name'],
        'description': data.get('description', ''), # .get() aman jika 'description' tidak ada
        # Penting: DynamoDB butuh tipe data Decimal untuk angka
        # Konversi int/float dari JSON ke Decimal
        'price': Decimal(str(data['price'])),
        'imageUrl': data.get('imageUrl', '')
    }

    try:
        # Simpan item ke DynamoDB
        table.put_item(Item=item)
        # Kembalikan item yang baru dibuat
        return create_response(201, item)
    except Exception as e:
        print(e)
        return create_response(500, {'message': f"Error internal: {str(e)}"})