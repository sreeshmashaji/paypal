from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import requests
import base64
import uuid

# PayPal credentials
PAYPAL_CLIENT_ID = "AdpLSpsvdloH4ogtX34Rrwp3e6cnrpa5BSzgWWQXGyxc9Mw2QUMEh7bGGZjnX7DwHkr2cQ0gvfyhtpDw"
PAYPAL_CLIENT_SECRET = "EASEDDzaCQaydD6YtpilocL9Kl3sfiOS4NNBSCE65uqX_MXS8krvUdkyxpRQ7bT77ulgWMoK_ip1fCeL"

app = FastAPI()

paypal_request_id = str(uuid.uuid4())

def get_access_token():
    token_url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Authorization": f"Basic {base64.b64encode((PAYPAL_CLIENT_ID + ':' + PAYPAL_CLIENT_SECRET).encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to generate access token")

class PayPalOrderRequest(BaseModel):
    intent: str = "CAPTURE"
    reference_id: str = "default_ref_id"
    currency_code: str = "USD"
    value: str = "100.00"
    payment_method_preference: str = "IMMEDIATE_PAYMENT_REQUIRED"
    brand_name: str = "My Brand"
    locale: str = "en-US"
    landing_page: str = "BILLING"
    shipping_preference: str = "SET_PROVIDED_ADDRESS"
    user_action: str = "PAY_NOW"
    return_url: str = "http://localhost:8000/orders/success"
    cancel_url: str = "http://localhost:8000/orders/cancel"

@app.get("/orders/success")
async def success():
    return {"message": "Payment successful"}

@app.get("/orders/cancel")
async def cancel():
    return {"message": "Payment canceled"}

@app.post("/create-paypal-order/")
async def create_paypal_order(
    order_request: PayPalOrderRequest = Depends(),
    access_token: str = Depends(get_access_token)
):
    headers = {
        'Content-Type': 'application/json',
        'PayPal-Request-Id': paypal_request_id,
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        "intent": order_request.intent,
        "purchase_units": [
            {
                "reference_id": order_request.reference_id,
                "amount": {
                    "currency_code": order_request.currency_code,
                    "value": order_request.value,
                    "breakdown": {
                        "item_total": {
                            "currency_code": order_request.currency_code,
                            "value": "100.00"
                        }
                    }
                },
                "items": [
                    {
                        "name": "Sample Item",
                        "sku": "item123",
                        "unit_amount": {
                            "currency_code": order_request.currency_code,
                            "value": "50.00"
                        },
                        "quantity": 2,
                        "image_url": "https://example.com/image.jpg"
                    }
                ],
                "shipping": {
                    "address": {
                        "address_line_1": "1234 Elm Street",
                        "address_line_2": "Apt 567",
                        "admin_area_2": "San Francisco",
                        "admin_area_1": "CA",
                        "postal_code": "94107",
                        "country_code": "US"
                    }
                }
            }
        ],
        "application_context": {
            "brand_name": order_request.brand_name,
            "locale": order_request.locale,
            "landing_page": order_request.landing_page,
            "shipping_preference": order_request.shipping_preference,
            "user_action": order_request.user_action,
            "return_url": order_request.return_url,
            "cancel_url": order_request.cancel_url
        }
    }

    response = requests.post('https://api-m.sandbox.paypal.com/v2/checkout/orders', headers=headers, json=data)
    print(response.json())
    if response.status_code == 201:
        return {"message": "PayPal order created successfully", "order_id": response.json()["id"]}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to create PayPal order")

@app.get("/order/{order_id}")
async def get_order_details(order_id: str, access_token: str = Depends(get_access_token)):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch order details")

@app.post("/capture-paypal-order/{order_id}")
async def capture_paypal_order(order_id: str, access_token: str = Depends(get_access_token)):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.post(f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture', headers=headers)
    if response.status_code == 201:
        return {"message": "Payment captured successfully", "capture_id": response.json()["purchase_units"][0]["payments"]["captures"][0]["id"]}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to capture PayPal order")





