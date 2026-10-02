import requests
import datetime
import xml.etree.ElementTree as ET
from gtts import gTTS
import os

TOKEN = "8904852019:AAGkUH1_vE9C5Do1p0w92wEW89ed34pkMps"
CHAT_ID = "5813100849"

simdi = datetime.datetime.now().strftime("%d.%m.%Y - %H:%M")

def veri_tara():
    url = "https://www.trthaber.com/sondakika.rss"
    basliklar = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:5]:
                basliklar.append(item.find('title').text)
    except:
        basliklar.append("Gündem akışı otonom tarama modunda işleniyor.")
    return basliklar

def rapor_olustur(haberler):
    haber_metni = "\n".join([f"• {h}" for h in haberler])
    
    tam_rapor = f"""
KÜRESEL OTONOM HERŞEYİ BİLME MOTORU - SESLİ ANALİZ RAPORU. 
Zaman Dilimi: {simdi}.

1. Saha Gündemi ve Çatışmaların Arka Planı:
Dünya genelinde patlak veren çatışmalar ve krizler anlık değildir; kökleri emperyalist paylaşım mücadelelerine dayanır. Sahadaki yansımalar:
{haber_metni}

2. Piyasalar, Finans ve Hisseler:
Küresel sermaye piyasalarındaki dalgalanmalar, paranın ve emtianın akış yönü krizlerin kimin için fırsat olduğunu açıkça gösteriyor.

3. Yapay Zeka ve Çin'in Yükselişi:
Çin'in yapay zeka alanındaki baş döndürücü hızı, teknoloji dünyasındaki çip savaşları ve algoritmik üstünlük yarışını kızıştırıyor.

4. Bilim ve Uzayın Derinlikleri:
NASA'nın uzayda bulduğu sıra dışı keşifler, insanın evrendeki yerini ve dünyadaki yapay kavgaların geçiciliğini yüzümüze vuruyor.

5. Tarihsel Perspektif:
Hiçbir şey gizli kalmaz. Bu bülten, her şeyden haberdar olman için sansürsüz olarak hazırlanmıştır.
"""
    return tam_rapor

def sese_cevir_ve_gonder(metin):
    # Metni ses dosyasına çeviriyoruz
    tts = gTTS(text=metin, lang='tr', slow=False)
    ses_dosyasi = "bulten.mp3"
    tts.save(ses_dosyasi)
    
    # Telegram'a ses dosyası olarak fırlatıyoruz
    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
    with open(ses_dosyasi, "rb") as audio:
        files = {"audio": audio}
        data = {
            "chat_id": CHAT_ID,
            "caption": f"🎧 **Otonom Sesli Bülten** - {simdi}"
        }
        response = requests.post(url, data=data, files=files)
        
    if response.status_code == 200:
        print("Sesli rapor başarıyla fırlatıldı.")
    else:
        print(f"Hata: {response.text}")

if __name__ == "__main__":
    veriler = veri_tara()
    rapor = rapor_olustur(veriler)
    sese_cevir_ve_gonder(rapor)
