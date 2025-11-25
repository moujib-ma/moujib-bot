from flask import Flask, request, jsonify
import requests
import os
import logging
import re
from datetime import datetime
import random

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- إعدادات واتساب ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "moujib_token_secret")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "EAAfo3utE4ioBQJ72Y5gkM29CnuSvLVlh3WZBvfKVt5rLLpt8TS15QTW36mLUSZC5Gwg2ZCu7sMDnBHMr5FuDwHuYr9WfASsZAlYIpG06F7pj4tV6e6XdknSMHI6D0YcyuoZB6ptQ4j1prkahIirpDTDPV3ecDWMb3zrwxBeiRgfGiQrfxT2A1CZAZCNZBSZCcAXuk7AZDZD")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "889973017535202")
SELLER_PHONE_NUMBER = "212770890339"
VERSION = "v19.0"

class WhatsAppBot:
    def __init__(self):
        # 🇲🇦 الردود المغربية الأصيلة (بدون تيفيناغ)
        self.responses = {
            'greeting': {
                'ar': "أهلاً وسهلاً بك! 👋\n\n🛍️ *خدماتنا:*\n\n👕 1. كوليكسيون الرجال\n👗 2. كوليكسيون النساء\n💰 3. استعلام عن السعر\n📞 4. التوصيل والدفع\n\nاختر رقم أو اكتب سؤالك!",
                'fr': "Bienvenue chez nous! 👋\n\n🛍️ *Nos services:*\n\n👕 1. Collection Homme\n👗 2. Collection Femme\n💰 3. Demande de prix\n📞 4. Livraison et Paiement\n\nChoisissez un numéro ou écrivez votre question!"
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
        
        # 🇲🇦 المنتجات المغربية
        self.products = {
            'a': {'ar': 'سروال جينز مغربي', 'fr': 'Jean Marocain', 'price': 200},
            'b': {'ar': 'تيشيرت ديال المغربية', 'fr': 'T-shirt Marocain', 'price': 100},
            'c': {'ar': 'جاكيت ديال البرد', 'fr': 'Veste d hiver', 'price': 350},
            'd': {'ar': 'سباطي بلما', 'fr': 'Chaussures sport', 'price': 280},
            'e': {'ar': 'فستان تركي', 'fr': 'Robe Turque', 'price': 250},
            'f': {'ar': 'بلوزة ديال الشربيل', 'fr': 'Chemisier brodé', 'price': 180},
            'g': {'ar': 'شورت ديال ستايل مغربي', 'fr': 'Short style marocain', 'price': 120},
            'h': {'ar': 'كعب ديال العيد', 'fr': 'Talons de fête', 'price': 220}
        }
        
        # 🇲🇦 الكلمات المغربية المميزة (بدون تيفيناغ)
        self.darija_patterns = {
            'greeting': {
                'ar': ['سلام', 'السلام', 'salam', 'slm', 'أهلا', 'بسلامة', 'لاباس', 'واشالك', 'بنعمة'],
                'fr': ['salam', 'slm', 'labas', 'cv', 'bien', 'hello', 'hi', 'bnjrn']
            },
            'browsing': {
                'ar': ['1', 'واحد', 'الحوايج', 'هوايج', 'شوية', 'رجال', 'نساء', 'عيالات', 'سروال', 'جينز', 'تيشيرت', 'سباطي', 'حذاء'],
                'fr': ['1', 'wahd', 'l7wayj', '7wayj', 'chwiya', 'rjal', 'nsa', '3yalat', 'sserwal', 'jeans', 'tichirt', 'ssbati']
            },
            'pricing': {
                'ar': ['3', 'ثلاثة', 'بشحال', 'شحال', 'ثمن', 'سعر', 'prix', 'combien', 'تخفيض', 'promo', 'soldes', 'غالي'],
                'fr': ['3', 'tlata', 'bch7al', 'ch7al', 'taman', 'ssir', 'combien', 'promo', 'solde', 'ghali']
            },
            'delivery': {
                'ar': ['4', 'أربعة', 'توصيل', 'livraison', 'شحون', 'واش كتصيفطو', 'شحال كتعطل', 'فين المحل', 'local', 'magasin', 'واش فابور'],
                'fr': ['4', 'rb3a', 'touslil', 'livraison', 'ch7oun', 'wach ktsyefto', 'ch7al kt3etel', 'fin lm7el', 'wach fabour']
            },
            'ordering': {
                'ar': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'بغيت', 'أريد', 'نبدي', 'كوموند', 'commande', 'شريت', 'acheter', 'سروال كحل'],
                'fr': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'bghit', 'b7al', '3ndi', 'nbeddi', 'chrit']
            },
            'support': {
                'ar': ['مشكل', 'مشكلة', 'probleme', 'عندي مشكل', 'بغيت نهضر مع بنادم', 'human', 'جاوبني', 'reponds', 'القياس', 'taille', 'size', 'بغيت نرجع', 'retour', 'واش كاين'],
                'fr': ['mchkil', '3ndi mchkil', 'bghit nhder m3a bnadm', 'jawbni', 'l9yas', 'bghit nrja3', 'wach kayn']
            },
            'closing': {
                'ar': ['شكرا', 'merci', 'thanks', 'الله يحفظك', 'صافي', 'safi', 'ok', 'd\'accord', 'بسلامة', 'bye', 'تمام'],
                'fr': ['chokran', 'mrc', 'allah yhfedk', 'safi', 'ok', 'd\'accord', 'bslama', 'tamam']
            }
        }
        
        # 🇲🇦 الردود المغربية العفوية (بدون تيفيناغ)
        self.spontaneous_responses = {
            'ar': [
                "واها زوين! ان شاء الله عليك! 😄",
                "الله ما يمتناش مغربي! 🇲🇦",
                "دايما نغييموك! 💪",
                "هيا سي من البلاد! 😎",
                "والله ان شاء الله! ما يكلش والو! 🙏"
            ],
            'fr': [
                "Waha zwin! Inchallah 3lik! 😄",
                "Allah ma yemtnach Maghribi! 🇲🇦",
                "Dayma nghaymouk! 💪",
                "Hya si mn lblad! 😎",
                "Wallah inchallah! Ma ykellch walou! 🙏"
            ]
        }
        
        # 🇲🇦 المدن المغربية
        self.moroccan_cities = [
            'الدار البيضاء', 'كازا', 'casablanca', 'الرباط', 'رباط', 'rabat', 
            'مراكش', 'marrakech', 'فاس', 'fes', 'طنجة', 'tanger', 'مكناس', 'meknes',
            'أكادير', 'agadir', 'تطوان', 'tetouan', 'وجدة', 'oujda', 'الجديدة', 'el jadida',
            'القنيطرة', 'kenitra', 'تمارة', 'temara', 'سلا', 'sale', 'المحمدية', 'mohammedia',
            'بن جرير', 'benguerir', 'خريبكة', 'khouribga', 'الدارلبيضاء', 'دار البيضاء'
        ]
        
        # 🇲🇦 الأحياء الشعبية في المدن
        self.popular_districts = {
            'casablanca': ['عين السبع', 'حي الحسني', 'الحي المحمدي', 'سيدي مؤمن', 'الرويس', 'ابن مسيك'],
            'rabat': ['حي الرياض', 'أكدال', 'حي الحسن', 'توميلين', 'العكاري', 'ياكوماد'],
            'marrakech': ['المراكشي', 'سيدي يوسف بن علي', 'الداوديات', 'المحاميد', 'القيادة'],
            'fes': ['فاس الجديد', 'الدار البيضاء', 'المرينيين', 'الرياض', 'عين قادوس']
        }
        
        # لتتبع حالة المستخدمين
        self.user_sessions = {}
        self.user_context = {}  # لتخزين سياق المحادثة
    
    def detect_language(self, text: str) -> str:
        """اكتشاف لغة النص (عربية أو فرنسية فقط)"""
        arabic_pattern = re.compile('[\u0600-\u06FF]')
        if arabic_pattern.search(text):
            return 'ar'
        return 'fr'
    
    def detect_intent(self, message: str) -> str:
        """اكتشاف نية المستخدم مع فهم الدارجة المغربية"""
        message_lower = message.lower().strip()
        lang = self.detect_language(message)
        
        logger.info(f"🔍 فحص الرسالة: '{message}' - اللغة: {lang}")
        
        # التحقق من كل فئة من نوايا المستخدم
        for intent, patterns in self.darija_patterns.items():
            for pattern in patterns[lang] if lang in patterns else patterns.get('ar', []):
                if pattern in message_lower:
                    logger.info(f"🎯 تم اكتشاف النية: {intent} من الرسالة: {message}")
                    return intent
        
        # اكتشاف المدن المغربية
        for city in self.moroccan_cities:
            if city.lower() in message_lower:
                logger.info(f"🏙️ تم اكتشاف مدينة: {city}")
                return 'delivery'
        
        # إذا كانت الرسالة تحتوي على أرقام هواتف مغربية أو عناوين
        if re.search(r'06[0-9]{8}|07[0-9]{8}|05[0-9]{8}', message_lower) or \
           any(word in message_lower for word in ['حي', 'زنقة', 'شارع', 'درب', 'quartier', 'rue', 'derb']):
            return 'contact_info'
        
        return 'unknown'
    
    def get_moroccan_style_response(self, lang: str) -> str:
        """إرجاع رد مغربي عفوي بين الحين والآخر"""
        if random.random() < 0.3:  # 30% فرصة لرد عفوي
            responses = self.spontaneous_responses[lang]
            return f"\n\n{random.choice(responses)}"
        return ""
    
    def process_message(self, message: str, sender_phone: str) -> str:
        """معالجة الرسالة بإسلوب مغربي أصيل"""
        message_lower = message.lower().strip()
        lang = self.detect_language(message)
        
        logger.info(f"🔍 معالجة رسالة من {sender_phone}: '{message}'")
        
        # 🔥 الأولوية: إذا كان المستخدم لديه جلسة نشطة
        if sender_phone in self.user_sessions and self.user_sessions[sender_phone].get('waiting_for_contact'):
            logger.info(f"🎯 المستخدم {sender_phone} لديه جلسة نشطة - معالجة كمعلومات اتصال")
            return self.process_contact_info(message, lang, sender_phone)
        
        # اكتشاف نية المستخدم
        intent = self.detect_intent(message)
        logger.info(f"🧠 النية المكتشفة: {intent}")
        
        # معالجة حسب النية
        if intent == 'greeting':
            response = self.responses['greeting'][lang]
            spontaneous = self.get_moroccan_style_response(lang)
            return response + spontaneous
        
        elif intent == 'browsing':
            if any(word in message_lower for word in ['1', 'رجال', 'rjal', 'homme', 'male']):
                response = self.responses['men_collection'][lang]
            elif any(word in message_lower for word in ['2', 'نساء', 'nsa', 'femme', 'women']):
                response = self.responses['women_collection'][lang]
            else:
                response = self.responses['greeting'][lang]
            
            spontaneous = self.get_moroccan_style_response(lang)
            return response + spontaneous
        
        elif intent == 'pricing':
            response = self.responses['pricing'][lang]
            spontaneous = self.get_moroccan_style_response(lang)
            return response + spontaneous
        
        elif intent == 'delivery':
            # معالجة خاصة للاستفسارات عن المدن
            city_found = None
            for city in self.moroccan_cities:
                if city.lower() in message_lower:
                    city_found = city
                    break
            
            base_response = self.responses['delivery'][lang]
            
            if city_found:
                if lang == 'ar':
                    city_response = f"\n\n📍 نعم كنديرو التوصيل ل{city_found}!"
                    if 'كازا' in city_found or 'الدار البيضاء' in city_found:
                        city_response += " التوصيل مجاني لك!"
                    elif 'رباط' in city_found:
                        city_response += " التوصيل مجاني عليك!"
                    else:
                        city_response += " التوصيل ب20 درهم سير زوين!"
                else:
                    city_response = f"\n\n📍 Oui on livre à {city_found}!"
                    if 'casa' in city_found.lower():
                        city_response += " Livraison gratuite!"
                    elif 'rabat' in city_found.lower():
                        city_response += " Livraison gratuite!"
                    else:
                        city_response += " Livraison à 20 DH!"
                
                base_response += city_response
            
            spontaneous = self.get_moroccan_style_response(lang)
            return base_response + spontaneous
        
        elif intent == 'ordering':
            return self.process_order(message_lower, lang, sender_phone)
        
        elif intent == 'support':
            return self.handle_support(message_lower, lang, sender_phone)
        
        elif intent == 'closing':
            return self.handle_closing(message_lower, lang, sender_phone)
        
        elif intent == 'contact_info':
            # إذا أرسل معلومات اتصال بدون طلب مسبق
            if lang == 'ar':
                return "شكراً على معلوماتك! 📝\n\nولكن كيما تبدلاتي ما تخترتيش شي حاجة من القايمونة. المرجوع تختاري حاجة ولا تساند معلومات التوصيل."
            else:
                return "Merci pour vos informations! 📝\n\nMais comme vous avez changé, vous n'avez pas choisi quelque chose du menu. Le retour, vous choisissez quelque chose ou vous envoyez les informations de livraison."
        
        else:
            # إذا لم يتم التعرف على النية
            base_response = self.responses['greeting'][lang]
            if lang == 'ar':
                additional = "\n\nسمحتي ما فهمتش! زيد سؤالك ولا اكتب مرة أخرى!"
            else:
                additional = "\n\nDésolé je n'ai pas compris! Ajoutez votre question ou écrivez à nouveau!"
            
            spontaneous = self.get_moroccan_style_response(lang)
            return base_response + additional + spontaneous
    
    def process_order(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة طلب المنتج بإسلوب مغربي"""
        try:
            logger.info(f"🛒 بدء معالجة طلب من {sender_phone}: {message}")
            
            product_code = None
            # البحث عن الحرف في الرسالة
            for char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
                if char in message:
                    product_code = char
                    break
            
            if not product_code or product_code not in self.products:
                logger.warning(f"❌ رمز المنتج غير صحيح: {product_code}")
                if lang == 'ar':
                    return "❌ ما تعرفتوش على لي طلبتي!\n\n📋 المرجوع تختار حرف من القايمونة:\nA, B, C, D للرجال\nE, F, G, H للنساء"
                else:
                    return "❌ Je n'ai pas reconnu ce que vous avez demandé!\n\n📋 Veuillez choisir une lettre du menu:\nA, B, C, D pour Homme\nE, F, G, H pour Femme"
            
            # استخراج الكمية
            quantity = 1
            numbers = re.findall(r'\d+', message)
            if numbers:
                quantity = int(numbers[0])
                quantity = min(quantity, 10)  # حد أقصى 10 قطع
            
            product = self.products[product_code]
            total = product['price'] * quantity
            
            # 🔥 حفظ معلومات الطلب مؤقتاً
            self.user_sessions[sender_phone] = {
                'product': product,
                'quantity': quantity,
                'total': total,
                'timestamp': datetime.now(),
                'waiting_for_contact': True
            }
            
            logger.info(f"✅ تم حفظ طلب من {sender_phone}: {product['ar']} x {quantity} = {total} درهم")
            
            if lang == 'ar':
                return f"""✅ تم تسجيل اختيارك!

📦 الحاجة: {product['ar']}
🔢 الكمية: {quantity}
💰 المجموع: {total} درهم

⬇️ *عاش تكمل الطلببة، ساندلنا دابا:*
👤 الاسم الكامل
📍 العنوان المفصل (الشارع، الحي، المدينة)
📞 رقم التلفون لي نتوصلو به

غادي نوصلو بيك للتأكيد النهائي! 📞"""
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
            logger.error(f"💥 خطأ في معالجة الطلب: {str(e)}")
            if lang == 'ar':
                return "سمحتي ما تمشيتش الطلببة! زيد مرة أخرى."
            else:
                return "Désolé, la commande n'a pas fonctionné! Réessayez."
    
    def handle_support(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة طلبات الدعم بإسلوب مغربي"""
        if 'human' in message.lower() or 'بنادم' in message or 'bdem' in message:
            if lang == 'ar':
                return """🆘 *مركز المساعدة*

للإتصال بممثل خدمة العملاء:
📞 0522-123456

أو راسلنا على:
📧 support@moujib.ma

ساعات الخدمة:
⏰ 9:00 - 18:00 (الإثنين - السبت)

للاستفسارات الفورية، اكتب سؤالك وغادي نعاونوك!"""
            else:
                return """🆘 *Centre d'Aide*

Pour contacter un représentant:
📞 0522-123456

Ou écrivez-nous à:
📧 support@moujib.ma

Heures d'ouverture:
⏰ 9:00 - 18:00 (Lundi - Samedi)

Pour des questions immédiates, écrivez votre question et nous vous aiderons!"""
        else:
            if lang == 'ar':
                return "تشانقلو نعاونوك على مشكلتك! 💪\n\nسمحتي ليًا تقدر تسمعني تشانقلو ما تستعجلش عليك?\n\nولا راسل سؤالك مرة أخرى وغادي نفهموه لك!"
            else:
                return "On va vous aider avec votre problème! 💪\n\nDésolé si vous pouvez m'écouter, on va vous aider, ne vous inquiétez pas?\n\nOu envoyez votre question à nouveau et on va la comprendre pour vous!"
    
    def handle_closing(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة نهاية المحادثة بإسلوب مغربي"""
        if lang == 'ar':
            responses = [
                "شكراً عليك! 🙏\n\nان شاء الله تبقى ليمتيحان معاك! ما تسمعش شي حاجة من غادي! 🇲🇦\n\nمع السلامة 👋",
                "الله يحفظني وإياك! 🤲\n\nتمام ان شاء الله تبقى ليمتيحان! ما تسمعش شي حاجة نغييموك! 💪\n\nبسلامة 👋",
                "شكراً بزاف! 😊\n\nان شاء الله تبقى ليمتيحان معاك! ما تسمعش شي حاجة نغييموك! 🙏\n\nمع السلامة 👋"
            ]
        else:
            responses = [
                "Merci à vous! 🙏\n\nInchallah vous restez satisfait! N'écoutez rien pour plus tard! 🇲🇦\n\nAu revoir 👋",
                "Allah me protège et vous! 🤲\n\nParfait inchallah vous restez satisfait! N'écoutez rien on vous aide! 💪\n\nSalut 👋",
                "Merci beaucoup! 😊\n\nInchallah vous restez satisfait avec nous! N'écoutez rien on vous aide! 🙏\n\nAu revoir 👋"
            ]
        
        return random.choice(responses)
    
    def process_contact_info(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة معلومات الاتصال وإرسال إشعار للبائع"""
        try:
            logger.info(f"📞 بدء معالجة معلومات الاتصال من {sender_phone}")
            
            # 1. الحصول على معلومات الطلب من الجلسة
            order_info = self.user_sessions.get(sender_phone, {})
            
            if not order_info:
                logger.error(f"❌ لا توجد جلسة للمستخدم {sender_phone}")
                if lang == 'ar':
                    return "سمحتي ما تمشيتش الطلببة! زيد مرة أخرى."
                else:
                    return "Désolé, la commande n'a pas fonctionné! Réessayez."
            
            # 2. إنشاء رسالة الإشعار للبائع
            product = order_info.get('product', {})
            quantity = order_info.get('quantity', 1)
            total = order_info.get('total', 0)
            
            notify_text = f"""🚨 *طلبية جديدة!*

📞 العميل: {sender_phone}
📝 المعلومات المقدمة:
{message}

🛒 *تفاصيل الطلب:*
📦 المنتج: {product.get('ar', 'غير محدد')} / {product.get('fr', 'N/A')}
🔢 الكمية: {quantity}
💰 الإجمالي: {total} درهم

⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # 3. إرسال الإشعار للبائع
            logger.info(f"🔄 محاولة إرسال إشعار للبائع على الرقم: {SELLER_PHONE_NUMBER}")
            seller_success = send_whatsapp_message(SELLER_PHONE_NUMBER, notify_text)
            
            if seller_success:
                logger.info(f"🎉 تم إرسال إشعار الطلبية بنجاح للبائع من العميل {sender_phone}")
                
                # إرسال تأكيد إضافي للبائع
                confirm_text = f"✅ تم استلام طلبية جديدة من {sender_phone} - الرجاء التواصل مع العميل خلال 30 دقيقة"
                send_whatsapp_message(SELLER_PHONE_NUMBER, confirm_text)
                
            else:
                logger.error(f"❌ فشل إرسال إشعار الطلبية للبائع من العميل {sender_phone}")
                
                # محاولة بديلة: إرسال رسالة مختصرة
                short_notify = f"🚨 طلبية جديدة من {sender_phone} - المنتج: {product.get('ar', 'غير معروف')} - {total} درهم"
                send_whatsapp_message(SELLER_PHONE_NUMBER, short_notify)
            
            # 4. تنظيف الجلسة بعد إرسال الإشعار
            if sender_phone in self.user_sessions:
                del self.user_sessions[sender_phone]
                logger.info(f"🧹 تم تنظيف جلسة المستخدم {sender_phone}")
            
            # 5. الرد على الزبون
            logger.info(f"📨 إرسال تأكيد للزبون {sender_phone}")
            
            if lang == 'ar':
                return f"""✅ تم قبول معلوماتك بنجاح!

📞 غادي يوصلو بيك فريقنا خلال 30 دقيقة للتأكيد النهائي للطلبية.

شكراً على توقيتك بينا! 🤝

{random.choice(self.spontaneous_responses['ar'])}"""
            else:
                return f"""✅ Informations acceptées avec succès!

📞 Notre équipe vous contactera dans 30 minutes pour confirmation finale.

Merci de votre temps avec nous! 🤝

{random.choice(self.spontaneous_responses['fr'])}"""
            
        except Exception as e:
            logger.error(f"💥 خطأ في معالجة معلومات الاتصال: {str(e)}")
            if lang == 'ar':
                return "سمحتي وقع مشكل في معالمة معلوماتك. المرجوع جرب مرة أخرى أو الإتصال بينا بشيخة."
            else:
                return "Désolé, un problème est survenu lors du traitement de vos informations. Veuillez réessayer ou nous contacter directement."

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

# بقية الكود (الويب هوك والرواتب) تبقى كما هي
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
            'quantity': session.get('quantity', 1),
            'total': session.get('total', 0),
            'waiting_since': session.get('timestamp').strftime('%H:%M:%S') if session.get('timestamp') else 'غير معروف'
        })
    
    return jsonify({
        'status': 'صحي',
        'service': 'موجيب بوت',
        'version': '🇲🇦 مغربي 100%',
        'active_sessions_count': len(bot.user_sessions),
        'active_sessions': active_sessions,
        'seller_number': SELLER_PHONE_NUMBER,
        'features': ['دارجة مغربية', 'فرنسية', 'توصيل مجاني'],
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"🚀 تشغيل سيرفر موجيب على المنفذ {port}")
    logger.info(f"📞 رقم البائع: {SELLER_PHONE_NUMBER}")
    logger.info(f"🇲🇦 البوت مغربي 100% - جاهز للخدمة!")
    logger.info(f"🔧 وضع التصحيح: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)