from flask import Flask, request, jsonify
import requests
import os
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Temporary fix - use environment variables only
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "test_token_123")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")  # MUST be set in environment
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")  # MUST be set in environment
SELLER_PHONE_NUMBER = "212770890339"
VERSION = "v19.0"

class WhatsAppBot:
    def __init__(self):
        self.responses = {
            'greeting': {
                'ar': "أهلاً وسهلاً! 👋\n\n1. منتجات الرجال\n2. منتجات النساء\n3. الأسعار\n4. التوصيل",
                'fr': "Bienvenue! 👋\n\n1. Homme\n2. Femme\n3. Prix\n4. Livraison"
            }
        }
        self.user_sessions = {}
    
    def detect_language(self, text: str) -> str:
        arabic_pattern = re.compile('[\u0600-\u06FF]')
        return 'ar' if arabic_pattern.search(text) else 'fr'
    
    def process_message(self, message: str, sender_phone: str) -> str:
        message_lower = message.lower().strip()
        lang = self.detect_language(message)
        
        logger.info(f"Processing: {message} from {sender_phone}")
        
        # Simple response logic
        if any(word in message_lower for word in ['سلام', 'salam', 'bonjour', 'hello']):
            return self.responses['greeting'][lang]
        elif message_lower in ['1', '2', '3', '4']:
            return f"✅ تم اختيار {message} - سيتم الرد قريباً"
        else:
            return "اكتب 'سلام' للبدء أو اختر رقم من 1 إلى 4"
        
# Initialize bot
bot = WhatsAppBot()

def send_whatsapp_message(to: str, text: str) -> bool:
    """Send WhatsApp message with error handling"""
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        logger.error("❌ Missing ACCESS_TOKEN or PHONE_NUMBER_ID")
        return False
        
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        
        logger.info(f"🔄 Sending to {to}")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Message sent successfully")
            return True
        else:
            logger.error(f"❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Send error: {str(e)}")
        return False

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified")
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.info("📩 Webhook received")
        
        if not data:
            return 'OK', 200
            
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message_data = value['messages'][0]
            
            if message_data.get('type') != 'text':
                return 'OK', 200
                
            phone_number = message_data['from']
            message_body = message_data['text']['body']
            
            logger.info(f"📨 Message from {phone_number}: {message_body}")
            
            reply_text = bot.process_message(message_body, phone_number)
            success = send_whatsapp_message(phone_number, reply_text)
            
            if not success:
                logger.error("Failed to send reply")
                
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
    
    return 'OK', 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
        'whatsapp_api': 'checking...',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/test-token', methods=['GET'])
def test_token():
    """Test if the access token is valid"""
    if not ACCESS_TOKEN:
        return jsonify({'error': 'No ACCESS_TOKEN set'}), 400
        
    try:
        url = f"https://graph.facebook.com/{VERSION}/me"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        response = requests.get(url, headers=headers, timeout=10)
        
        return jsonify({
            'token_valid': response.status_code == 200,
            'status_code': response.status_code,
            'response': response.json() if response.status_code == 200 else response.text
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    # Check required environment variables
    if not ACCESS_TOKEN:
        logger.warning("⚠️ ACCESS_TOKEN not set - bot will not send messages")
    if not PHONE_NUMBER_ID:
        logger.warning("⚠️ PHONE_NUMBER_ID not set - bot will not send messages")
    
    logger.info(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)