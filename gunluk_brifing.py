#!/usr/bin/env python3
"""
News briefing -> Telegram (text + voice).
Needs 3 secrets: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY
(set them in GitHub: Settings > Secrets and variables > Actions).
"""

import asyncio
import html
import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

# ---------------- AYARLAR ----------------
TR = timezone(timedelta(hours=3))  # Türkiye saati

KATEGORILER = {
    "Türkiye Gündemi": [
        "https://www.aa.com.tr/tr/rss/default?cat=guncel",
        "https://www.trthaber.com/gundem_articles.rss",
        "https://www.ntv.com.tr/turkiye.rss",
    ],
    "Türk Ekonomisi": [
        "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
        "https://www.trthaber.com/ekonomi_articles.rss",
        "https://www.ntv.com.tr/ekonomi.rss",
        "https://www.bloomberght.com/rss",
    ],
    "Türk Gençliği ve Eğitim": [
        "https://www.aa.com.tr/tr/rss/default?cat=egitim",
        "https://www.ntv.com.tr/egitim.rss",
        "https://www.trthaber.com/egitim_articles.rss",
    ],
    "Dünya Finansı": [
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    ],
    "Dünya ve Savaşlar": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.aa.com.tr/tr/rss/default?cat=dunya",
    ],
    "Fizik ve Bilim": [
        "https://www.sciencedaily.com/rss/matter_energy/physics.xml",
        "https://phys.org/rss-feed/physics-news/",
        "https://www.quantamagazine.org/feed/",
    ],
    "Yapay Zeka": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://venturebeat.com/category/ai/feed/",
        "https://openai.com/news/rss.xml",
    ],
}

# Bu konular Google Haberler'de ayrıca aranır ve brifingde mutlaka ele alınır
# ("İran'la savaş var mı, neden başladı?" gibi sorulara cevap verir). İstediğinizi ekleyin/çıkarın.
TAKIP_KONULARI = [
    "İran",
    "İsrail Gazze",
    "Rusya Ukrayna",
    "Merkez Bankası faiz dolar",
    "Türkiye genç işsizliği üniversite",
]

