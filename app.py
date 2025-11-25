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
        # 🇲🇦 الردود المغربية الأصيلة
        self.responses = {
            'greeting': {
                'ar': "ⴰⵀⵍⴰⵏ ⵡⴰⵙⴰⵍⴰⵎ ⵍⴽ! 👋\n\n🛍️ *ⵙⵔⴷⵖⵉⵏ ⴷⵔⴱⵉ ⵏⴽ:*\n\n👕 1. ⵍⵃⵡⴰⵢⴰⵊ ⵏ ⵉⵔⴳⴰⵣⵏ\n👗 2. ⵍⵃⵡⴰⵢⴰⵊ ⵏ ⵉⵙⴽⵜⵓⵔⵏ\n💰 3. ⵙⵉⵔ ⵏ ⵍⵎⵏⵙⴰ\n🚚 4. ⵜⵜⵓⵚⵍⵉⵍ ⵡⴰⵍⵙⵍⴼ\n\nⴷⵉⵔ ⵕⵇⵎ ⵡⵍⴰ ⵉⴽⵜⴱ ⵙⵓⴰⵍⴽ!",
                'fr': "Ahlan wsalam lik! 👋\n\n🛍️ *Services darbi nk:*\n\n👕 1. L7wayj n Irgazn\n👗 2. L7wayj n Iskturn\n💰 3. Ssir l mnsa\n🚚 4. Ttouslil w slf\n\nDir rakam wla kteb soualak!"
            },
            'men_collection': {
                'ar': "🔥 *ⵍⵃⵡⴰⵢⴰⵊ ⵏ ⵉⵔⴳⴰⵣⵏ:*\n\n👖 A. ⵙⵔⵡⴰⵍ ⵊⵉⵏⵣ - 200 ⴷⵔⵀⵎ\n👕 B. ⵜⵉⵛⵉⵔⵜ - 100 ⴷⵔⵀⵎ\n🧥 C. ⵊⴰⴽⵉⵜ - 350 ⴷⵔⵀⵎ\n👟 D. ⵙⴱⴰⵜⵉ - 280 ⴷⵔⵀⵎ\n\nⵃⵜⵜ ⵍⵉⴳⵔⴰⵎ ⵅⴼ ⵍⵇⵜⵉⵢⴰ (ⵎⵜⵍ: A 2)",
                'fr': "🔥 *L7wayj n Irgazn:*\n\n👖 A. Sserwal Jeans - 200 DH\n👕 B. Tichirt - 100 DH\n🧥 C. Jakett - 350 DH\n👟 D. Ssbati - 280 DH\n\n7ett lgram w l9tiya (mtl: A 2)"
            },
            'women_collection': {
                'ar': "💫 *ⵍⵃⵡⴰⵢⴰⵊ ⵏ ⵉⵙⴽⵜⵓⵔⵏ:*\n\n👗 A. ⴼⵙⵜⴰⵏ - 250 ⴷⵔⵀⵎ\n👚 B. ⴱⵍⵣⴰ - 180 ⴷⵔⵀⵎ\n🩳 C. ⵛⵓⵔⵜ - 120 ⴷⵔⵀⵎ\n👠 D. ⴽⵄⴱ - 220 ⴷⵔⵀⵎ\n\nⵃⵜ ⵍⵉⴳⵔⴰⵎ ⵅⴼ ⵍⵇⵜⵉⵢⴰ",
                'fr': "💫 *L7wayj n Iskturn:*\n\n👗 A. Fstan - 250 DH\n👚 B. Blouza - 180 DH\n🩳 C. Short - 120 DH\n👠 D. K3ab - 220 DH\n\n7ett lgram w l9tiya"
            },
            'pricing': {
                'ar': "💰 *ⵙⵉⵔ ⵏ ⵍⵎⵏⵙⴰ:*\n\n• ⵙⵉⵔⴰⵜ ⵎⵏ 100 ⴷⵔⵀⵎ\n• ⵜⵅⵙⵉⵙ 10% ⵉⵍⴰ ⵍⵜⵍⴰⴱⴰⵜ ⵍⵍⵉ ⴼⵓⵇ 500 ⴷⵔⵀⵎ\n• ⵜⵜⵓⵚⵍⵉⵍ ⵎⴳⵔⴰⵏⵉ ⵉⵍⴰ ⵍⵜⵍⴰⴱⴰⵜ ⵍⵍⵉ ⴼⵓⵇ 300 ⴷⵔⵀⵎ\n• ⵍⴷⴼⵄ ⵜⵍⵇⴰ ⵉⵍⴰ ⵍⵉⵙⵜⵍⵎ ⵡⵍⴰ ⵜⵀⵡⵉⵍ ⴱⴰⵏⴽⵉ\n\nⵍⵍⵉⵙⵜⵉⴼⵙⴰⵔ 3ⵍⴰ ⵛⵉ ⵃⴰⵊⴰ ⵙⵓⵢⴰ، ⵉⴽⵜⴱ ⵙⵎⵉⵜⵀ!",
                'fr': "💰 *Ssir l mnsa:*\n\n• Ssirat mn 100 DH\n• Tkhesis 10% l talabat lli foug 500 DH\n• Ttouslil mgrani l talabat lli foug 300 DH\n• Ldfa3 tleqa 3la listlam wla thwil banki\n\nLlistifssar 3la chi haja swiya, kteb smitha!"
            },
            'delivery': {
                'ar': "🚚 *ⵜⵜⵓⵚⵍⵉⵍ:*\n\n• ⵜⵜⵓⵚⵍⵉⵍ ⵅⵍⴰⵍ 24-48 ⵙⴰⵄⴰ\n• ⵎⴳⵔⴰⵏⵉ ⵍⴷⴷⴰⵔ ⵍⴱⵉⴹⴰ ⵡⵔⵔⴱⴰⵟ\n• 20 ⴷⵔⵀⵎ ⵍⵍⵎⴷⵏ ⵍⵅⵔⴰ\n• ⵏⵅⴷⵎⵓ ⵎⵏ ⵍⵉⵜⵏⵉⵏ ⵍⵉⵙⵙⴱⵜ\n\nⵍⵜⵜⴱⵄ ⵡⵍⴰ ⵍⵉⵙⵜⵉⴼⵙⴰⵔ، ⵔⴰⵙⵍⵏⴰ!",
                'fr': "🚚 *Ttouslil:*\n\n• Ttouslil khlal 24-48 sa3a\n• Mgrani l ddare lbida w rrbat\n• 20 DH l lmdn lkhra\n• Nkhdmo mn litnin l ssbt\n\nL ttb3 wla listifssar, rasselna!"
            }
        }
        
        # 🇲🇦 المنتجات المغربية
        self.products = {
            'a': {'ar': 'ⵙⵔⵡⴰⵍ ⵊⵉⵏⵣ ⵎⵖⵔⴱⵉ', 'fr': 'Sserwal Jeans Maghribi', 'price': 200},
            'b': {'ar': 'ⵜⵉⵛⵉⵔⵜ ⴷⵉⵍ ⵎⵖⵔⴱⵉⵢⴰ', 'fr': 'Tichirt Dl Maghribiya', 'price': 100},
            'c': {'ar': 'ⵊⴰⴽⵉⵜ ⵏ ⵍⴱⵔⵔⴰⴷ', 'fr': 'Jakett n Lbrrad', 'price': 350},
            'd': {'ar': 'ⵙⴱⴰⵜⵉ ⴱⵍⵎⴰ', 'fr': 'Ssbati Blma', 'price': 280},
            'e': {'ar': 'ⴼⵙⵜⴰⵏ ⵜⵔⴽⵉ', 'fr': 'Fstan Tarki', 'price': 250},
            'f': {'ar': 'ⴱⵍⵣⴰ ⴷⵉⵍ ⵛⵔⴱⵉⵍ', 'fr': 'Blouza Dl Chrbil', 'price': 180},
            'g': {'ar': 'ⵛⵓⵔⵜ ⵏ ⵙⵜⵉⵍ ⵎⵖⵔⴱⵉ', 'fr': 'Short n Stil Maghribi', 'price': 120},
            'h': {'ar': 'ⴽⵄⴱ ⵏ ⵍⵄⵉⴷ', 'fr': 'K3ab n L3id', 'price': 220}
        }
        
        # 🇲🇦 الكلمات المغربية المميزة
        self.darija_patterns = {
            'greeting': {
                'ar': ['سلام', 'السلام', 'salam', 'slm', 'ⵙⵍⴰⵎ', 'ⴰⵀⵍⴰⵏ', 'ⴱⵙⵍⵎⴰ', 'ⵍⴰⴱⴰⵙ', 'ⵡⴰⵛⴰⵍⴽ', 'ⴱⵏⴰⵎ'],
                'fr': ['salam', 'slm', 'labas', 'cv', 'bien', 'hello', 'hi', 'bnjrn']
            },
            'browsing': {
                'ar': ['1', 'واحد', 'ⵡⴰⵀⴷ', 'ⵍⵃⵡⴰⵢⴰⵊ', 'ⵃⵡⴰⵢⴰⵊ', 'ⵛⵡⵉⵢⴰ', 'رجال', 'ⵉⵔⴳⴰⵣⵏ', 'نساء', 'ⵉⵙⴽⵜⵓⵔⵏ', 'عيالات', 'سروال', 'ⵙⵔⵡⴰⵍ', 'جينز', 'تيشيرت', 'ⵜⵉⵛⵉⵔⵜ', 'سبادري', 'ⵙⴱⴰⵜⵉ', 'حذاء'],
                'fr': ['1', 'wahd', 'l7wayj', '7wayj', 'chwiya', 'rjal', 'nsa', '3yalat', 'sserwal', 'jeans', 'tichirt', 'ssbati']
            },
            'pricing': {
                'ar': ['3', 'ثلاثة', 'ⵜⵍⴰⵜⴰ', 'بشحال', 'ⴱⵛⵃⴰⵍ', 'شحال', 'ⵛⵃⴰⵍ', 'ثمن', 'ⵜⵎⴰⵏ', 'سعر', 'ⵙⵉⵔ', 'prix', 'combien', 'ⴽⵓⵎⴱⵢⴰⵏ', 'تخفيض', 'ⵜⵅⵙⵉⵙ', 'promo', 'soldes', 'غالي', 'ⵖⴰⵍⵉ'],
                'fr': ['3', 'tlata', 'bch7al', 'ch7al', 'taman', 'ssir', 'combien', 'promo', 'solde', 'ghali']
            },
            'delivery': {
                'ar': ['4', 'أربعة', 'ⵔⴱⵄⴰ', 'توصيل', 'ⵜⵜⵓⵚⵍⵉⵍ', 'livraison', 'شحون', 'ⵛⵃⵓⵏ', 'واش كتصيفطو', 'ⵡⴰⵛ ⴽⵜⵚⵢⴼⵟⵓ', 'شحال كتعطل', 'ⵛⵃⴰⵍ ⴽⵜⵄⵟⵍ', 'فين المحل', 'ⴼⵉⵏ ⵍⵎⵃⵍ', 'local', 'magasin', 'واش فابور', 'ⵡⴰⵛ ⴼⴰⴱⵓⵔ'],
                'fr': ['4', 'rb3a', 'touslil', 'livraison', 'ch7oun', 'wach ktsyefto', 'ch7al kt3etel', 'fin lm7el', 'wach fabour']
            },
            'ordering': {
                'ar': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'بغيت', 'ⴱⵖⵉⵜ', 'أريد', 'نبدي', 'ⵏⴱⴷⵉ', 'كوموند', 'commande', 'شريت', 'ⵛⵔⵉⵜ', 'acheter', 'سروال كحل', 'ⵙⵔⵡⴰⵍ ⴽⵃⵍ'],
                'fr': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'bghit', 'b7al', '3ndi', 'nbeddi', 'chrit']
            },
            'support': {
                'ar': ['مشكل', 'ⵎⵛⴽⵍ', 'مشكلة', 'probleme', 'عندي مشكل', 'ⵄⵏⴷⵉ ⵎⵛⴽⵍ', 'بغيت نهضر مع بنادم', 'ⴱⵖⵉⵜ ⵏⵀⴹⵔ ⵎⵄⴰ ⴱⵏⴰⴷⵎ', 'human', 'جاوبني', 'ⵊⴰⵡⴱⵏⵉ', 'reponds', 'القياس', 'ⵍⵇⵢⴰⵙ', 'taille', 'size', 'بغيت نرجع', 'ⴱⵖⵉⵜ ⵏⵔⵊⴰⵄ', 'retour', 'واش كاين', 'ⵡⴰⵛ ⴽⴰⵢⵏ'],
                'fr': ['mchkil', '3ndi mchkil', 'bghit nhder m3a bnadm', 'jawbni', 'l9yas', 'bghit nrja3', 'wach kayn']
            },
            'closing': {
                'ar': ['شكرا', 'ⵛⵓⴽⵔⴰⵏ', 'merci', 'الله يحفظك', 'ⴰⵍⵍⴰⵀ ⵢⵃⴼⴹⴽ', 'صافي', 'ⵚⴰⴼⵉ', 'safi', 'ok', 'd\'accord', 'بسلامة', 'ⴱⵙⵍⴰⵎⴰ', 'bye', 'ⵜⵎⴰⵎ'],
                'fr': ['chokran', 'mrc', 'allah yhfedk', 'safi', 'ok', 'd\'accord', 'bslama', 'tamam']
            }
        }
        
        # 🇲🇦 الردود المغربية العفوية
        self.spontaneous_responses = {
            'ar': [
                "ⵡⴰⵀⴰ ⵣⵉⵏⵏ! ⵏⵛⴰⵍⵍⴰⵀ ⵄⵍⵉⴽ! 😄",
                "ⵉⵍⵍⴰ ⵙⵉ ⵎⴰⵢⵎⵏⵜⵛ ⵎⵖⵔⴱⵉ! 🇲🇦",
                "ⴷⴰⵢⵎⴰ ⵏⵖⵢⵢⵎⵓ ⵍⴽ! 💪",
                "ⵀⵢⴰ ⵙⵉ ⵎⵏ ⵍⴱⵍⴰⴷ! 😎",
                "ⵡⴰⵍⵍⴰⵀ ⵏⵛⴰⵍⵍⴰⵀ! ⵎⴰⵢⴽⵍⵛⵛ ⵡⴰⵍⵓ! 🙏"
            ],
            'fr': [
                "Waha zine! Nchallah 3lik! 😄",
                "Illa si maymntch Maghribi! 🇲🇦",
                "Dayma nghyyemo lik! 💪",
                "Hya si mn lblad! 😎",
                "Wallah nchallah! Maykllch walou! 🙏"
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
        """اكتشاف لغة النص مع التركيز على الدارجة"""
        arabic_pattern = re.compile('[\u0600-\u06FF]')
        tifinagh_pattern = re.compile('[\u2D30-\u2D7F]')
        
        if tifinagh_pattern.search(text):
            return 'ar'  # نعتبر التيفيناغ عربية
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
            if any(word in message_lower for word in ['1', 'رجال', 'rjal', 'ⵉⵔⴳⴰⵣⵏ', 'homme', 'male']):
                response = self.responses['men_collection'][lang]
            elif any(word in message_lower for word in ['2', 'نساء', 'nsa', 'ⵉⵙⴽⵜⵓⵔⵏ', 'femme', 'women']):
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
                        city_response += " ⵜⵜⵓⵚⵍⵉⵍ ⵎⴳⵔⴰⵏⵉ ⵍⴽ!"
                    elif 'رباط' in city_found:
                        city_response += " ⵍⵜⵜⵓⵚⵍⵉⵍ ⵎⴳⵔⴰⵏⵉ ⵄⵍⵉⴽ!"
                    else:
                        city_response += " ⵜⵜⵓⵚⵍⵉⵍ ⴱ20 ⴷⵔⵀⵎ ⵙⵉⵔ ⵣⵡⵉⵏ!"
                else:
                    city_response = f"\n\n📍 Oui on livre à {city_found}!"
                    if 'casa' in city_found.lower():
                        city_response += " Livraison gratuite!"
                    elif 'rabat' in city_found.lower():
                        city_response += " Livraison mgrani!"
                    else:
                        city_response += " Livraison b 20 DH sir zwine!"
                
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
                return "ⵛⵓⴽⵔⴰⵏ ⵄⵍⴰ ⵎⵄⵍⵓⵎⴰⵜⴽ! 📝\n\nⵡⴰⵍⴰⴽⵉⵏ ⴽⵢⵏ ⴱⵍⵉ ⵎⴰ ⵣⴰⴷⵜⵉ ⵎⴰ ⵜⵉⵅⵜⴰⵔ ⵛⵉ ⵃⴰⵊⴰ ⵎⵏ ⵍⵇⴰⵢⵎⵓⵏ. ⵍⵎⵔⵊⵄ ⵜⵉⵅⵜⴰⵔ ⵃⴰⵊⴰ ⵡⵍⴰ ⵜⵙⵙⵏⴷ ⵎⵄⵍⵓⵎⴰⵜ ⵍⵜⵜⵓⵚⵍⵉⵍ."
            else:
                return "Chokran 3la ma3lomatk! 📝\n\nWalakin kayn bli mazadti machi tkhtar chi haja mn lkaymun. Lmerja3 tkhtar haja wla tsnd ma3lomat ttouslil."
        
        else:
            # إذا لم يتم التعرف على النية
            base_response = self.responses['greeting'][lang]
            if lang == 'ar':
                additional = "\n\nⵙⵎⵃⵜⵉ ⵎⴰ ⴼⵀⵎⵜⵛⵀ! ⵣⵉⴷ ⵙⵓⴰⵍⴽ ⵡⵍⴰ ⵉⴽⵜⴱ ⵎⵔⵔⵜ ⵅⵕⴰ!"
            else:
                additional = "\n\nSm7ti ma fhemtch! Zid soualak wla kteb mrrta khra!"
            
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
                    return "❌ ⵎⴰ ⵜⵉⵜⵇⵔⵔⵏⵛ ⵍⵍⵉ ⵜⵍⴱⵜⵉ!\n\n📋 ⵍⵎⵔⵊⵄ ⵜⵉⵅⵜⴰⵔ ⵍⵉⴳⵔⴰⵎ ⵎⵏ ⵍⵇⴰⵢⵎⵓⵏ:\nA, B, C, D ⵍⵉⵔⴳⴰⵣⵏ\nE, F, G, H ⵍⵉⵙⴽⵜⵓⵔⵏ"
                else:
                    return "❌ Ma tetqerrnch lli tlbati!\n\n📋 Lmerja3 tkhtar lgram mn lkaymun:\nA, B, C, D l Irgazn\nE, F, G, H l Iskturn"
            
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
                return f"""✅ ⵜⵎ ⵜⵙⵊⵉⵍ ⵜⵉⵅⵜⵉⵔⴰⴽ!

📦 ⵍⵃⴰⵊⴰ: {product['ar']}
🔢 ⵍⵇⵜⵉⵢⴰ: {quantity}
💰 ⵍⵎⴳⵎⵓⵄ: {total} ⴷⵔⵀⵎ

⬇️ *ⵄⴰⵛ ⵜⴽⵎⵍ ⵍⵜⵍⴰⴱⴰ، ⵙⵙⵏⴷⵍⵏⴰ ⴷⴰⴱⴰ:*
👤 ⵍⵉⵙⵎ ⵍⴽⴰⵎⵍ
📍 ⵍⵄⵏⵡⴰⵏ ⵎⴼⵚⵚⵍ (ⵛⵢⴰⵄ، ⵃⵉ، ⵍⵎⴷⵉⵏⴰ)
📞 ⵕⵇⵎ ⵍⵜⵍⵉⴼⵓⵏ ⵍⵍⵉ ⵏⵜⵡⵙⵍⵓ ⴱⵀ

ⵖⴰⴷⵉ ⵏⵡⵙⵍⵓ ⴱⴽ ⵍⵜⴰⵢⵉⴽⵉⴷ ⵏⵉⵀⴰⵢⵉ! 📞"""
            else:
                return f"""✅ Tm tsjil tkhtirak!

📦 Lhaja: {product['fr']}
🔢 L9tiya: {quantity}
💰 Lmgmu3: {total} DH

⬇️ *3ach tkeml tlaba, ssendlna daba:*
👤 Lism lkamel
📍 L3nwan mfssel (chi3a, 7i, lmdina)
📞 Rqem ltelfoun lli ntweslo bh

Ghadi nweslo bk ltaykid nihayi! 📞"""
        
        except Exception as e:
            logger.error(f"💥 خطأ في معالجة الطلب: {str(e)}")
            if lang == 'ar':
                return "ⵙⵎⵃⵜⵉ ⵎⴰ ⵜⵎⵛⵉⵜⵛ ⵍⵜⵍⴰⴱⴰ! ⵣⵉⴷ ⵎⵔⵔⵜ ⵅⵕⴰ."
            else:
                return "Sm7ti ma tmchitch tlaba! Zid mrrta khra."
    
    def handle_support(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة طلبات الدعم بإسلوب مغربي"""
        if 'human' in message.lower() or 'بنادم' in message or 'bdem' in message:
            if lang == 'ar':
                return """🆘 *ⵍⵎⵔⴽⵣ ⵏ ⵍⵎⵙⴰⵄⴷⴰ*

ⵍⵍⵉⵜⵙⴰⵍ ⴱⵎⵎⵜⵍ ⵖⵚⵚ ⵏ ⵍⵎⵙⴰⵄⴷⴰ:
📞 0522-123456

ⵡⵍⴰ ⵔⴰⵙⵍⵏⴰ ⵄⵍⴰ:
📧 support@moujib.ma

ⵙⴰⵄⴰⵜ ⵍⵅⴷⵎⴰ:
⏰ 9:00 - 18:00 (ⵍⵉⵜⵏⵉⵏ - ⵍⵉⵙⵙⴱⵜ)

ⵍⵍⵉⵙⵜⵉⴼⵙⴰⵔⴰⵜ ⵍⴼⵓⵔⵉⵢⴰ، ⵉⴽⵜⴱ ⵙⵓⴰⵍⴽ ⵡⵖⴰⴷⵉ ⵏⵙⴰⵄⴷⵓⴽ!"""
            else:
                return """🆘 *Lmerkez n lmsa3da*

L litsal b mmtel ghss n lmsa3da:
📞 0522-123456

Wla rasselna 3la:
📧 support@moujib.ma

Sa3at lkhdma:
⏰ 9:00 - 18:00 (Litnin - Lissbt)

L listifssarat lforiya, kteb soualak wghadi nsa3dok!"""
        else:
            if lang == 'ar':
                return "ⵛⵏⵅⵍⴼ ⵏⵙⴰⵄⴷⵓⴽ ⵄⵍⴰ ⵎⵛⴽⵍⴽ! 💪\n\nⵙⵎⵃⵜⵉ ⵍⵉⴰ ⵜⵇⴷⵔ ⵜⵙⵎⵄⵏⵉ ⵛⵏⵅⵍⴼ ⵎⴰ ⵜⵉⵙⵜⴰⵄⵊⵍⵛ ⵄⵍⵉⴽ?\n\nⵡⵍⴰ ⵔⴰⵙⵍ ⵙⵓⴰⵍⴽ ⵎⵔⵔⵜ ⵅⵕⴰ ⵡⵖⴰⴷⵉ ⵏⴼⵔⵎⵓⵀ ⵍⵉⴽ!"
            else:
                return "Chnkhlf nsa3dok 3la mchkilk! 💪\n\nSm7ti lia tqdr tsma3ni chnkhlf mwa tist3jlch 3lik?\n\nWla rassel soualk mrrta khra wghadi nfrmoh lik!"
    
    def handle_closing(self, message: str, lang: str, sender_phone: str) -> str:
        """معالجة نهاية المحادثة بإسلوب مغربي"""
        if lang == 'ar':
            responses = [
                "ⵛⵓⴽⵔⴰⵏ ⵄⵍⵉⴽ! 🙏\n\nⵏⵛⴰⵍⵍⴰⵀ ⵜⴱⵇⴰ ⵍⵉⵎⵜⵉⵀⴰⵏ ⵎⵄⴰ ⵍⴽ! ⵎⴰ ⵜⵙⵎⵄⵛ ⵙⵉ ⵃⴰⵊⴰ ⵎⵏ ⵖⴷⵉ! 🇲🇦\n\nⵎⵄⴰ ⵙⵙⵍⴰⵎⴰ 👋",
                "ⵍⵍⴰⵀ ⵉⵀⴼⴹⵏⵉ ⵡⵉⴰⵍⵉⴽ! 🤲\n\nⵜⵎⴰⵎ ⵏⵛⴰⵍⵍⴰⵀ ⵜⴱⵇⴰ ⵍⵉⵎⵜⵉⵀⴰⵏ! ⵎⴰ ⵜⵙⵎⵄⵛ ⵙⵉ ⵃⴰⵊⴰ ⵏⵖⵢⵢⵎⵓ ⵍⵉⴽ! 💪\n\nⴱⵙⵍⵎⴰ ⵖⴰ ⵜⵎⴰⵎ 👋",
                "ⵛⵓⴽⵔⴰⵏ ⴱⵣⴰⴼ! 😊\n\nⵏⵛⴰⵍⵍⴰⵀ ⵜⴱⵇⴰ ⵍⵉⵎⵜⵉⵀⴰⵏ ⵎⵄⴰ ⵍⴽ! ⵎⴰ ⵜⵙⵎⵄⵛ ⵙⵉ ⵃⴰⵊⴰ ⵏⵖⵢⵢⵎⵓ ⵍⵉⴽ! 🙏\n\nⵎⵄⴰ ⵙⵙⵍⴰⵎⴰ ⵖⴰ ⵜⵎⴰⵎ 👋"
            ]
        else:
            responses = [
                "Chokran bzzaf! 🙏\n\nNchallah tbqa limtihan m3ak! Ma tsma3ch si haja mn ghdi! 🇲🇦\n\nM3a ssalama 👋",
                "Allah yhfedni wialik! 🤲\n\nTamam nchallah tbqa limtihan! Ma tsma3ch si haja nghyyemo lik! 💪\n\nBslama gha tamam 👋",
                "Mrc bcp! 😊\n\nNchallah tbqa limtihan m3ak! Ma tsma3ch si haja nghyyemo lik! 🙏\n\nM3a ssalama gha tamam 👋"
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
                    return "ⵙⵎⵃⵜⵉ ⵎⴰ ⵜⵎⵛⵉⵜⵛ ⵍⵜⵍⴰⴱⴰ! ⵣⵉⴷ ⵎⵔⵔⵜ ⵅⵕⴰ."
                else:
                    return "Sm7ti ma tmchitch tlaba! Zid mrrta khra."
            
            # 2. إنشاء رسالة الإشعار للبائع
            product = order_info.get('product', {})
            quantity = order_info.get('quantity', 1)
            total = order_info.get('total', 0)
            
            notify_text = f"""🚨 *ⵜⵍⴰⴱⴰ ⵎⵥⵉⴷⴰ!*

📞 ⵍⵄⵎⵉⵍ: {sender_phone}
📝 ⵍⵎⵄⵍⵓⵎⴰⵜ ⵍⵎⵇⴷⵎⴰ:
{message}

🛒 *ⵜⴼⵚⵉⵍ ⵍⵜⵍⴰⴱⴰ:*
📦 ⵍⵃⴰⵊⴰ: {product.get('ar', 'ⵎⴰ ⵜⵉⵜⵇⵔⵔⵏⵛ')} / {product.get('fr', 'N/A')}
🔢 ⵍⵇⵜⵉⵢⴰ: {quantity}
💰 ⵍⵎⴳⵎⵓⵄ: {total} ⴷⵔⵀⵎ

⏰ ⵍⵎⵉⵏ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # 3. إرسال الإشعار للبائع
            logger.info(f"🔄 محاولة إرسال إشعار للبائع على الرقم: {SELLER_PHONE_NUMBER}")
            seller_success = send_whatsapp_message(SELLER_PHONE_NUMBER, notify_text)
            
            if seller_success:
                logger.info(f"🎉 تم إرسال إشعار الطلبية بنجاح للبائع من العميل {sender_phone}")
                
                # إرسال تأكيد إضافي للبائع
                confirm_text = f"✅ ⵜⵎ ⵍⵇⴱⴷ ⵜⵍⴰⴱⴰ ⵎⵥⵉⴷⴰ ⵎⵏ {sender_phone} - ⵍⵎⵔⵊⵄ ⵍⵜⵜⵡⴰⵚⵍ ⵎⵄⴰ ⵍⵄⵎⵉⵍ ⵅⵍⴰⵍ 30 ⴷⵔⵉⵇⴰ"
                send_whatsapp_message(SELLER_PHONE_NUMBER, confirm_text)
                
            else:
                logger.error(f"❌ فشل إرسال إشعار الطلبية للبائع من العميل {sender_phone}")
                
                # محاولة بديلة: إرسال رسالة مختصرة
                short_notify = f"🚨 ⵜⵍⴰⴱⴰ ⵎⵥⵉⴷⴰ ⵎⵏ {sender_phone} - ⵍⵃⴰⵊⴰ: {product.get('ar', 'ⵎⴰ ⵜⵉⵜⵇⵔⵔⵏⵛ')} - {total} ⴷⵔⵀⵎ"
                send_whatsapp_message(SELLER_PHONE_NUMBER, short_notify)
            
            # 4. تنظيف الجلسة بعد إرسال الإشعار
            if sender_phone in self.user_sessions:
                del self.user_sessions[sender_phone]
                logger.info(f"🧹 تم تنظيف جلسة المستخدم {sender_phone}")
            
            # 5. الرد على الزبون
            logger.info(f"📨 إرسال تأكيد للزبون {sender_phone}")
            
            if lang == 'ar':
                return f"""✅ ⵜⵎ ⵍⵇⴱⴷ ⵎⵄⵍⵓⵎⴰⵜⴽ ⴱⵏⵊⴰⵃ!

📞 ⵖⴰⴷⵉ ⵢⵡⵙⵍⴰ ⴱⴽ ⴼⵔⵉⵇⴰ ⵏⴰ ⵅⵍⴰⵍ 30 ⴷⵔⵉⵇⴰ ⵍⵜⴰⵢⵉⴽⵉⴷ ⵏⵉⵀⴰⵢⵉ ⵏ ⵍⵜⵍⴰⴱⴰ.

ⵛⵓⴽⵔⴰⵏ ⵄⵍⴰ ⵜⵡⵇⵉⵜⴽ ⴱⵏⴰ! 🤝

{random.choice(self.spontaneous_responses['ar'])}"""
            else:
                return f"""✅ Tm lqbd ma3lomatk bnjah!

📞 Ghadi yweslo bk friqa na khlal 30 driqa ltaykid nihayi n tlaba.

Chokran 3la twqitk bna! 🤝

{random.choice(self.spontaneous_responses['fr'])}"""
            
        except Exception as e:
            logger.error(f"💥 خطأ في معالجة معلومات الاتصال: {str(e)}")
            if lang == 'ar':
                return "ⵙⵎⵃⵜⵉ ⵡⵇⵄ ⵎⵛⴽⵍ ⴼⵉ ⵎⵄⴰⵍⵎⵉⵜ ⵎⵄⵍⵓⵎⴰⵜⴽ. ⵍⵎⵔⵊⵄ ⵊⵔⵔ ⵎⵔⵔⵜ ⵅⵕⴰ ⵡⵍⴰ ⵍⵉⵜⵙⴰⵍ ⴱⵏⴰ ⴱⵛⵉⴽⵀ."
            else:
                return "Sm7ti wq3 mchkil f ma3lmit ma3lomatk. Lmerja3 jerr mrrta khra wla litsal bna bchikh."

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

# بقية الكود (الويب هوك والرواتب) تبقى كما هي مع تحديث الرسائل
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
            'product': session.get('product', {}).get('ar', 'ⵎⴰ ⵜⵉⵜⵇⵔⵔⵏⵛ'),
            'quantity': session.get('quantity', 1),
            'total': session.get('total', 0),
            'waiting_since': session.get('timestamp').strftime('%H:%M:%S') if session.get('timestamp') else 'ⵎⴰ ⵜⵉⵜⵇⵔⵔⵏⵛ'
        })
    
    return jsonify({
        'status': 'ⵎⵔⵜⴰⵀ',
        'service': 'ⵎⵓⵊⵉⴱ ⴱⵓⵜ',
        'version': '🇲🇦 ⵎⵖⵔⴱⵉ 100%',
        'active_sessions_count': len(bot.user_sessions),
        'active_sessions': active_sessions,
        'seller_number': SELLER_PHONE_NUMBER,
        'features': ['ⴼⵀⵎ ⵏⵏⵉⵢⴰ', 'ⵜⵉⴼⵉⵏⴰⵖ', 'ⴷⴰⵔⵉⵊⴰ', 'ⵜⵜⵓⵚⵍⵉⵍ ⵎⴳⵔⴰⵏⵉ'],
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/test-moroccan', methods=['GET'])
def test_moroccan():
    """اختبار الردود المغربية"""
    test_messages = [
        "سلام",
        "بشحال سروال الجينز",
        "واش كتصيفطو ل كازا",
        "عندي مشكل ف القياس",
        "شكرا بزاف"
    ]
    
    results = []
    for msg in test_messages:
        intent = bot.detect_intent(msg)
        lang = bot.detect_language(msg)
        response = bot.process_message(msg, "212600000000")
        results.append({
            'message': msg,
            'intent': intent,
            'language': lang,
            'response_preview': response[:100] + "..."
        })
    
    return jsonify({
        'test_results': results,
        'moroccan_features': ['دارجة', 'تيفيناغ', 'مدن مغربية', 'ردود عفوية']
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"🚀 تشغيل سيرفر ⵎⵓⵊⵉⴱ على المنفذ {port}")
    logger.info(f"📞 رقم البائع: {SELLER_PHONE_NUMBER}")
    logger.info(f"🇲🇦 البوت مغربي 100% - جاهز للخدمة!")
    logger.info(f"🔧 وضع التصحيح: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)