import os
import feedparser
import requests
from google import genai
from datetime import datetime

# Çevre değişkenlerinden anahtarları al
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini istemcisini başlat
client = genai.Client(api_key=GEMINI_API_KEY)

# Takip edilecek RSS kaynakları
RSS_URLS = [
    "https://feeds.bbci.co.uk/turkce/rss.xml",
    "https://tr.sputniknews.com/export/rss2/archive/index.xml"
]

def fetch_news():
    articles = []
    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:2]:
            articles.append({
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "link": entry.link
            })
    return articles

def generate_analysis(article):
    prompt = f"""
    Aşağıdaki haber başlığını ve içeriğini al. Bunu kinik, hafif alaycı, derinlemesine ve analitik bir dille, sıradan insanların göremediği arka plan detaylarını ve en önemli noktaları vererek Türkçe özetle.
    
    Başlık: {article['title']}
    İçerik: {article['summary']}
    
    Özet akıcı ve Telegram'a atılmaya uygun formatta olsun.
    """
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    return response.text

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    try:
        news_list = fetch_news()
        if not news_list:
            print("Haber bulunamadı.")
            send_to_telegram("⚠️ *Derin Bülten Uyarı*\n\nHaber akışı çekilemedi, kaynaklar boş döndü.")
        
        # Günlük kota sınırına takılmamak için her çalıştırmada sadece 1 haber işliyoruz
        for item in news_list[:1]:
            analysis = generate_analysis(item)
            # Tarih ve en önemli detayların yer alacağı mesaj formatı
            simdiki_zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
            message = f"🚨 *Derin Bülten Analizi*\n\n📅 *Tarih:* {simdiki_zaman} (UTC)\n\n{analysis}\n\n🔗 [Habere Git]({item['link']})"
            send_to_telegram(message)
            
        print("Bültenler başarıyla gönderildi!")
        
    except Exception as e:
        error_message = f"❌ *Derin Bülten Kritik Hata*\n\nBot çalışırken bir hata oluştu ve bülten gönderilemedi.\n\n`Hata Detayı: {str(e)}`"
        print(f"Hata oluştu: {e}")
        try:
            send_to_telegram(error_message)
        except Exception as telegram_error:
            print(f"Telegram'a hata mesajı iletilemedi: {telegram_error}")
        
        raise e
      
