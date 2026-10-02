import requests
import datetime

# Telegram Bot Bilgileri
TOKEN = "8904852019:AAGkUH1_vE9C5Do1p0w92wEW89ed34pkMps"
CHAT_ID = "5813100849"

bugun = datetime.datetime.now().strftime("%d.%m.%Y")

# Derin Analiz Metni (Jeopolitik, NATO, Türkiye'nin Borç Sarmalı ve Gerçekler)
bulten_metni = f"""
🧠 **DERİN ANALİZ BÜLTENİ — {bugun}** 🧠

**1. Jeopolitik ve NATO Satranç Tahtası:**
Küresel güç dengeleri kırılma noktasında. NATO'nun genişleme hamleleri ve Doğu blokunun sert karşılıkları, vekalet savaşlarını doğrudan nükleer eşiğe taşıyor. Masada barış konuşulurken sahnede tamamen enerji koridorları, nadir toprak elementleri ve tedarik zincirlerinin kontrolü için kanlı bir pazarlık dönüyor. Hiçbir ittifak masum değil; her devlet kendi çıkarının kurbanı veya celladı.

**2. Türkiye'nin Ekonomik Borç Sarmalı:**
Türkiye'nin içinde bulunduğu ekonomik sıkışmışlık, sadece kur dalgalanmaları veya enflasyon rakamlarından ibaret değil. Yapısal üretim kısıtları, dış borç servisinin getirdiği devasa yük ve liyakatsizliğin yarattığı kaynak israfı, ülkeyi orta gelir tuzağının çok ötesine, kalıcı bir ekonomik dar boğaza sürüklüyor. Çarklar dönerken faturayı ödeyen yine geleceği çalınan genç nesil oluyor.

**3. Gençliğin Omuzundaki Yük ve Varoluşsal Sıkışmışlık:**
Bugünün gençleri; pasaport kuyruklarında, mülakat eşitsizliklerinde ve geleceksizlik psikolojisinde nefes almaya çalışıyor. Sistem, düşünen, sorgulayan ve üreten beyinleri ülkenin dışına iterken içeride sessiz bir ruhsal çöküntü yaratıyor. Bu sadece ekonomik değil, aynı zamanda varoluşsal bir krizdir.

**4. Tarihsel ve Fevri Perspektif:**
Tarih, teerrürden ibarettir çünkü akıllanmayan insan toplulukları aynı hataları tekrarlar. Roma'nın çöküşünden Osmanlı'nın son dönemindeki mali kapitülasyonlara kadar her büyük imparatorluğun düşüş reçetesi aynıdır: Üretmeden tüketmek, hukuku esnetmek ve adaleti yok etmek.

*Bu analiz tamamen otonom bir motor tarafından hiçbir filtre uygulanmadan üretilmiştir.*
"""

def telegrama_gonder(metin):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": metin,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Bülten başarıyla fırlatıldı.")
    else:
        print(f"Hata oluştu: {response.text}")

if __name__ == "__main__":
    telegrama_gonder(bulten_metni)
  
