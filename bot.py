import os
import feedparser
import requests
from google import genai
from google.genai import errors
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Çevre değişkenlerinden API anahtarlarını alıyoruz
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini istemcisini başlatıyoruz
client = genai.Client(api_key=GEMINI_API_KEY)

# RSS Kaynakları (Jeopolitik ve ekonomik odaklı)
RSS_FEEDS = [
    "https://www.reuters.com/arc/outboundfeeds/rss/?outputType=xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml"
]

def send_telegram_message(text):
    """Telegram üzerinden mesaj gönderir."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Telegram mesajı gönderilemedi: {response.text}")

# 503 veya geçici sunucu hatalarında 10 saniye arayla 3 kez tekrar deneme mekanizması
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    retry=retry_if_exception_type((errors.ServerError, errors.APIError)),
    reraise=True
)
def generate_analysis_with_retry(prompt):
    """Gemini API çağrısını hata durumunda yinelenecek şekilde yapar."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def generate_analysis(item_title, item_summary):
    """Haber için alaycı, analitik ve sistem eleştirisi içeren özet üretir."""
    prompt = f"""
    Aşağıdaki haberi; sistemik yolsuzluklar, elitlerin çıkarları ve ekonomik sömürü lensinden bakarak, alaycı, son derece analitik ve gerçekçi bir dille Türkçe olarak özetle.
    
    Başlık: {item_title}
    Özet: {item_summary}
    """
    try:
        return generate_analysis_with_retry(prompt)
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        return None

def main():
    print("Bot çalıştırılıyor...")
    
    # Şimdilik ilk beslemeden örnek bir haber çekelim
    feed = feedparser.parse(RSS_FEEDS[0])
    if feed.entries:
        entry = feed.entries[0]
        title = entry.get("title", "Başlık Yok")
        summary = entry.get("summary", "Özet yok")
        
        print(f"İşlenen haber: {title}")
        
        analysis = generate_analysis(title, summary)
        if analysis:
            message = f"🚨 *Analitik Bülten*\n\n{analysis}"
            send_telegram_message(message)
            print("Mesaj başarıyla Telegram'a gönderildi.")
        else:
            print("Analiz üretilemediği için mesaj gönderilmedi.")
    else:
        print("RSS akışından haber alınamadı.")

if __name__ == "__main__":
    main()
  
