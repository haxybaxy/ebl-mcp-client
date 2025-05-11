from fastapi import FastAPI, HTTPException, Request
from twilio.rest import Client
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="Twilio WhatsApp API")

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # Format: whatsapp:+14155238886

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class WhatsAppRequest(BaseModel):
    to_number: str  # Format: whatsapp:+1234567890
    message: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Twilio WhatsApp API"}

@app.post("/send-whatsapp")
async def send_whatsapp(whatsapp_request: WhatsAppRequest):
    try:
        # Ensure the 'to' number has the whatsapp: prefix
        to_number = whatsapp_request.to_number
        if not to_number.startswith('whatsapp:'):
            to_number = f"whatsapp:{to_number}"

        message = client.messages.create(
            body=whatsapp_request.message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_number
        )
        return {
            "status": "success",
            "message_sid": message.sid,
            "message": "WhatsApp message sent successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook(request: Request):
    """
    Webhook endpoint to receive incoming WhatsApp messages
    """
    form_data = await request.form()
    message_body = form_data.get('Body', '')
    from_number = form_data.get('From', '')
    
    # Here you can add your logic to handle incoming messages
    # For example, you could store them in a database or trigger other actions
    
    return {
        "status": "success",
        "received_message": message_body,
        "from": from_number
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
