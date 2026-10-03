import os
import feedparser
import requests
from google import genai
from google.genai import errors
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Cevre degiskenlerinden API anahtarlarini ve Telegram bilgilerini aliyoruz
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini istemcisini baslatiyoruz
client = genai.Client(api_key=GEMINI_API_KEY)

# GitHub sunucularindan engellenmeyen dunya haberi RSS kaynaklari
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition_world.rss",
    "https://feeds.feedburner.com/ndtvnews-world-news"
]

def send_telegram_message(text):
    """Telegram uzerinden mesaj gonderir ve durumu detaylica loglar."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print(f"Telegram API Yanit Kodu: {response.status_code}")
    print(f"Telegram API Yaniti: {response.text}")
    if response.status_code != 200:
        print(f"HATA: Telegram mesaji gonderilemedi -> {response.text}")

# Gecici sunucu hatalarinda 10 saniye arayla 3 kez otomatik tekrar deneme
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    retry=retry_if_exception_type((errors.ServerError, errors.APIError)),
    reraise=True
)
def generate_analysis_with_retry(prompt):
    """Gemini API cagrisini guncel model ile yapar."""
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    return response.text

def generate_analysis(item_title, item_summary):
    """Haberleri sistemik somuru ve gercekci bir perspektifle analiz eder."""
    prompt = f"""
    Asagidaki haberi; sistemik curumuslugu, elitlerin ve kuresel odaklarin cikarlarini, ekonomik somuruyu ve perde arkasindaki gercekleri goz onune alarak; son derece alayci, tavizsiz, acimasizca gercekci ve analitik bir dille Turkce olarak analiz et ve ozetle.
    
    Baslik: {item_title}
    Ozet: {item_summary}
    """
    try:
        return generate_analysis_with_retry(prompt)
    except Exception as e:
        print(f"Gemini API hatasi: {e}")
        return None

def main():
    print("Derin Bulten botu calistiriliyor...")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("HATA: Telegram Token veya Chat ID eksik!")
        return

    # RSS akislarindan veri cekmeyi deniyoruz
    feed = None
    for url in RSS_FEEDS:
        print(f"RSS deneniyor: {url}")
        parsed_feed = feedparser.parse(url)
        if parsed_feed.entries:
            feed = parsed_feed
            print(f"Basariyla veri alindi: {url}")
            break

    if feed and feed.entries:
        entry = feed.entries[0]
        title = entry.get("title", "Baslik Yok")
        summary = entry.get("summary", "Ozet yok")
        
        print(f"Islenen haber: {title}")
        
        analysis = generate_analysis(title, summary)
        if analysis:
            message = f"🚨 *Derin Analitik Bulten*\n\n{analysis}"
            send_telegram_message(message)
            print("Surec basariyla tamamlandi.")
        else:
            print("Analiz uretilemedi.")
    else:
        print("HATA: Hicbir RSS kaynakindan veri alinamadi.")

if __name__ == "__main__":
    main()
  
