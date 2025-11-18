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

def cart_create_response(status_code, body):
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
        user_id = event['pathParameters']['userId']
    except KeyError:
        return create_response(400, {'message': 'Missing userId di path'})

    try:
        data = json.loads(event['body'])
        product_id = data['productId']
        # Ubah quantity menjadi Decimal
        quantity = Decimal(str(data['quantity']))
    except (json.JSONDecodeError, KeyError, TypeError):
        return create_response(400, {'message': 'Body JSON tidak valid atau field (productId, quantity) hilang'})

    try:
        # 1. Ambil keranjang yang ada saat ini
        response = table.get_item(Key={'userId': user_id})
        cart = response.get('Item', {'userId': user_id, 'items': []})
        items_list = cart.get('items', [])
        
        # 2. Cari apakah produk sudah ada di keranjang
        item_found = False
        new_items_list = []
        
        for item in items_list:
            if item['productId'] == product_id:
                item_found = True
                if quantity > 0:
                    # Update quantity jika > 0
                    item['quantity'] = quantity
                    new_items_list.append(item)
                # Jika quantity == 0, kita tidak menambahkannya kembali
                # (ini sama dengan menghapusnya)
            else:
                new_items_list.append(item)

        # 3. Jika produk baru dan quantity > 0, tambahkan ke daftar
        if not item_found and quantity > 0:
            new_items_list.append({
                'productId': product_id,
                'quantity': quantity
            })

        # 4. Simpan kembali daftar items yang baru ke DynamoDB
        # Ini akan menimpa (overwrite) daftar 'items' yang lama
        response = table.update_item(
            Key={'userId': user_id},
            UpdateExpression="SET items = :i",
            ExpressionAttributeValues={
                ':i': new_items_list
            },
            ReturnValues="ALL_NEW" # Kembalikan item keranjang yang baru
        )

        return create_response(200, response.get('Attributes', {}))

    except Exception as e:
        print(e)
        return create_response(500, {'message': f"Error internal: {str(e)}"})