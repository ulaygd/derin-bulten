import os
import feedparser
import requests
from google import genai

# Çevre değişkenlerinden anahtarları al
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini istemcisini başlat
client = genai.Client(api_key=GEMINI_API_KEY)

# Takip edilecek RSS kaynakları (istediğin gibi çoğaltabilirsin)
RSS_URLS = [
    "https://feeds.bbci.co.uk/turkce/rss.xml",
    "https://tr.sputniknews.com/export/rss2/archive/index.xml"
]

def fetch_news():
    articles = []
    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]: # Her kaynaktan son 3 haber
            articles.append({
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "link": entry.link
            })
    return articles

def generate_analysis(article):
    prompt = f"""
    Aşağıdaki haber başlığını ve içeriğini al. Bunu kinik, hafif alaycı, derinlemesine ve analitik bir dille, sıradan insanların göremediği arka plan detaylarını vererek Türkçe özetle.
    
    Başlık: {article['title']}
    İçerik: {article['summary']}
    
    Özet akıcı ve Telegram'a atılmaya uygun formatta olsun.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
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
    news_list = fetch_news()
    if not news_list:
        print("Haber bulunamadı.")
    
    for item in news_list[:2]: # Şimdilik ilk 2 haberi işlesin
        analysis = generate_analysis(item)
        message = f"🚨 *Derin Bülten Analizi*\n\n{analysis}\n\n🔗 [Habere Git]({item['link']})"
        send_to_telegram(message)
    print("Bültenler başarıyla gönderildi!")
  
