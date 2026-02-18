import sqlite3

def veritabani_hazirla():
    baglanti = sqlite3.connect("dükkan.db")
    kursor = baglanti.cursor()
    
    # Ürünler tablosunu oluşturalım
    kursor.execute('''
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            fiyat REAL,
            stok INTEGER
        )
    ''')
    
    # Eğer tablo boşsa ilk ürünleri ekleyelim
    kursor.execute("SELECT COUNT(*) FROM urunler")
    if kursor.fetchone()[0] == 0:
        ilk_urunler = [
            ('Laptop', 15000, 10),
            ('Mouse', 250, 50),
            ('Klavye', 500, 20)
        ]
        kursor.executemany("INSERT INTO urunler (ad, fiyat, stok) VALUES (?, ?, ?)", ilk_urunler)
    
    baglanti.commit()
    baglanti.close()

if __name__ == "__main__":
    veritabani_hazirla()