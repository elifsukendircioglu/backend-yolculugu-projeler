from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import sqlite3

app = FastAPI()

# Tarayıcı izinleri (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- VERİ YAPISI ---
class YeniUrunSemasi(BaseModel):
    ad: str
    fiyat: float
    stok: int
    resim_url: str  
    kategori: str

# --- YARDIMCI FONKSİYON (Veritabanı İşlemleri) ---
def db_sorgu(sorgu, parametre=(), fetch=False):
    baglanti = sqlite3.connect("dükkan.db")
    baglanti.row_factory = sqlite3.Row
    kursor = baglanti.cursor()
    kursor.execute(sorgu, parametre)
    sonuc = None
    if fetch:
        # Verileri sözlük formatına çeviriyoruz ki Frontend rahat okusun
        sonuc = [dict(row) for row in kursor.fetchall()]
    baglanti.commit()
    baglanti.close()
    return sonuc

# --- BAŞLANGIÇTA TABLOLARI OLUŞTUR ---
@app.on_event("startup")
def tablo_olustur():
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

# --- ENDPOINTLER (Backend Kapıları) ---

@app.get("/stok")
def stogu_goster():
    urunler = db_sorgu("SELECT * FROM urunler", fetch=True)
    return {"guncel_stok": [
        {
            "urun_adi": u["ad"], 
            "fiyat": u["fiyat"], 
            "stok_adedi": u["stok"], 
            "resim_url": u["resim_url"],
            "kategori": u["kategori"]
        } for u in urunler
    ]}

@app.post("/urun-ekle")
def urun_ekle(gelen_urun: YeniUrunSemasi):
    db_sorgu("INSERT INTO urunler (ad, fiyat, stok, resim_url, kategori) VALUES (?, ?, ?, ?, ?)", 
             (gelen_urun.ad, gelen_urun.fiyat, gelen_urun.stok, gelen_urun.resim_url, gelen_urun.kategori))
    return {"mesaj": "Başarıyla eklendi!"}

@app.post("/satin-al/{urun_adi}")
def satin_al(urun_adi: str):
    temiz_ad = urun_adi.strip()
    # Stok düşür
    db_sorgu("""
        UPDATE urunler 
        SET stok = stok - 1 
        WHERE TRIM(LOWER(ad)) = LOWER(?) AND stok > 0
    """, (temiz_ad,))
    # Satışı kaydet
    db_sorgu("INSERT INTO satislar (urun_adi) VALUES (?)", (temiz_ad,))
    return {"mesaj": "Satın alma işlemi başarılı!"}

@app.get("/satis-gecmisi")
def satis_gecmisi():
    satislar = db_sorgu("SELECT urun_adi as urun, tarih FROM satislar ORDER BY tarih DESC LIMIT 10", fetch=True)
    return {"satislar": satislar}

@app.delete("/urun-sil/{urun_adi}")
def urun_sil(urun_adi: str):
    db_sorgu("DELETE FROM urunler WHERE lower(ad) = ?", (urun_adi.lower(),))
    return {"mesaj": "Ürün silindi"}

@app.get("/magaza-ozet")
def magaza_ozet():
    # Ciro Hesabı (JOIN ile fiyatları çekiyoruz)
    ciro_sonuc = db_sorgu('''
        SELECT SUM(u.fiyat) as toplam_kazanc 
        FROM satislar s 
        JOIN urunler u ON s.urun_adi = u.ad
    ''', fetch=True)
    ciro = ciro_sonuc[0]["toplam_kazanc"] or 0
    
    # En Popüler Ürün
    populer_sonuc = db_sorgu('''
        SELECT urun_adi, COUNT(urun_adi) as adet 
        FROM satislar 
        GROUP BY urun_adi 
        ORDER BY adet DESC LIMIT 1
    ''', fetch=True)
    populer_isim = populer_sonuc[0]["urun_adi"] if populer_sonuc else "Henüz yok"
    
    return {
        "toplam_ciro": round(ciro, 2),
        "en_populer": populer_isim
    }

@app.get("/stok-indir")
def stok_indir():
    urunler = db_sorgu("SELECT * FROM urunler", fetch=True)
    csv_icerik = "Urun Adi,Fiyat,Stok,Kategori\n"
    for u in urunler:
        csv_icerik += f"{u['ad']},{u['fiyat']},{u['stok']},{u['kategori']}\n"
    
    return PlainTextResponse(
        content=csv_icerik,
        headers={"Content-Disposition": "attachment; filename=stok_raporu.csv"}
    )