KATEGORI_BASINA_MAX = 10      # kategori başına en fazla haber
TAKIP_BASINA_MAX = 6          # takip konusu başına en fazla haber
ILK_BRIFING_SAATI = 8         # günün ilk brifingi (Türkiye saati); gece boyunca biriken haberleri kapsar
ILK_PENCERE_SAAT = 14         # ilk brifingte kaç saat geriye bakılsın
NORMAL_PENCERE_SAAT = 5       # diğer brifinglerde kaç saat geriye bakılsın
# Sırayla denenir; model yoksa (404) ya da limit dolduysa (429) sıradakine geçilir.
# Özel model için GEMINI_MODEL ortam değişkeni verebilirsiniz.
VARSAYILAN_MODELLER = ["gemini-3.8-flash", "gemini-3.7-flash",
                       "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
SES = "tr-TR-AhmetNeural"     # kadın sesi için: tr-TR-EmelNeural
GORULENLER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gorulenler.json")
# -----------------------------------------

ATOM = "{http://www.w3.org/2005/Atom}"
UA = {"User-Agent": "Mozilla/5.0 (Brifing-Bot)"}
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def env_yukle():
    """Aynı klasördeki .env dosyasını okur (ek kurulum gerekmez)."""
    yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(yol):
        return
    with open(yol, encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if satir and not satir.startswith("#") and "=" in satir:
                k, v = satir.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if v:
                    os.environ.setdefault(k.strip(), v)


def temizle(m, n=300):
    m = re.sub(r"<[^>]+>", " ", m or "")
    m = html.unescape(re.sub(r"\s+", " ", m)).strip()
    return m[:n]


def tarih_coz(m):
    if not m:
        return None
    try:
        d = parsedate_to_datetime(m)
    except Exception:
        try:
            d = datetime.fromisoformat(m.replace("Z", "+00:00"))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def feed_oku(url):
    out = []
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        kok = ET.fromstring(r.content)
    except Exception as e:
        print(f"[uyarı] {url[:70]}: {e}", file=sys.stderr)
        return out
    varsayilan = url.split("/")[2].replace("www.", "")
    for o in kok.iter("item"):
        kaynak = temizle(o.findtext("source"), 40) or varsayilan
        out.append({"baslik": temizle(o.findtext("title"), 170),
                    "link": (o.findtext("link") or "").strip(),
                    "ozet": temizle(o.findtext("description")),
                    "tarih": tarih_coz(o.findtext("pubDate")), "kaynak": kaynak})
    for o in kok.iter(ATOM + "entry"):
        l = o.find(ATOM + "link")
        out.append({"baslik": temizle(o.findtext(ATOM + "title"), 170),
                    "link": l.get("href") if l is not None else "",
                    "ozet": temizle(o.findtext(ATOM + "summary")),
                    "tarih": tarih_coz(o.findtext(ATOM + "updated") or o.findtext(ATOM + "published")),
                    "kaynak": varsayilan})
    return out


def google_haber_url(konu):
    q = urllib.parse.quote(f"{konu} when:1d")
    return f"https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr"


def gorulenleri_yukle():
    try:
        with open(GORULENLER, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def haberleri_topla(simdi):
    saat = int(os.environ.get("SON_SAAT", 0)) or (
        ILK_PENCERE_SAAT if simdi.hour <= ILK_BRIFING_SAATI else NORMAL_PENCERE_SAAT)
    sinir = datetime.now(timezone.utc) - timedelta(hours=saat)
    gorulen = gorulenleri_yukle()
    goruldu_baslik = set()
    sonuc = {}

    def filtrele(liste, maks):
        liste = [h for h in liste if h["link"] and h["link"] not in gorulen
                 and (h["tarih"] is None or h["tarih"] >= sinir)]
        liste.sort(key=lambda h: h["tarih"] or datetime.min.replace(tzinfo=timezone.utc),
                   reverse=True)
        secilen = []
        for h in liste:
            anahtar = re.sub(r"\W+", "", h["baslik"].lower())[:50]
            if anahtar and anahtar not in goruldu_baslik:
                goruldu_baslik.add(anahtar)
                secilen.append(h)
            if len(secilen) >= maks:
                break
        return secilen

    for kategori, urller in KATEGORILER.items():
        liste = []
        for u in urller:
            liste.extend(feed_oku(u))
        sonuc[kategori] = filtrele(liste, KATEGORI_BASINA_MAX)

    for konu in TAKIP_KONULARI:
        sonuc[f"TAKİP: {konu}"] = filtrele(feed_oku(google_haber_url(konu)), TAKIP_BASINA_MAX)
    return sonuc, gorulen


def tarih_str(d):
    return d.astimezone(TR).strftime("%d.%m %H:%M") if d else "tarih yok"


def baslik_tarih(simdi):
    return f"{simdi.day} {AYLAR[simdi.month - 1]} {simdi.year} {GUNLER[simdi.weekday()]}, {simdi:%H:%M}"


SISTEM = (
    "Sen kullanıcının samimi ama dürüst haber arkadaşısın. Türkçe konuş, sıcak ve sade ol, "
    "'sen' diye hitap et; ama asla süsleme ya da gereksiz korkutma yapma, iyi haberi de kötü "
    "haberi de olduğu gibi söyle. Kurallar:\n"
    "1) Güncel olaylar için SADECE sana verilen haber listesine (ve varsa arama sonuçlarına) dayan; "
    "listede olmayan olay, rakam, tarih ya da alıntı uydurma.\n"
    "2) Arka plan anlatırken (neden başladı, taraflar, dönüm noktaları) kendi bilgini kullanabilirsin; "
    "emin olmadığın yerde 'tam emin değilim' de ve bilgin güncel olmayabilir diye belirt.\n"
    "3) Gerçeği yorumdan ayır. Yorumlarını 'Yorumum:' ile başlat.\n"
    "4) Kaynaklar çelişiyorsa söyle. Tek kaynağa dayanan iddiayı 'X kaynağına göre' diye aktar.\n"
    "5) Savaş ve çatışmalarda taraf tutma; iddiaları kimin öne sürdüğünü belirt. Doğrulanamayan "
    "kayıp/zarar rakamlarını kesin bilgi gibi değil iddia olarak sun.\n"
    "6) Her haberin yanına tarihini yaz (listede verilen tarih/saat)."
)


def istek_olustur(haberler, simdi):
    bolumler = []
    for kat, liste in haberler.items():
        if not liste:
            continue
        satirlar = [f"## {kat}"]
        for h in liste:
            satirlar.append(f"- [{tarih_str(h['tarih'])} | {h['kaynak']}] {h['baslik']}\n"
                            f"  {h['ozet']}\n  {h['link']}")
        bolumler.append("\n".join(satirlar))
    if not bolumler:
        return None
    takip = ", ".join(TAKIP_KONULARI)
    return (
        f"Şu an: {baslik_tarih(simdi)} (Türkiye saati). Aşağıdaki YENİ haberlerden brifing hazırla.\n"
        "Çıktıyı iki bölüm olarak ver:\n\n"
        "===METIN===\n"
        "Önce 'Kısaca' başlığıyla en önemli 4-5 maddeyi yaz. Sonra her konu başlığı için:\n"
        "- Gelişmeler: her haber tarih/saatiyle, 1-2 cümle, altında link.\n"
        "- Arka plan: büyük ve süregelen hikayeler için (savaş, kriz, büyük ekonomik gelişme) "
        "bu neden oldu, nasıl başladı, kimler taraf, şu ana kadar ne yaşandı: ayrıntılı ama anlaşılır anlat.\n"
        "- Yorumum: 2-4 cümle analiz (bu neden önemli, bana/Türkiye'ye/gençlere etkisi).\n"
        "- Emin olmadıklarım: belirsiz ya da doğrulanamayan noktalar varsa yaz.\n"
        f"Takip konuları ({takip}) için ayrı bir 'Takip Konuları' bölümü ekle ve her biri için açıkça "
        "'şu an durum ne?' sorusunu cevapla (örneğin bir savaş veya çatışma varsa: var mı, neden "
        "başladı, taraflar kim, son durum ne). Haberlerde o konuyla ilgili yeni gelişme yoksa bunu "
        "açıkça söyle.\n"
        "Konu bölümlerinden haber gelmeyenleri atla.\n\n"
        "===SES===\n"
        "Aynı brifingin dostça konuşma metni: yaklaşık 800-1100 kelime, akıcı konuşma dili, "
        "link/madde işareti/markdown yok. 'Merhaba' ile başla, tarih ve saati söyle, en önemli konuları "
        "arka planıyla anlat, kısa bir kapanışla bitir.\n\n"
        "HABERLER:\n\n" + "\n\n".join(bolumler)
    )


def yz_analiz(istek):
    ozel = os.environ.get("GEMINI_MODEL")
    modeller = [ozel] if ozel else VARSAYILAN_MODELLER
    arama = os.environ.get("GEMINI_ARAMA", "1") == "1"  # Google Arama ile güncel bilgi

    temel = {
        "systemInstruction": {"parts": [{"text": SISTEM}]},
        "contents": [{"role": "user", "parts": [{"text": istek}]}],
        "generationConfig": {"maxOutputTokens": 16000, "temperature": 0.6},
    }
    arama_ile = json.loads(json.dumps(temel))
    arama_ile["tools"] = [{"google_search": {}}]
    # Önce Google Arama'lı ayar; 400 hatası verirse sade ayar
    denemeler = [arama_ile, temel] if arama else [temel]
    basliklar = {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "content-type": "application/json"}

    r = None
    for model in modeller:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for govde in denemeler:
            for bekle in (0, 20):  # limit/yoğunluk (429, 500, 503) olursa 1 kez bekleyip tekrar dene
                if bekle:
                    time.sleep(bekle)
                r = requests.post(url, headers=basliklar, json=govde, timeout=240)
                if r.status_code not in (429, 500, 503):
                    break
            if r.status_code != 400:  # sadece 400'de başka ayar denenir
                break
            print(f"[uyarı] {model} ayar hatası 400: {r.text[:150]}", file=sys.stderr)
        if r.ok:
            print(f"[bilgi] Kullanılan model: {model}")
            break
        print(f"[uyarı] {model} -> {r.status_code}: {r.text[:200]}", file=sys.stderr)
    r.raise_for_status()

    adaylar = r.json().get("candidates") or []
    if not adaylar:
        raise RuntimeError(f"Yapay zeka yanıt vermedi: {r.text[:300]}")
    metin = "".join(p.get("text", "") for p in adaylar[0]["content"]["parts"])
    m = re.search(r"===METIN===(.*?)===SES===(.*)", metin, re.S)
    if m:
        yazi, ses = m.group(1).strip(), m.group(2).strip()
    else:
        yazi, ses = metin.strip(), re.sub(r"https?://\S+", "", metin)
    ses = re.sub(r"https?://\S+", "", re.sub(r"[*#_`]", "", ses))
    return yazi, ses


def parcala(metin, n=3900):
    parcalar, cur = [], ""
    for par in metin.split("\n\n"):
        while len(par) > n:  # tek paragraf çok uzunsa böl (önce birikeni gönder, sıra bozulmasın)
            if cur.strip():
                parcalar.append(cur)
                cur = ""
            parcalar.append(par[:n])
            par = par[n:]
        if len(cur) + len(par) + 2 > n and cur:
            parcalar.append(cur)
            cur = ""
        cur += par + "\n\n"
    if cur.strip():
        parcalar.append(cur)
    return parcalar


def tg(yontem, token, **kw):
    r = requests.post(f"https://api.telegram.org/bot{token}/{yontem}", timeout=180, **kw)
    r.raise_for_status()


def ses_uret(metin, dosya):
    import edge_tts
    asyncio.run(edge_tts.Communicate(metin, SES).save(dosya))


def calistir(token, chat):
    simdi = datetime.now(TR)
    haberler, gorulen = haberleri_topla(simdi)
    istek = istek_olustur(haberler, simdi)
    if not istek:
        print("Yeni haber yok.")
        return

    yazi, konusma = yz_analiz(istek)
    baslik = f"📰 Haber Brifingi\n🗓 {baslik_tarih(simdi)}\n\n"
    for p in parcala(baslik + yazi):
        tg("sendMessage", token, data={"chat_id": chat, "text": p,
                                       "disable_web_page_preview": "true"})

    # Metin gittiyse haberleri hemen "görüldü" say: ses hata verse bile aynı haberler tekrar gelmesin
    for liste in haberler.values():
        gorulen.update(h["link"] for h in liste)
    with open(GORULENLER, "w", encoding="utf-8") as f:
        json.dump(sorted(gorulen)[-4000:], f)

    try:
        with tempfile.TemporaryDirectory() as d:
            mp3 = os.path.join(d, "brifing.mp3")
            ses_uret(konusma, mp3)
            with open(mp3, "rb") as f:
                tg("sendAudio", token,
                   data={"chat_id": chat, "title": f"Brifing {simdi:%d.%m %H:%M}"},
                   files={"audio": ("brifing.mp3", f, "audio/mpeg")})
    except Exception as e:
        print(f"[uyarı] Ses gönderilemedi: {str(e).replace(token, '***')}", file=sys.stderr)
        tg("sendMessage", token, data={"chat_id": chat,
                                       "text": "🔇 Bu sefer ses oluşturulamadı, metin yukarıda."})
    print("Brifing gönderildi.")


def main():
    env_yukle()
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "GEMINI_API_KEY"):
        if not os.environ.get(k):
            sys.exit(f"{k} eksik (.env dosyasına ya da ortam değişkenlerine ekleyin).")
    token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    try:
        calistir(token, chat)
    except Exception as e:
        mesaj = str(e).replace(token, "***")[:400]
        try:  # hatayı Telegram'dan da haber ver (token gizlenir)
            tg("sendMessage", token, data={"chat_id": chat, "text": f"⚠️ Brifing hatası: {mesaj}"})
        except Exception:
            pass
        print(f"HATA: {mesaj}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
