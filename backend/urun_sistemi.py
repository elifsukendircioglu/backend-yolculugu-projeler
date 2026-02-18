class Urun:
    def __init__(self, ad, fiyat, stok):
        self.ad = ad
        self.fiyat = fiyat
        self.stok = stok

    def bilgileri_goster(self):
        print(f"Ürün: {self.ad} | Fiyat: {self.fiyat} TL | Stok: {self.stok}")

    def zam_yap(self, oran):
        self.fiyat += self.fiyat * (oran / 100)
        print(f"--- %{oran} zam yapıldı. Yeni fiyat: {self.fiyat} TL ---")

    def satis_yap(self, adet):
        # Stok kontrolü yapıyoruz
        if self.stok >= adet:
            self.stok -= adet
            print(f"✅ {adet} adet {self.ad} satıldı. Kalan stok: {self.stok}")
        else:
            print(f"❌ Hata: Yetersiz stok! Mevcut stok: {self.stok}")

# --- TEST KISMI ---
# Yeni bir ürün (nesne) oluşturuyoruz
laptop = Urun("Macbook Air", 40000, 5)

laptop.bilgileri_goster() # Önce mevcut durumu gör
laptop.satis_yap(2)       # 2 tane sat (Stok 3'e düşmeli)
laptop.satis_yap(10)      # 10 tane satmaya çalış (Hata vermeli)
laptop.zam_yap(20)        # %20 zam yap
laptop.bilgileri_goster() # Son durumu gör