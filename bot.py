import os
import requests
import feedparser
from google import genai

# Ortam değişkenlerinden gizli anahtarları ve bilgileri çekiyoruz
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# RSS Kaynağı
RSS_URL = "https://www.trthaber.com/sondakika.rss"

def ai_analiz_uret(haber_basligi, haber_ozeti, haber_tarihi):
    if not GEMINI_API_KEY:
        return "API anahtarı bulunamadı, analiz üretilemedi."
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Sen gerçekçi, acımasız gerçekleri doğrudan söyleyen, dost gibi konuşan bir analistsin. Yapay zeka gibi değil, bir insan gibi konuş.
    Aşağıdaki haberi incele ve şu formatta çıktı ver:
    
    🚨 GÜNDEM: {haber_basligi}
    🕒 Tarih / Saat: {haber_tarihi}
    📝 Özet: {haber_ozeti}
    
    🔎 SİSTEMİK VE JEOPOLİTİK DERİN ANALİZ:
    • Kök Neden & Küresel Boyut: (Bu habere özel olarak arkasındaki enerji koridorları, sermaye hegemonyası veya güç savaşlarını yaz)
    • Ekonomik Çöküş & Halkın Durumu: (Faturanın dar gelirliye ve halka nasıl kesildiğini yaz)
    • Siyasi ve Toplumsal Yansımalar: (Siyasi tiyatroları ve sistemik çürümüyü yaz)
    
    **Dost Gözüyle / Kendi Düşüncem:** 
    (Burada tamamen dost gibi konuş, olayın kemiğini, perde arkasındaki pislikleri ve asıl gerçeği sert bir dille özetle, asla kısaltma yapma, hakkını ver.)
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

def telegrama_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    feed = feedparser.parse(RSS_URL)
    if feed.entries:
        entry = feed.entries[0]
        baslik = entry.title
        ozet = entry.summary if hasattr(entry, 'summary') else ""
        # Haberin yayınlanma tarihini alıyoruz (yoksa belirtilmedi de geçebilir)
        tarih = entry.published if hasattr(entry, 'published') else "Tarih belirtilmemiş"
        
        # Yapay zekaya tarihle birlikte gönderiyoruz
        analizli_bulten = ai_analiz_uret(baslik, ozet, tarih)
        
        # Telegram'a basıyoruz
        telegrama_gonder(analizli_bulten)

if __name__ == "__main__":
    main()
  
