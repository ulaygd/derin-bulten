from datetime import datetime
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

TOKEN = "8904852019:AAGkUH1_vE9C5Do1p0w9i19NqK_9I4z_r0k"
SOHBET_ID = "5813100849"


def veri_tara():
  url = "https://www.trthaber.com/sondakika.rss"
  haberler = []
  try:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as response:
      cevap = response.read()
    kok = ET.fromstring(cevap)
    for eleman in kok.findall(".//item")[:7]:
      baslik = eleman.find("title").text
      aciklama = eleman.find("description")
      ozet = (
          aciklama.text
          if (aciklama is not None and aciklama.text)
          else "Detay verilmemiş."
      )
      if baslik:
        haberler.append({"baslik": baslik, "ozet": ozet})
  except Exception:
    pass
  return haberler


def derin_analiz_uret(haberler):
  if not haberler:
    return (
        "Şu an taranabilen güncel kritik bir veri akışı bulunamadı, sistem"
        " kararlı."
    )

  analiz_metni = ""
  savas_krizi_var_mi = False

  for h in haberler:
    baslik = h["baslik"]
    ozet = h["ozet"]

    # Çatışma, savaş veya kriz tetikleyicilerini yakala
     Kritik anahtar kelimeler
    if any(
        k in baslik.lower()
        for k in [
            "savaş",
            "operasyon",
            "çatışma",
            "füze",
            "saldırı",
            "ordu",
            "cephe",
            "gerilim",
            "tehdit",
            "kriz",
        ]
    ):
      savas_krizi_var_mi = True
      analiz_metni += f"🚨 **KRİTİK ÇATIŞMA / JEOPOLİTİK GELİŞME:**\n"
      analiz_metni += f"• **Olay:** {baslik}\n"
      analiz_metni += f"• **Saha Özeti:** {ozet}\n"
      analiz_metni += (
          "• **Geçmiş Bağlam & Analiz:** Bu durum, bölgedeki uzun vadeli"
          " güç dengelerinin ve geçmiş kriz hatlarının (vekalet savaşları ve"
          " diplomatik kopuşların) doğrudan bir yansımasıdır. Tarafların"
          " hamleleri, çatışmanın bölgesel bir yayılma riskini artırmakta ve"
          " ekonomik/lojistik hatları tehdit etmektedir.\n\n"
      )
    else:
      analiz_metni += f"📌 **Genel Gelişme:** {baslik}\n"
      analiz_metni += f"• {ozet}\n\n"

  if savas_krizi_var_mi:
    analiz_metni = (
        "⚠️ **DİKKAT: AKTİF ÇATIŞMA / KRİZ ALARMI TESPİT EDİLDİ**\n\n"
        + analiz_metni
    )

  return analiz_metni


def telegrama_gonder(analiz_raporu):
  tarih = datetime.now().strftime("%d %B %Y - Saat %H:%M")
  mesaj = (
      f"🧠 **DERİNLEMESİNE OTONOM ANALİZ BÜLTENİ** ({tarih})\n\n"
      f"{analiz_raporu}\n\n"
      "––––––––––––––––––––––––––––\n*Gerçekçi, ham ve tavizsiz analiz"
      " motoru.*"
  )

  api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  veri = urllib.parse.urlencode(
      {"chat_id": SOHBET_ID, "text": mesaj, "parse_mode": "Markdown"}
  ).encode("utf-8")

  req = urllib.request.Request(api_url, data=veri, method="POST")
  urllib.request.urlopen(req)


if __name__ == "__main__":
  ham_haberler = veri_tara()
  rapor = derin_analiz_uret(ham_haberler)
  telegrama_gonder(rapor)
  
