from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# --- CORS AYARLARI ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELLER (Pydantic Kullanıyoruz) ---
class YeniUrunSemasi(BaseModel):
    ad: str
    fiyat: float
    stok: int

# --- YARDIMCI FONKSİYONLAR (Veritabanı İşlemleri) ---

def db_sorgu(sorgu, parametre=(), fetch=False):
    """Veritabanı bağlantısını açar, işlemi yapar ve kapatır."""
    baglanti = sqlite3.connect("dükkan.db")
    baglanti.row_factory = sqlite3.Row
    kursor = baglanti.cursor()
    kursor.execute(sorgu, parametre)
    
    sonuc = None
    if fetch:
        sonuc = kursor.fetchall()
    
    baglanti.commit()
    baglanti.close()
    return sonuc

# --- YOLLAR (Endpoints) ---

@app.get("/")
def ana_sayfa():
    return {"mesaj": "Dükkanın Veritabanı Santraline Hoş Geldiniz! 🏛️"}

@app.get("/stok")
def stogu_goster():
    """Veritabanındaki tüm ürünleri listeler"""
    urunler = db_sorgu("SELECT * FROM urunler", fetch=True)
    liste = []
    for u in urunler:
        liste.append({
            "urun_adi": u["ad"],
            "fiyat": u["fiyat"],
            "stok_adedi": u["stok"]
        })
    return {"guncel_stok": liste}

@app.post("/urun-ekle")
def urun_ekle(gelen_urun: YeniUrunSemasi):
    """Ürün varsa stoğu artırır, yoksa yeni ürün ekler"""
    # Önce ürün var mı kontrol et
    mevcut = db_sorgu("SELECT * FROM urunler WHERE lower(ad) = ?", (gelen_urun.ad.lower(),), fetch=True)
    
    if mevcut:
        # Ürün var: Güncelle (Update)
        yeni_stok = mevcut[0]["stok"] + gelen_urun.stok
        db_sorgu("UPDATE urunler SET stok = ?, fiyat = ? WHERE ad = ?", 
                 (yeni_stok, gelen_urun.fiyat, mevcut[0]["ad"]))
        return {"mesaj": f"'{gelen_urun.ad}' stoğu güncellendi.", "yeni_stok": yeni_stok}
    else:
        # Ürün yok: Yeni Kayıt (Insert)
        db_sorgu("INSERT INTO urunler (ad, fiyat, stok) VALUES (?, ?, ?)", 
                 (gelen_urun.ad, gelen_urun.fiyat, gelen_urun.stok))
        return {"mesaj": f"'{gelen_urun.ad}' ilk kez veritabanına eklendi!"}

@app.post("/satin-al/{urun_adi}")
def satin_al(urun_adi: str):
    """Veritabanında stoğu bir azaltır"""
    # Ürünü bul ve stoğu 0'dan büyükse düşür
    baglanti = sqlite3.connect("dükkan.db")
    kursor = baglanti.cursor()
    
    kursor.execute("UPDATE urunler SET stok = stok - 1 WHERE lower(ad) = ? AND stok > 0", (urun_adi.lower(),))
    degisen_satir = kursor.rowcount
    
    baglanti.commit()
    baglanti.close()

    if degisen_satir > 0:
        return {"mesaj": f"{urun_adi} satıldı ve veritabanı güncellendi!"}
    else:
        raise HTTPException(status_code=400, detail="Ürün bulunamadı veya stok tükendi!")
@app.delete("/urun-sil/{urun_adi}")
def urun_sil(urun_adi: str):
    baglanti = sqlite3.connect("dükkan.db")
    kursor = baglanti.cursor()
    
    kursor.execute("DELETE FROM urunler WHERE lower(ad) = ?", (urun_adi.lower(),))
    silinen_sayisi = kursor.rowcount
    
    baglanti.commit()
    baglanti.close()

    if silinen_sayisi > 0:
        return {"mesaj": f"'{urun_adi}' veritabanından tamamen silindi!"}
    else:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı!")