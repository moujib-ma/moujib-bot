from flask import Flask, request, jsonify
import requests
import os
import logging
from typing import Optional, Dict, Any

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- إعدادات واتساب ---
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "moujib_token_secret")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "ضع_كود_التوكن_الطويل_هنا")
889973017535202 = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "ضع_رقم_الهاتف_ايدي_هنا")
VERSION = "v19.0"  # أحدث نسخة

class WhatsAppBot:
    """فئة لإدارة منطق البوت والردود"""
    
    def __init__(self):
        self.responses = {
            'greeting': {
                'ar': "مرحباً بك في مُجيب! 👋\n\n🎯 *خدماتنا:*\n\n👕 1. كوليكسيون الرجال\n👗 2. كوليكسيون النساء\n💰 3. استعلام عن السعر\n📞 4. التوصيل والدفع\n\nاختر رقم أو اكتب سؤالك!",
                'fr': "Bienvenue chez Moujib! 👋\n\n🎯 *Nos services:*\n\n👕 1. Collection Homme\n👗 2. Collection Femme\n💰 3. Demande de prix\n📞 4. Livraison et Paiement\n\nChoisissez un numéro ou écrivez votre question!"
            },
            'men_collection': {
                'ar': "🔥 *كوليكسيون الرجال:*\n\n👖 A. سروال جينز - 200 درهم\n👕 B. تيشيرت قطني - 100 درهم\n🧥 C. جاكيت شتوي - 350 درهم\n👟 D. أحذية رياضية - 280 درهم\n\nلطلب منتج، اكتب الحرف + الكمية (مثال: A 2)",
                'fr': "🔥 *Collection Homme:*\n\n👖 A. Jean - 200 DH\n👕 B. T-shirt coton - 100 DH\n🧥 C. Veste d'hiver - 350 DH\n👟 D. Chaussures sport - 280 DH\n\nPour commander, écrivez la lettre + quantité (ex: A 2)"
            },
            'women_collection': {
                'ar': "💫 *كوليكسيون النساء:*\n\n👗 A. فستان صيفي - 250 درهم\n👚 B. بلوزة حرير - 180 درهم\n🩳 C. شورت - 120 درهم\n👠 D. كعب عالي - 220 درهم\n\nلطلب منتج، اكتب الحرف + الكمية",
                'fr': "💫 *Collection Femme:*\n\n👗 A. Robe d'été - 250 DH\n👚 B. Chemisier soie - 180 DH\n🩳 C. Short - 120 DH\n👠 D. Talons - 220 DH\n\nPour commander, écrivez la lettre + quantité"
            },
            'pricing': {
                'ar': "💰 *معلومات الأسعار:*\n\n• الأسعار تبدأ من 100 درهم\n• خصم 10% للطلبات فوق 500 درهم\n• التوصيل مجاني لطلبات فوق 300 درهم\n• الدفع نقداً عند الاستلام أو تحويل بنكي\n\nللاستفسار عن منتج معين، اكتب اسمه!",
                'fr': "💰 *Informations Prix:*\n\n• Prix à partir de 100 DH\n• Remise 10% pour commandes > 500 DH\n• Livraison gratuite > 300 DH\n• Paiement cash à la livraison ou virement\n\nPour un produit spécifique, écrivez son nom!"
            },
            'delivery': {
                'ar': "🚚 *معلومات التوصيل:*\n\n• التوصيل خلال 24-48 ساعة\n• مجاني للدار البيضاء والرباط\n• 20 درهم للمدن الأخرى\n• نعمل من الإثنين إلى السبت\n\nللتتبع أو الاستفسار، راسلنا!",
                'fr': "🚚 *Informations Livraison:*\n\n• Livraison 24-48h\n• Gratuite pour Casablanca et Rabat\n• 20 DH autres villes\n• Lundi à Samedi\n\nPour suivi ou questions, contactez-nous!"
            },
            'unknown': {
                'ar': "🤔 لم أفهم سؤالك!\n\nجرب أحد الخيارات:\n• اكتب '1' للملابس الرجالية\n• اكتب '2' للملابس النسائية\n• اكتب 'سعر' للاستفسار عن الأسعار\n• اكتب 'توصيل' لمعلومات التوصيل\n\nأو اكتب سؤالك بطريقة أخرى!",
                'fr': "🤔 Je n'ai pas compris!\n\nEssayez:\n• Tapez '1' pour Homme\n• Tapez '2' pour Femme\n• Tapez 'prix' pour les tarifs\n• Tapez 'livraison' pour infos livraison\n\nOu reformulez votre question!"
            }
        }
    
    def detect_language(self, text: str) -> str:
        """اكتشاف لغة النص"""
        arabic_chars = set('ابتثجحخدذرزسشصضطظعغفقكلمنهوي')
        if any(char in arabic_chars for char in text):
            return 'ar'
        return 'fr'
    
    def process_message(self, message: str) -> str:
        """معالجة الرسالة وإرجاع الرد المناسب"""
        message = message.lower().strip()
        lang = self.detect_language(message)
        
        # الترحيب
        if any(word in message for word in ['salam', 'slm', 'سلام', 'bonjour', 'hello', 'hi', 'مرحبا']):
            return self.responses['greeting'][lang]
        
        # القوائم
        elif any(word in message for word in ['1', 'رجال', 'homme', 'male']):
            return self.responses['men_collection'][lang]
        
        elif any(word in message for word in ['2', 'نساء', 'femme', 'women']):
            return self.responses['women_collection'][lang]
        
        # الأسعار
        elif any(word in message for word in ['3', 'بشحال', 'ثمن', 'سعر', 'prix', 'combien']):
            return self.responses['pricing'][lang]
        
        # التوصيل
        elif any(word in message for word in ['4', 'توصيل', 'livraison', 'delivery']):
            return self.responses['delivery'][lang]
        
        # الطلبات
        elif any(char in message for char in ['a', 'b', 'c', 'd']):
            return self.process_order(message, lang)
        
        # غير معروف
        else:
            return self.responses['unknown'][lang]
    
    def process_order(self, message: str, lang: str) -> str:
        """معالجة طلب المنتج"""
        products = {
            'a': {'ar': 'سروال جينز', 'fr': 'Jean', 'price': 200},
            'b': {'ar': 'تيشيرت قطني', 'fr': 'T-shirt', 'price': 100},
            'c': {'ar': 'جاكيت شتوي', 'fr': 'Veste', 'price': 350},
            'd': {'ar': 'أحذية رياضية', 'fr': 'Chaussures', 'price': 280}
        }
        
        try:
            parts = message.split()
            product_code = parts[0].lower()
            quantity = int(parts[1]) if len(parts) > 1 else 1
            
            if product_code in products:
                product = products[product_code]
                total = product['price'] * quantity
                
                if lang == 'ar':
                    return f"✅ تم تسجيل طلبك!\n\n📦 المنتج: {product['ar']}\n🔢 الكمية: {quantity}\n💰 الإجمالي: {total} درهم\n\nللتأكيد، ارسل:\n• اسمك الكامل\n• العنوان\n• رقم الهاتف"
                else:
                    return f"✅ Commande enregistrée!\n\n📦 Produit: {product['fr']}\n🔢 Quantité: {quantity}\n💰 Total: {total} DH\n\nPour confirmer, envoyez:\n• Nom complet\n• Adresse\n• Téléphone"
        
        except (ValueError, IndexError):
            pass
        
        # إذا كان هناك خطأ في الطلب
        if lang == 'ar':
            return "📝 لطلب منتج، اكتب:\nالحرف + الكمية\nمثال: A 2\n\nالحروف المتاحة: A, B, C, D"
        else:
            return "📝 Pour commander, écrivez:\nLettre + Quantité\nExemple: A 2\n\nLettres disponibles: A, B, C, D"

