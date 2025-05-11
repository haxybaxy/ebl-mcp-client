import requests
import json

def send_whatsapp_message(to_number: str, message: str):
    url = "http://localhost:8000/send-whatsapp"
    
    # Make sure the number has the whatsapp: prefix
    if not to_number.startswith('whatsapp:'):
        to_number = f"whatsapp:{to_number}"
    
    payload = {
        "to_number": to_number,
        "message": message
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

if __name__ == "__main__":
    # Example usage
    to_number = "whatsapp:+34669923512" 
    message = "Hello! This is a test message from FastAPI and Twilio WhatsApp!"
    
    result = send_whatsapp_message(to_number, message)
    print(json.dumps(result, indent=2)) 