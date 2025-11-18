import boto3
import json
import os
from decimal import Decimal

# Inisialisasi DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Ambil nama tabel dari environment variable
# Ini tabel BARU Anda untuk arsip, misal "CheckoutHistory"
HISTORY_TABLE = os.environ.get('HISTORY_TABLE')
table = dynamodb.Table(HISTORY_TABLE)

# --- Helper Functions ---

def create_response(status_code, body):
    """ Helper untuk membuat respon API Gateway """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body)
    }

# --- Fungsi Handler Utama ---

def handler(event, context):
    try:
        data = json.loads(event['body'])
        
        # Ambil semua data dari 'data' (yaitu 'newOrder' dari frontend)
        order_id = data['orderId']
        user_id = data['userId']
        items = data['items']
        total_price = Decimal(str(data['totalPrice']))
        created_at = data['createdAt']
        
        # ---!! AMBIL DATA BARU !! ---
        nama_pelanggan = data.get('customerName', 'N/A') # Nama field dari 'newOrder'
        alamat_pelanggan = data.get('shippingAddress', 'N/A')
        metode_pembayaran = data.get('paymentMethod', 'N/A')
        
    except Exception as e:
        return create_response(400, {'message': f"Body JSON tidak valid: {str(e)}"})

    try:
        archive_item = {
            'orderId': order_id,
            'userId': user_id,
            'items': items,
            'totalPrice': total_price,
            'createdAt': created_at,
            
            # ---!! SIMPAN DATA BARU KE TABEL ARSIP !! ---
            'customerName': nama_pelanggan,
            'shippingAddress': alamat_pelanggan,
            'paymentMethod': metode_pembayaran
        }
        
        table.put_item(Item=archive_item)
        
        return create_response(201, {'message': 'Checkout berhasil diarsipkan', 'archivedOrderId': order_id})
        
    except Exception as e:
        print(f"ERROR: Gagal menyimpan arsip ke DynamoDB: {e}")
        return create_response(500, {'message': f'Gagal mengarsipkan: {str(e)}'})