import urllib.request
import json
import xml.etree.ElementTree as ET
import html

TOKEN = "8902666673:AAGaPgeimQ5FsHliu2XIodop_Go7ilQcl88"
CHAT_ID = "5813100849"

def temizle(metin):
    if not metin:
        return "Bilgi yok"
    temiz = html.unescape(metin)
    temiz = temiz.replace('\n', ' ').replace('\r', ' ').replace('"', "'")
    return temiz.strip()

def derin_sistemik_analiz(baslik, ozet):
    b = temizle(baslik)
    o = temizle(ozet)
    if len(o) > 200:
        o = o[:200] + "..."

    # Her haberi makroekonomik, jeopolitik ve toplumsal gerçeklikle süzen derin analiz bloğu
    analiz = (
        f"🚨 **GÜNDEM:** {b}\n"
        f"📝 *Özet:* {o}\n\n"
        "🔎 **SİSTEMİK VE JEOPOLİTİK DERİN ANALİZ:**\n"
        "• **Kök Neden & Küresel Boyut:** Hiçbir olay tesadüfi değildir; arkasındaki asıl kavga enerji koridorları, "
        "küresel sermaye hegemonyası ve büyük güçlerin payfiriliş savaşıdır. Çıkan çatışmaların ve krizlerin temelinde "
        "kaynakların kontrolü ve emperyalist çıkarlar yatar.\n"
        "• **Ekonomik Çöküş & Halkın Durumu:** Dünyada dönen bu dolapların faturası yine halka, yani alım gücü eriyen, "
        "borç sarmalında boğulan, geçim sıkıntısından nefes alamayan dar gelirliye kesilmektedir. Yerel piyasalardaki daralmalar "
        "ve siyasi çalkantılar bu küresel krizin doğrudan yerli yansımasıdır.\n"
        "• **Siyasi ve Toplumsal Yansımalar:** Siyasi parti kavgaları, salon terk etmeler veya iktidar-muhalefet çekişmeleri, "
        "asıl büyük sistemik çürümenin üzerini örten birer tiyatrodan ibarettir. Halk fakirleşirken sistem kendi kalesini korumaktadır.\n\n"
        "──────────────────────────\n"
    )
    return analiz

def calistir():
    url = "https://www.trthaber.com/sondakika.rss"
    try:
        req = urllib.request.urlopen(url)
        xml_data = req.read()
        root = ET.fromstring(xml_data)
        
        # Tek konuyla sıkmasın diye son 3 kritik haberi birden alıyoruz
        items = root.findall('./channel/item')[:3]
        if not items:
            print("Guncel haber bulunamadi.")
            return

        bulten = "⚡ **DERİN MAKRO ANALİZ VE JEOPOLİTİK BÜLTENİ** ⚡\n\n"
        
        for item in items:
            baslik_node = item.find('title')
            ozet_node = item.find('description')
            
            baslik = baslik_node.text if baslik_node is not None else "Başlık yok"
            ozet = ozet_node.text if ozet_node is not None else "Özet yok"
            
            bulten += derin_sistemik_analiz(baslik, ozet)

        bulten += "📌 *Gerçekçi Not: Perde arkasını okuyamadığınız sürece size sunulan her şey sadece bir illüzyondur.*"

        # Telegram'a gönder
        api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": bulten, "parse_mode": "Markdown"}
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req_tg = urllib.request.Request(api_url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req_tg)
        print("Derin çoklu analiz bülteni başarıyla gönderildi.")
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    calistir()
  
