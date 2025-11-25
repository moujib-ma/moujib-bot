from flask import Flask, request, jsonify
import requests
import os
import logging
import re
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- إعدادات واتساب ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "moujib_token_secret")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "EAAfo3utE4ioBQJ72Y5gkM29CnuSvLVlh3WZBvfKVt5rLLpt8TS15QTW36mLUSZC5Gzg2ZCu7sMDnBHMr5FuDwHuYr9WfASsZAlYIpG06F7pj4tV6e6XdknSMHI6D0YcyuoZB6ptQ4j1prkahIirpDTDPV3ecDWMb3zrwxBeiRgfGiQrfxT2A1CZAZCNZBSZCcAXuk7AZDZD")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "889973017535202")
SELLER_PHONE_NUMBER = "212770890339"
VERSION = "v19.0"

class WhatsAppBot:
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
            'help': {
                'ar': "🆘 *كيف يمكنني مساعدتك؟*\n\n📋 1 - عرض منتجات الرجال\n📋 2 - عرض منتجات النساء\n💰 3 - معلومات الأسعار\n🚚 4 - معلومات التوصيل\n\nأو اكتب رسالتك مباشرة!",
                'fr': "🆘 *Comment puis-je vous aider?*\n\n📋 1 - Voir produits Homme\n📋 2 - Voir produits Femme\n💰 3 - Informations prix\n🚚 4 - Informations livraison\n\nOu écrivez votre message directement!"
            },
            'contact_info_received': {
                'ar': "✅ تم استلام معلوماتك بنجاح!\n\n📞 سيتصل بك فريقنا خلال 30 دقيقة للتأكيد النهائي للطلب.\n\nشكراً لثقتك بنا! 🤝",
                'fr': "✅ Informations reçues avec succès!\n\n📞 Notre équipe vous contactera dans 30 minutes pour confirmation finale.\n\nMerci de votre confiance! 🤝"
            },
            'unknown': {
                'ar': "🤔 لم أفهم سؤالك!\n\nاكتب 'مساعدة' للحصول على قائمة الخيارات المتاحة\nأو اكتب سؤالك بطريقة أخرى!",
                'fr': "🤔 Je n'ai pas compris!\n\nTapez 'aide' pour voir les options disponibles\nOu reformulez votre question!"
            }
        }
        
        self.products = {
            'a': {'ar': 'سروال جينز', 'fr': 'Jean', 'price': 200},
            'b': {'ar': 'تيشيرت قطني', 'fr': 'T-shirt', 'price': 100},
            'c': {'ar': 'جاكيت شتوي', 'fr': 'Veste', 'price': 350},
            'd': {'ar': 'أحذية رياضية', 'fr': 'Chaussures', 'price': 280},
            'e': {'ar': 'فستان صيفي', 'fr': 'Robe été', 'price': 250},
            'f': {'ar': 'بلوزة حرير', 'fr': 'Chemisier soie', 'price': 180},
            'g': {'ar': 'شورت', 'fr': 'Short', 'price': 120},
            'h': {'ar': 'كعب عالي', 'fr': 'Talons', 'price': 220}
        }
        
        # لتتبع حالة المستخدمين
        self.user_sessions = {}
    
    def detect_language(self, text: str) -> str:
        """اكتشاف لغة النص"""
        arabic_pattern = re.compile('[\u0600-\u06FF]')
        if arabic_pattern.search(text):
            return 'ar'
        return 'fr'
    
    def process_message(self, message: str, sender_phone: str) -> str:
        """معالجة الرسالة وإرجاع الرد المناسب"""
        message = message.lower().strip()
        lang = self.detect_language(message)
        
        logger.info(f"معالجة رسالة من {sender_phone}: '{message}'")
        
        # إذا كان المستخدم لديه جلسة نشطة، اعتبر أي رسالة معلومات اتصال
        if sender_phone in self.user_sessions:
            logger.info(f"المستخدم {sender_phone} لديه جلسة نشطة - معالجة كمعلومات اتصال")
            return self.process_contact_info(message, lang, sender_phone)
        
        # الترحيب والمساعدة
        if any(word in message for word in ['salam', 'slm', 'سلام', 'bonjour', 'hello', 'hi', 'مرحبا', 'مساء', 'صباح']):
            return self.responses['greeting'][lang]
        
        elif any(word in message for word in ['مساعدة', 'aide', 'help', 'خيارات']):
            return self.responses['help'][lang]
        
        # القوائم
        elif any(word in message for word in ['1', 'رجال', 'homme', 'male', 'ذكور']):
            return self.responses['men_collection'][lang]
        
        elif any(word in message for word in ['2', 'نساء', 'femme', 'women', 'إناث']):
            return self.responses['women_collection'][lang]
        
        # الأسعار
        elif any(word in message for word in ['3', 'بشحال', 'ثمن', 'سعر', 'prix', 'combien', 'تكلفة']):
            return self.responses['pricing'][lang]
        
        # التوصيل
        elif any(word in message for word in ['4', 'توصيل', 'livraison', 'delivery', 'شحون', 'وصل']):
            return self.responses['delivery'][lang]
        
        # الطلبات
        elif any(char in message for char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']):
            return self.process_order(message, lang, sender_phone)
        
        # شكر
        elif any(word in message for word in ['شكر', 'merci', 'thanks', 'thank']):
            if lang == 'ar':
                return "العفو! 😊\nهل يمكنني مساعدتك بأي شيء آخر؟"
            else:
                return "De rien! 😊\nPuis-je vous aider avec autre chose?"
        
        # غير معروف
        else:
            return self.responses['unknown'][lang]
    
    def is_contact_info(self, message: str) -> bool:
        """التعرف على المعلومات الشخصية في الرسالة"""
        contact_keywords = [
            'اسم', 'عائلة', 'شارع', 'حي', 'مدينة', 'عنوان', 'هاتف', 'رقم', 
            'name', 'rue', 'avenue', 'ville', 'adresse', 'téléphone', 'phone',
            'الدار البيضاء', 'casablanca', 'الرباط', 'rabat', 'مراكش', 'marrakech',
            'فاس', 'fes', 'طنجة', 'tanger', 'مكناس', 'meknes', 'أكادير', 'agadir',
            '068', '06', '07', '05', '+212', '212'
        ]
        
        # إذا كانت الرسالة تحتوي على كلمات مفتاحية أو أرقام هاتف
        for keyword in contact_keywords:
            if keyword in message.lower():
                return True
        
        # إذا كانت الرسالة تحتوي على نمط رقم هاتف مغربي
        phone_pattern = re.compile(r'(\+212|0)([5-7]\d{8})')
        if phone_pattern.search(message):
            return True
        
        return False
    
    def process_order(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة طلب المنتج"""
        try:
            parts = message.split()
            product_code = None
            
            # البحث عن الحرف في الرسالة
            for char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
                if char in message.lower():
                    product_code = char
                    break
            
            if not product_code or product_code not in self.products:
                return self.responses['unknown'][lang]
            
            # استخراج الكمية
            quantity = 1
            numbers = re.findall(r'\d+', message)
            if numbers:
                quantity = int(numbers[0])
                quantity = min(quantity, 10)  # حد أقصى 10 قطع
            
            product = self.products[product_code]
            total = product['price'] * quantity
            
            # حفظ معلومات الطلب مؤقتاً - هذا مهم للإشعار!
            self.user_sessions[sender_phone] = {
                'product': product,
                'quantity': quantity,
                'total': total,
                'timestamp': datetime.now(),
                'waiting_for_contact': True  # علامة أننا ننتج معلومات الاتصال
            }
            
            logger.info(f"✅ تم حفظ طلب من {sender_phone}: {product['ar']} x {quantity} = {total} درهم")
            logger.info(f"🔄 الآن في انتظار معلومات الاتصال من {sender_phone}")
            
            if lang == 'ar':
                return f"""✅ تم تسجيل اختيارك!

📦 المنتج: {product['ar']}
🔢 الكمية: {quantity}
💰 الإجمالي: {total} درهم

⬇️ *لإكمال الطلب، أرسل لنا الآن:*
👤 الاسم الكامل
📍 العنوان المفصل (الشارع، الحي، المدينة)
📞 رقم الهاتف للتواصل

سنقوم بالاتصال بك للتأكيد النهائي! 📞"""
            else:
                return f"""✅ Choix enregistré!

📦 Produit: {product['fr']}
🔢 Quantité: {quantity}
💰 Total: {total} DH

⬇️ *Pour compléter la commande, envoyez-nous:*
👤 Nom complet
📍 Adresse détaillée (Rue, Quartier, Ville)
📞 Numéro de téléphone

Nous vous contacterons pour confirmation finale! 📞"""
        
        except Exception as e:
            logger.error(f"خطأ في معالجة الطلب: {str(e)}")
            return self.responses['unknown'][lang]
    
    def process_contact_info(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة معلومات الاتصال وإرسال إشعار للبائع"""
        try:
            # 1. الحصول على معلومات الطلب من الجلسة
            order_info = self.user_sessions.get(sender_phone, {})
            
            # 2. إنشاء رسالة الإشعار للبائع
            notify_text = f"""🚨 *طلبية جديدة!*

📞 العميل: {sender_phone}
📝 المعلومات المقدمة:
{message}

"""
            
            if order_info:
                product = order_info.get('product', {})
                quantity = order_info.get('quantity', 1)
                total = order_info.get('total', 0)
                
                notify_text += f"""🛒 *تفاصيل الطلب:*
📦 المنتج: {product.get('ar', 'غير محدد')} / {product.get('fr', 'N/A')}
🔢 الكمية: {quantity}
💰 الإجمالي: {total} درهم

"""
            
            notify_text += f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 3. إرسال الإشعار للبائع - هذا هو الجزء المهم!
            logger.info(f"🔄 محاولة إرسال إشعار للبائع على الرقم: {SELLER_PHONE_NUMBER}")
            logger.info(f"📤 محتوى الإشعار: {notify_text}")
            
            seller_success = send_whatsapp_message(SELLER_PHONE_NUMBER, notify_text)
            
            if seller_success:
                logger.info(f"✅ تم إرسال إشعار الطلبية بنجاح للبائع من العميل {sender_phone}")
                
                # 4. إرسال تأكيد إضافي للبائع
                confirm_text = f"✅ تم استلام طلبية جديدة من {sender_phone} - الرجاء التواصل مع العميل خلال 30 دقيقة"
                send_whatsapp_message(SELLER_PHONE_NUMBER, confirm_text)
                
            else:
                logger.error(f"❌ فشل إرسال إشعار الطلبية للبائع من العميل {sender_phone}")
                
                # محاولة بديلة: إرسال رسالة مختصرة
                short_notify = f"🚨 طلبية جديدة من {sender_phone} - المنتج: {order_info.get('product', {}).get('ar', 'غير معروف')} - {order_info.get('total', 0)} درهم"
                send_whatsapp_message(SELLER_PHONE_NUMBER, short_notify)
            
            # 5. تنظيف الجلسة بعد إرسال الإشعار
            if sender_phone in self.user_sessions:
                del self.user_sessions[sender_phone]
                logger.info(f"🧹 تم تنظيف جلسة المستخدم {sender_phone}")
            
            # 6. الرد على الزبون
            return self.responses['contact_info_received'][lang]
            
        except Exception as e:
            logger.error(f"💥 خطأ في معالجة معلومات الاتصال: {str(e)}")
            if lang == 'ar':
                return "حدث خطأ في معالجة معلوماتك. يرجى المحاولة مرة أخرى أو الاتصال بنا مباشرة."
            else:
                return "Erreur de traitement. Veuillez réessayer ou nous contacter directement."

# تهيئة البوت
bot = WhatsAppBot()

def send_whatsapp_message(to: str, text: str) -> bool:
    """إرسال رسالة واتساب"""
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
        
        logger.info(f"🔄 إرسال رسالة إلى {to}")
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        logger.info(f"📤 استجابة API: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"✅ تم إرسال الرسالة بنجاح إلى {to}")
            return True
        else:
            logger.error(f"❌ خطأ في إرسال الرسالة: {response.status_code}")
            logger.error(f"📋 تفاصيل الخطأ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("⏰ انتهت مهلة إرسال الرسالة")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"🔌 خطأ في الاتصال: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"💥 خطأ غير متوقع في الإرسال: {str(e)}")
        return False

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """المصافحة مع فيسبوك للتحقق من السيرفر"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    logger.info(f"طلب تحقق: mode={mode}")

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("✅ تم التحقق من الويب هوك بنجاح")
            return challenge, 200
        else:
            logger.warning("❌ فشل التحقق من الويب هوك - توكن غير صحيح")
            return 'Forbidden', 403
    
    return 'Hello World', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """استقبال الرسائل من واتساب"""
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("طلب POST بدون بيانات")
            return 'OK', 200
        
        logger.info("📩 بيانات مستلمة من الويب هوك")
        
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
            message_body = message_data['text']['body']
            
            logger.info(f"📨 رسالة من {phone_number}: {message_body}")
            
            # معالجة الرسالة والحصول على الرد
            reply_text = bot.process_message(message_body, phone_number)
            
            # إرسال الرد للزبون
            success = send_whatsapp_message(phone_number, reply_text)
            
            if success:
                logger.info(f"✅ تم إرسال الرد إلى {phone_number}")
            else:
                logger.error(f"❌ فشل إرسال الرد إلى {phone_number}")
                
    except Exception as e:
        logger.error(f"💥 خطأ في معالجة الويب هوك: {str(e)}")
    
    return 'OK', 200

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة السيرفر"""
    active_sessions = []
    for phone, session in bot.user_sessions.items():
        active_sessions.append({
            'phone': phone,
            'product': session.get('product', {}).get('ar', 'غير معروف'),
            'waiting_since': session.get('timestamp').strftime('%H:%M:%S')
        })
    
    return jsonify({
        'status': 'healthy',
        'service': 'Moujib WhatsApp Bot',
        'version': '3.0',
        'active_sessions_count': len(bot.user_sessions),
        'active_sessions': active_sessions,
        'seller_number': SELLER_PHONE_NUMBER,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/test-notification', methods=['GET'])
def test_notification():
    """اختبار إرسال إشعار للتاجر"""
    test_message = f"""🔔 *اختبار إشعار البوت*

هذه رسالة اختبار من بوت مجيب 
الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ إذا وصلتك هذه الرسالة، فالبوت يعمل بشكل صحيح ويستطيع إرسال الإشعارات إليك!"""
    
    success = send_whatsapp_message(SELLER_PHONE_NUMBER, test_message)
    
    return jsonify({
        'success': success,
        'message': 'تم إرسال رسالة الاختبار',
        'seller_number': SELLER_PHONE_NUMBER,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/debug-sessions', methods=['GET'])
def debug_sessions():
    """تصحيح الجلسات النشطة"""
    return jsonify({
        'active_sessions': bot.user_sessions,
        'count': len(bot.user_sessions)
    }), 200

@app.route('/', methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    return jsonify({
        'message': 'مرحباً بك في Moujib WhatsApp Bot',
        'status': 'يعمل',
        'seller_notifications': 'مفعل',
        'active_sessions': len(bot.user_sessions),
        'endpoints': {
            'webhook': '/webhook',
            'health': '/health',
            'test_notification': '/test-notification',
            'debug_sessions': '/debug-sessions'
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"🚀 تشغيل سيرفر Moujib على المنفذ {port}")
    logger.info(f"📞 رقم البائع: {SELLER_PHONE_NUMBER}")
    logger.info(f"🔧 وضع التصحيح: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)