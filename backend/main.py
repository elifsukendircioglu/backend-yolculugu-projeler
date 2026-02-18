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

# VERİ YAPISI (Resim URL dahil)
class YeniUrunSemasi(BaseModel):
    ad: str
    fiyat: float
    stok: int
    resim_url: str  # <--- Burası 'resim_url' ise HTML'de de öyle olmalı!

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
    # Program başlarken tabloları otomatik oluşturur (Sıfır hata için)
    db_sorgu('''CREATE TABLE IF NOT EXISTS urunler 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, fiyat REAL, stok INTEGER, resim_url TEXT)''')
    db_sorgu('''CREATE TABLE IF NOT EXISTS satislar 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, urun_adi TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

@app.get("/stok")
def stogu_goster():
    urunler = db_sorgu("SELECT * FROM urunler", fetch=True)
    return {"guncel_stok": [{"urun_adi": u["ad"], "fiyat": u["fiyat"], "stok_adedi": u["stok"], "resim_url": u["resim_url"]} for u in urunler]}

@app.post("/urun-ekle")
def urun_ekle(gelen_urun: YeniUrunSemasi):
    # Bu satır veritabanına eklemeyi yapar
    db_sorgu("INSERT INTO urunler (ad, fiyat, stok, resim_url) VALUES (?, ?, ?, ?)", 
             (gelen_urun.ad, gelen_urun.fiyat, gelen_urun.stok, gelen_urun.resim_url))
    return {"mesaj": "Başarıyla eklendi!"}

@app.post("/satin-al/{urun_adi}")
def satin_al(urun_adi: str):
    db_sorgu("UPDATE urunler SET stok = stok - 1 WHERE lower(ad) = ? AND stok > 0", (urun_adi.lower(),))
    db_sorgu("INSERT INTO satislar (urun_adi) VALUES (?)", (urun_adi,))
    return {"mesaj": "Satıldı!"}

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
    
    # 1. Toplam Ciro Hesabı (Satılan ürünlerin fiyat toplamı)
    # satislar ve urunler tablolarını 'join' ile birleştiriyoruz
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