from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
# main.py dosyasında mutlaka olması gereken kısım:
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Bu yıldız her yerden erişime izin verir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELLER (Veri Yapıları) ---

class Urun:
    """Arka odadaki ürünün teknik yapısı"""
    def __init__(self, ad: str, fiyat: float, stok: int):
        self.ad = ad
        self.fiyat = fiyat
        self.stok = stok

class YeniUrunSemasi(BaseModel):
    """Müşteriden (Dışarıdan) beklediğimiz veri formatı"""
    ad: str
    fiyat: float
    stok: int

# --- VERİTABANI (Şimdilik geçici liste) ---

dukan_stogu = [
    Urun("Laptop", 15000, 10),
    Urun("Mouse", 250, 50),
    Urun("Klavye", 500, 20)
]

# --- YOLLAR (Endpoints) ---

@app.get("/")
def ana_sayfa():
    return {"mesaj": "Dükkan Santraline Hoş Geldiniz! 🚀"}

@app.get("/stok")
def stogu_goster():
    """Tüm ürünleri listeleyen kapı"""
    liste = []
    for urun in dukan_stogu:
        liste.append({
            "urun_adi": urun.ad,
            "fiyat": urun.fiyat,
            "stok_adedi": urun.stok
        })
    return {"guncel_stok": liste}

@app.post("/urun-ekle")
def urun_ekle(gelen_urun: YeniUrunSemasi):
    """Yeni ürün ekleyen veya var olanın stoğunu güncelleyen kapı"""
    
    # 1. Kontrol: Bu ürün zaten var mı?
    for mevcut_urun in dukan_stogu:
        if mevcut_urun.ad.lower() == gelen_urun.ad.lower():
            # Ürün bulundu! Stoğu artırıyoruz.
            mevcut_urun.stok += gelen_urun.stok
            # Fiyat güncellenmiş olabilir, onu da güncelleyelim
            mevcut_urun.fiyat = gelen_urun.fiyat
            
            return {
                "mesaj": f"'{mevcut_urun.ad}' zaten vardı, stok {gelen_urun.stok} adet artırıldı.",
                "yeni_toplam_stok": mevcut_urun.stok
            }
    
    # 2. Ürün bulunamadıysa: Yeni kayıt oluştur
    yeni_kayit = Urun(gelen_urun.ad, gelen_urun.fiyat, gelen_urun.stok)
    dukan_stogu.append(yeni_kayit)
    
    return {
        "mesaj": f"'{gelen_urun.ad}' ilk kez stoklara eklendi!",
        "toplam_urun_cesidi": len(dukan_stogu)
    }
@app.post("/satin-al/{urun_adi}")
def satin_al(urun_adi: str):
    for urun in dukan_stogu:
        if urun.ad.lower() == urun_adi.lower():
            if urun.stok > 0:
                urun.stok -= 1
                return {"mesaj": f"{urun.ad} satıldı!", "kalan_stok": urun.stok}
            else:
                raise HTTPException(status_code=400, detail="Maalesef stok tükendi!")
    
    raise HTTPException(status_code=404, detail="Ürün bulunamadı!")