# تهيئة البوت
bot = WhatsAppBot()

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """المصافحة مع فيسبوك للتحقق من السيرفر"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("تم التحقق من الويب هوك بنجاح")
            return challenge, 200
        else:
            logger.warning("فشل التحقق من الويب هوك")
            return 'Forbidden', 403
    
    return 'Hello World', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """استقبال الرسائل من واتساب"""
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("لا توجد بيانات في الطلب")
            return 'OK', 200
        
        logger.info(f"بيانات مستلمة: {data}")
        
        # استخراج الرسالة
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message_data = value['messages'][0]
            
            # التحقق من أن الرسالة نصية
            if message_data.get('type') != 'text':
                logger.info("رسالة غير نصية - تم تجاهلها")
                return 'OK', 200
            
            phone_number = message_data['from']
            message_body = message_body = message_data['text']['body']
            
            logger.info(f"رسالة من {phone_number}: {message_body}")
            
            # معالجة الرسالة والحصول على الرد
            reply_text = bot.process_message(message_body)
            
            # إرسال الرد
            success = send_whatsapp_message(phone_number, reply_text)
            
            if success:
                logger.info(f"تم إرسال الرد إلى {phone_number}")
            else:
                logger.error(f"فشل إرسال الرد إلى {phone_number}")
                
    except Exception as e:
        logger.error(f"خطأ في معالجة الويب هوك: {str(e)}")
        logger.error(f"تفاصيل الخطأ: {data}")
    
    return 'OK', 200

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة السيرفر"""
    return jsonify({
        'status': 'healthy',
        'service': 'Moujib WhatsApp Bot',
        'version': '1.0'
    }), 200

def send_whatsapp_message(to: str, text: str) -> bool:
    """إرسال رسالة واتساب"""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {EAAfo3utE4ioBQAbXAqBDuNZBfXRUUhmaBRbM0jp2ZAnwNBZBwzZAWy2u5JBHe4nKoSjGEarEkKFDSxlZBOSw3gZBgjula2MUKgTzEPEmwHj2jJDSUNxFch4UcWFqurWh3LOUf6peNdkq15PzVvutLhrfE0YTkxuZBnGxgZASlZBRAB3m1QNAmyA64jVThGLV1kHcZAEByYYdfMXOHmJZCK7zllOdlSrZBhRhD6NsiZCZA1KeerGKSD5QonZAwBlO3BhSGXgpnZAW9Q3jlW2PNhhiALhFKd8hc1QagAZDZD}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"خطأ في إرسال الرسالة: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"خطأ في الاتصال: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}")
        return False

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # التحقق من المتغيرات البيئية
    required_vars = ['WHATSAPP_ACCESS_TOKEN', 'WHATSAPP_PHONE_NUMBER_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"متغيرات بيئية مفقودة: {missing_vars}")
        logger.warning("سيتم استخدام القيم الافتراضية")
    
    # تشغيل التطبيق
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"تشغيل سيرفر Moujib على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)