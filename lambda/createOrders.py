import boto3
import json
import os
import uuid
import datetime
from decimal import Decimal

# Inisialisasi DynamoDB resource
dynamodb = boto3.resource('dynamodb')
ORDERS_TABLE = os.environ.get('ORDERS_TABLE')
table = dynamodb.Table(ORDERS_TABLE)

# --- FUNGSI HELPER (PASTIKAN INI ADA) ---
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
            'Access-Control-Allow-Origin': '*'  # <-- INI BAGIAN PENTING UNTUK CORS
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

# --- FUNGSI HANDLER UTAMA ---
def lambda_handler(event, context):
    
    try:
        data = json.loads(event['body'])
        user_id = data['userId']
        items = data['items']
        
        # ---!! PASTIKAN ANDA MENGAMBIL DATA BARU INI !! ---
        nama_pelanggan = data.get('nama', 'N/A')
        alamat_pelanggan = data.get('alamat', 'N/A')
        metode_pembayaran = data.get('metodePembayaran', 'N/A')
        
    except Exception as e:
        # Jika JSON tidak valid, ini akan CRASH dan log ke CloudWatch
        print(f"JSON Body tidak valid: {e}")
        return create_response(400, {'message': f"Body JSON tidak valid: {str(e)}"})

    try:
        # Hitung total harga di backend
        total_price = sum(Decimal(str(item['price'])) * Decimal(str(item['quantity'])) for item in items)
        
        order_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().isoformat()
        
        order_item = {
            'orderId': order_id,
            'userId': user_id,
            'items': items,
            'totalPrice': total_price,
            'status': 'PENDING', # Status awal pesanan
            'createdAt': created_at,
            
            # ---!! PASTIKAN ANDA MENYIMPAN DATA BARU INI !! ---
            'customerName': nama_pelanggan,
            'shippingAddress': alamat_pelanggan,
            'paymentMethod': metode_pembayaran
        }
        
        # Simpan pesanan baru ke DynamoDB
        table.put_item(Item=order_item)
        
        # Kembalikan item LENGKAP (termasuk data baru)
        return create_response(201, order_item)
        
    except Exception as e:
        # Jika ada error lain (misal DDB gagal), ini akan CRASH
        print(f"Error saat menyimpan ke DDB: {e}")
        return create_response(500, {'message': f"Error internal server: {str(e)}"})