from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# VERİ YAPISI (Kategori dahil edildi)
class YeniUrunSemasi(BaseModel):
    ad: str
    fiyat: float
    stok: int
    resim_url: str  
    kategori: str

# YARDIMCI FONKSİYON
def db_sorgu(sorgu, parametre=(), fetch=False):
    baglanti = sqlite3.connect("dükkan.db")
    baglanti.row_factory = sqlite3.Row
    kursor = baglanti.cursor()
    kursor.execute(sorgu, parametre)
    sonuc = kursor.fetchall() if fetch else None
    baglanti.commit()
    baglanti.close()
    return sonuc

@app.on_event("startup")
def tablo_olustur():
    # Kategori sütunu eklenmiş tablo yapısı
    db_sorgu('''CREATE TABLE IF NOT EXISTS urunler 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 ad TEXT UNIQUE, 
                 fiyat REAL, 
                 stok INTEGER, 
                 resim_url TEXT, 
                 kategori TEXT)''')
    
    db_sorgu('''CREATE TABLE IF NOT EXISTS satislar 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 urun_adi TEXT, 
                 tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

@app.get("/stok")
def stogu_goster():
    urunler = db_sorgu("SELECT * FROM urunler", fetch=True)
    return {"guncel_stok": [
        {
            "urun_adi": u["ad"], 
            "fiyat": u["fiyat"], 
            "stok_adedi": u["stok"], 
            "resim_url": u["resim_url"],
            "kategori": u["kategori"] # Kategori bilgisini frontend'e gönderiyoruz
        } for u in urunler
    ]}

@app.post("/urun-ekle")
def urun_ekle(gelen_urun: YeniUrunSemasi):
    # Kategori verisini de VALUES içine ekledik
    db_sorgu("INSERT INTO urunler (ad, fiyat, stok, resim_url, kategori) VALUES (?, ?, ?, ?, ?)", 
             (gelen_urun.ad, gelen_urun.fiyat, gelen_urun.stok, gelen_urun.resim_url, gelen_urun.kategori))
    return {"mesaj": "Başarıyla eklendi!"}

@app.post("/satin-al/{urun_adi}")
def satin_al(urun_adi: str):
    # 1. Gelen ismin başındaki sonundaki boşlukları temizleyelim
    temiz_ad = urun_adi.strip()
    
    # 2. Stok güncelleme (Büyük/Küçük harf duyarlılığını SQL seviyesinde öldürüyoruz)
    db_sorgu("""
        UPDATE urunler 
        SET stok = stok - 1 
        WHERE TRIM(LOWER(ad)) = LOWER(?) AND stok > 0
    """, (temiz_ad,))
    
    # 3. Satış kaydı (Orijinal ismiyle kaydedelim)
    db_sorgu("INSERT INTO satislar (urun_adi) VALUES (?)", (temiz_ad,))
    
    return {"mesaj": "İşlem denendi!"}
@app.get("/satis-gecmisi")
def satis_gecmisi():
    satislar = db_sorgu("SELECT * FROM satislar ORDER BY tarih DESC LIMIT 10", fetch=True)
    return {"satislar": [{"urun": s["urun_adi"], "tarih": s["tarih"]} for s in satislar]}

@app.delete("/urun-sil/{urun_adi}")
def urun_sil(urun_adi: str):
    db_sorgu("DELETE FROM urunler WHERE lower(ad) = ?", (urun_adi.lower(),))
    return {"mesaj": "Silindi"}

@app.get("/magaza-ozet")
def magaza_ozet():
    baglanti = sqlite3.connect("dükkan.db")
    baglanti.row_factory = sqlite3.Row
    kursor = baglanti.cursor()
    
    # 1. Toplam Ciro Hesabı
    kursor.execute('''
        SELECT SUM(u.fiyat) as toplam_kazanc 
        FROM satislar s 
        JOIN urunler u ON s.urun_adi = u.ad
    ''')
    ciro = kursor.fetchone()["toplam_kazanc"] or 0
    
    # 2. En Çok Satan Ürün
    kursor.execute('''
        SELECT urun_adi, COUNT(urun_adi) as adet 
        FROM satislar 
        GROUP BY urun_adi 
        ORDER BY adet DESC LIMIT 1
    ''')
    populer = kursor.fetchone()
    populer_isim = populer["urun_adi"] if populer else "Henüz yok"
    
    baglanti.close()
    return {
        "toplam_ciro": round(ciro, 2),
        "en_populer": populer_isim
    }
from fastapi.responses import PlainTextResponse

@app.get("/stok-indir")
def stok_indir():
    urunler = db_sorgu("SELECT * FROM urunler", fetch=True)
    
    # CSV formatında başlıkları oluşturalım
    csv_icerik = "Ürün Adı,Fiyat,Stok,Kategori\n"
    
    for u in urunler:
        csv_icerik += f"{u['ad']},{u['fiyat']},{u['stok']},{u['kategori']}\n"
    
    return PlainTextResponse(
        content=csv_icerik,
        headers={"Content-Disposition": "attachment; filename=stok_raporu.csv"}
    )