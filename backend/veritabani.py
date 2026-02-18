import sqlite3

def veritabani_hazirla():
    baglanti = sqlite3.connect("dükkan.db")
    kursor = baglanti.cursor()
    
    # 1. Ürünler tablosuna 'resim_url' sütunu ekleyelim (Eğer yoksa)
    kursor.execute('''
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            fiyat REAL,
            stok INTEGER,
            resim_url TEXT DEFAULT 'https://via.placeholder.com/150'
        )
    ''')
    
    # 2. Satışlar tablosunu oluşturalım (Kim neyi ne zaman aldı?)
    kursor.execute('''
        CREATE TABLE IF NOT EXISTS satislar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    baglanti.commit()
    baglanti.close()

if __name__ == "__main__":
    veritabani_hazirla()