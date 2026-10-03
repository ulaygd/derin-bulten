import os
import feedparser
import requests
from google import genai
from google.genai import errors
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Çevre değişkenlerinden API anahtarlarını ve Telegram bilgilerini alıyoruz
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini istemcisini başlatıyoruz
client = genai.Client(api_key=GEMINI_API_KEY)

# GitHub sunucularından engellenmeyen, kararlı dünya haberi RSS kaynakları
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition_world.rss",
    "https://feeds.feedburner.com/ndtvnews-world-news"
]

def send_telegram_message(text):
    """Telegram üzerinden mesaj gönderir ve durumu detaylıca loglar."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print(f"Telegram API Yanıt Kodu: {response.status_code}")
    print(f"Telegram API Yanıtı: {response.text}")
    if response.status_code != 200:
        print(f"HATA: Telegram mesajı gönderilemedi -> {response.text}")

# 503 veya geçici sunucu hatalarında 10 saniye arayla 3 kez otomatik tekrar deneme
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    retry=retry_if_exception_type((errors.ServerError, errors.APIError)),
    reraise=True
)
def generate_analysis_with_retry(prompt):
    """Gemini API çağrısını güncel kütüphane standardıyla yapar."""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

def generate_analysis(item_title, item_summary):
    """Haberleri sistemik sömürü, elitlerin çıkarları ve gerçekçi bir perspektifle analiz eder."""
    prompt = f"""
    Aşağıdaki haberi; sistemik çürümüşlüğü, elitlerin ve küresel odakların çıkarlarını, ekonomik sömürüyü ve perde arkasındaki gerçekleri göz önüne alarak; son derece alaycı, tavizsiz, acımasızca gerçekçi ve analitik bir dille Türkçe olarak analiz et ve özetle.
    
    Başlık: {item_title}
    Özet: {item_summary}
    """
    try:
        return generate_analysis_with_retry(prompt)
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        return None

def main():
    print("Derin Bülten botu çalıştırılıyor...")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("HATA: Telegram Token veya Chat ID eksik!")
        return

    # RSS akışlarından veri çekmeyi deniyoruz
    feed = None
    for url in RSS_FEEDS:
        print(f"RSS deneniyor: {url}")
        parsed_feed = feedparser.parse(url)
        if parsed_feed.entries:
            feed = parsed_feed
            print(f"Başarıyla veri alındı: {url}")
            break

    if feed and feed.entries:
        entry = feed.entries[0]
        title = entry.get("title", "Başlık Yok")
        summary = entry.get("summary", "Özet yok")
        
        print(f"İşlenen haber: {title}")
        
        analysis = generate_analysis(title, summary)
        if analysis:
            message = f"🚨 *Derin Analitik Bülten*\n\n{analysis}"
            send_telegram_message(message)
            print("Süreç başarıyla tamamlandı.")
        else:
            print("Analiz üretilemedi.")
    else:
        print("HATA: Hiçbir RSS kaynağından veri alınamadı.")

if __name__ == "__main__":
    main()
  
