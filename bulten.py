from datetime import datetime
import xml.etree.ElementTree as ET
from gTTS import gTTS
import requests

TOKEN = "8904852019:AAGkUH1_vE9C5Do1p0w9i19NqK_9I4z_r0k"
SOHBET_ID = "5813100849"


def veri_tara():
  url = "https://www.trthaber.com/sondakika.rss"
  basliklar = []
  try:
    cevap = requests.get(url)
    kok = ET.fromstring(cevap.content)
    for eleman in kok.findall(".//item")[:5]:
      baslik = eleman.find("title").text
      basliklar.append(baslik)
  except Exception as e:
    basliklar.append("Haber çekilemedi.")
  return ". ".join(basliklar)


def ses_yap(metin):
  tarih = datetime.now().strftime("%d %B %Y - Saat %H:%00")
  tam_metin = (
      f"Merhaba! {tarih} itibarıyla güncel son dakika haberleri şöyle:"
      f" {metin}"
  )
  tts = gTTS(text=tam_metin, lang="tr")
  tts.save("bulten.mp3")


def telegrama_gonder():
  url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
  with open("bulten.mp3", "rb") as ses_dosyasi:
    dosyalar = {"audio": ses_dosyasi}
    veriler = {
        "chat_id": SOHBET_ID,
        "caption": "🎙️ Saatlik Otomatik Otonom Bültenin Hazır!",
    }
    requests.post(url, data=veriler, files=dosyalar)


if __name__ == "__main__":
  haberler = veri_tara()
  ses_yap(haberler)
  telegrama_gonder()
  
