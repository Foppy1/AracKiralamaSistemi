import sys  # Sistem işlemleri için gerekli kütüphane
import json
import requests  # HTTP istekleri yapmak için gerekli kütüphane
import sqlite3  # SQLite veritabanı kullanmak için gerekli kütüphane
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QDialog, QMainWindow  # PyQt5 ile GUI oluşturmak için gerekli bileşenler
from PyQt5.QtGui import QPixmap  # Resimleri göstermek için gerekli bileşen
from PyQt5.QtCore import Qt  # PyQt5'in temel bileşenleri

# Araç sınıfı tanımı
class Arac:
    def __init__(self, arac_id, marka, model, yil, gunluk_kiralama_ucreti):
        # Araç özellikleri
        self.arac_id = arac_id
        self.marka = marka
        self.model = model
        self.yil = yil
        self.gunluk_kiralama_ucreti = gunluk_kiralama_ucreti
        self.kiralama_durumu = False  # Kiralama durumu (başlangıçta False olarak ayarlanmış)

    # Araç kiralama durumunu güncellemek için metot
    def arac_durumu_guncelle(self, durum):
        self.kiralama_durumu = durum

# Müşteri sınıfı tanımı
class Musteri:
    def __init__(self, ad, soyad, telefon):
        # Müşteri özellikleri
        self.ad = ad
        self.soyad = soyad
        self.telefon = telefon

# KiralamaSistemi sınıfı tanımı
class KiralamaSistemi:
    def __init__(self):
        # Veritabanı bağlantısı oluştur
        self.conn = sqlite3.connect('kiralama.db')
        self.cur = self.conn.cursor()

        # Tabloları oluştur (varsa)
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Arabalar (
                            arac_id TEXT PRIMARY KEY,
                            marka TEXT,
                            model TEXT,
                            yil TEXT,
                            gunluk_kiralama_ucreti TEXT,
                            kiralama_durumu INTEGER
                            )''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Musteriler (
                            telefon TEXT PRIMARY KEY,
                            ad TEXT,
                            soyad TEXT
                            )''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS KiralamaGecmisi (
                            arac_id TEXT,
                            musteri_telefon TEXT,
                            FOREIGN KEY (arac_id) REFERENCES Arabalar(arac_id),
                            FOREIGN KEY (musteri_telefon) REFERENCES Musteriler(telefon)
                            )''')
        self.conn.commit()  # Değişiklikleri kaydet

    # Araba ekleme metodu
    def arac_ekle(self, arac):
        # Veritabanına araç ekle
        self.cur.execute("INSERT INTO Arabalar VALUES (?, ?, ?, ?, ?, ?)",
                         (arac.arac_id, arac.marka, arac.model, arac.yil, arac.gunluk_kiralama_ucreti, 0))  # Kiralama durumu başlangıçta 0
        self.conn.commit()
        return f"{arac.marka} {arac.model} aracı kiralama sistemine eklendi."

    # Müşteri ekleme metodu
    def musteri_ekle(self, musteri):
        # Veritabanına müşteri ekle
        self.cur.execute("INSERT INTO Musteriler VALUES (?, ?, ?)",
                         (musteri.telefon, musteri.ad, musteri.soyad))
        self.conn.commit()
        return f"{musteri.ad} {musteri.soyad} müşterisi kaydedildi."

    # Kiralama yapma metodu
    def kiralama_yap(self, arac_id, musteri_telefon):
        # Veritabanında araç ve müşteriyi kontrol et
        self.cur.execute("SELECT * FROM Arabalar WHERE arac_id=?", (arac_id,))
        arac = self.cur.fetchone()
        self.cur.execute("SELECT * FROM Musteriler WHERE telefon=?", (musteri_telefon,))
        musteri = self.cur.fetchone()

        # Kiralama yap
        if arac and musteri:
            if arac[5] == 0:  # Araç kiralanmamışsa
                self.cur.execute("UPDATE Arabalar SET kiralama_durumu=1 WHERE arac_id=?", (arac_id,))
                self.cur.execute("INSERT INTO KiralamaGecmisi VALUES (?, ?)", (arac_id, musteri_telefon))
                self.conn.commit()
                return f"{arac[1]} {arac[2]} aracı, {musteri[1]} {musteri[2]} tarafından kiralandı."
            else:
                return "Bu araç zaten kiralanmış."
        else:
            return "Belirtilen araç veya müşteri bulunamadı."

    # Kiralama iptal etme metodu
    def kiralama_iptal_et(self, arac_id):
        # Veritabanında araç kontrol et
        self.cur.execute("SELECT * FROM Arabalar WHERE arac_id=?", (arac_id,))
        arac = self.cur.fetchone()

        # Kiralama iptal et
        if arac:
            if arac[5] == 1:  # Araç kiralanmışsa
                self.cur.execute("UPDATE Arabalar SET kiralama_durumu=0 WHERE arac_id=?", (arac_id,))
                self.cur.execute("DELETE FROM KiralamaGecmisi WHERE arac_id=?", (arac_id,))
                self.conn.commit()
                return f"{arac[1]} {arac[2]} aracı kiralama iptal edildi."
            else:
                return "Bu araç zaten kiralanmamış."
        else:
            return "Belirtilen araç bulunamadı."

    # Kiralama bilgisi alma metodu
    def kiralama_bilgisi(self):
        self.cur.execute("SELECT * FROM KiralamaGecmisi")
        kiralama_gecmisi = self.cur.fetchall()
        bilgi = "Kiralama Geçmişi:\n"
        for kiralama in kiralama_gecmisi:
            arac_id, musteri_telefon = kiralama
            self.cur.execute("SELECT * FROM Arabalar WHERE arac_id=?", (arac_id,))
            arac = self.cur.fetchone()
            self.cur.execute("SELECT * FROM Musteriler WHERE telefon=?", (musteri_telefon,))
            musteri = self.cur.fetchone()
            if arac and musteri:
                bilgi += f"Araç: {arac[1]} {arac[2]}, Müşteri: {musteri[1]} {musteri[2]}, Telefon: {musteri_telefon}\n"
        return bilgi

# AnaArayuz sınıfı tanımı
class AnaArayuz(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARAÇ KİRALAMA SİSTEMİ")
        self.initUI()

    def initUI(self):
        # Butonlar oluştur
        arac_ekle_button = QPushButton("Araç Ekle")
        arac_ekle_button.clicked.connect(self.arac_ekle_clicked)

        musteri_ekle_button = QPushButton("Müşteri Ekle")
        musteri_ekle_button.clicked.connect(self.musteri_ekle_clicked)

        kiralama_yap_button = QPushButton("Kiralama Yap")
        kiralama_yap_button.clicked.connect(self.kiralama_yap_clicked)

        kiralama_iptal_et_button = QPushButton("Kiralama İptal Et")
        kiralama_iptal_et_button.clicked.connect(self.kiralama_iptal_et_clicked)

        # Dikey bir düzen oluştur
        layout = QVBoxLayout()
        layout.addWidget(arac_ekle_button)
        layout.addWidget(musteri_ekle_button)
        layout.addWidget(kiralama_yap_button)
        layout.addWidget(kiralama_iptal_et_button)

        # Resim göstermek için bir QLabel ekle
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(300, 200)
        self.fetch_photo_from_url("https://cdn.cetas.com.tr/Delivery/Public/Image/-1x-1/arac-kiralama_4258138668.jpg")
        layout.addWidget(self.photo_label)

        self.setLayout(layout)

    # URL'den fotoğraf indir
    def fetch_photo_from_url(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.photo_label.setPixmap(pixmap.scaledToWidth(300))
        except Exception as e:
            print("Error fetching photo:", e)

    # Araç ekleme butonuna tıklandığında çağrılır
    def arac_ekle_clicked(self):
        arac_ekle_arayuz = AracEkleArayuz()
        arac_ekle_arayuz.exec_()

    # Müşteri ekleme butonuna tıklandığında çağrılır
    def musteri_ekle_clicked(self):
        musteri_ekle_arayuz = MusteriEkleArayuz()
        musteri_ekle_arayuz.exec_()

    # Kiralama yapma butonuna tıklandığında çağrılır
    def kiralama_yap_clicked(self):
        kiralama_yap_arayuz = KiralamaYapArayuz()
        kiralama_yap_arayuz.exec_()

    # Kiralama iptal etme butonuna tıklandığında çağrılır
    def kiralama_iptal_et_clicked(self):
        kiralama_iptal_et_arayuz = KiralamaIptalEtArayuz()
        kiralama_iptal_et_arayuz.exec_()

# AracEkleArayuz sınıfı tanımı
class AracEkleArayuz(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Araç Ekle")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Araç ID giriş kutusu
        self.arac_id_label = QLabel("Araç ID:")
        self.arac_id_entry = QLineEdit()
        layout.addWidget(self.arac_id_label)
        layout.addWidget(self.arac_id_entry)

        # Marka giriş kutusu
        self.marka_label = QLabel("Marka:")
        self.marka_entry = QLineEdit()
        layout.addWidget(self.marka_label)
        layout.addWidget(self.marka_entry)

        # Model giriş kutusu
        self.model_label = QLabel("Model:")
        self.model_entry = QLineEdit()
        layout.addWidget(self.model_label)
        layout.addWidget(self.model_entry)

        # Yıl giriş kutusu
        self.yil_label = QLabel("Yıl:")
        self.yil_entry = QLineEdit()
        layout.addWidget(self.yil_label)
        layout.addWidget(self.yil_entry)

        # Günlük kiralama ücreti giriş kutusu
        self.gunluk_kiralama_ucreti_label = QLabel("Günlük Kiralama Ücreti:")
        self.gunluk_kiralama_ucreti_entry = QLineEdit()
        layout.addWidget(self.gunluk_kiralama_ucreti_label)
        layout.addWidget(self.gunluk_kiralama_ucreti_entry)

        # Araç ekle butonu
        self.arac_ekle_button = QPushButton("Araç Ekle")
        self.arac_ekle_button.clicked.connect(self.arac_ekle)
        layout.addWidget(self.arac_ekle_button)

        # Sonuç etiketi
        self.result_label = QLabel()
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    # Araç ekleme metodu
    def arac_ekle(self):
        arac_id = self.arac_id_entry.text()
        marka = self.marka_entry.text()
        model = self.model_entry.text()
        yil = self.yil_entry.text()
        gunluk_kiralama_ucreti = self.gunluk_kiralama_ucreti_entry.text()

        result = kiralama_sistemi.arac_ekle(Arac(arac_id, marka, model, yil, gunluk_kiralama_ucreti))
        self.result_label.setText(result)

# MusteriEkleArayuz sınıfı tanımı
class MusteriEkleArayuz(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Müşteri Ekle")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Ad giriş kutusu
        self.ad_label = QLabel("Ad:")
        self.ad_entry = QLineEdit()
        layout.addWidget(self.ad_label)
        layout.addWidget(self.ad_entry)

        # Soyad giriş kutusu
        self.soyad_label = QLabel("Soyad:")
        self.soyad_entry = QLineEdit()
        layout.addWidget(self.soyad_label)
        layout.addWidget(self.soyad_entry)

        # Telefon giriş kutusu
        self.telefon_label = QLabel("Telefon:")
        self.telefon_entry = QLineEdit()
        layout.addWidget(self.telefon_label)
        layout.addWidget(self.telefon_entry)

        # Müşteri ekle butonu
        self.musteri_ekle_button = QPushButton("Müşteri Ekle")
        self.musteri_ekle_button.clicked.connect(self.musteri_ekle)
        layout.addWidget(self.musteri_ekle_button)

        # Sonuç etiketi
        self.result_label = QLabel()
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    # Müşteri ekleme metodu
    def musteri_ekle(self):
        ad = self.ad_entry.text()
        soyad = self.soyad_entry.text()
        telefon = self.telefon_entry.text()

        result = kiralama_sistemi.musteri_ekle(Musteri(ad, soyad, telefon))
        self.result_label.setText(result)

# KiralamaYapArayuz sınıfı tanımı
class KiralamaYapArayuz(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kiralama Yap")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Araç ID giriş kutusu
        self.arac_id_label = QLabel("Araç ID:")
        self.arac_id_entry = QLineEdit()
        layout.addWidget(self.arac_id_label)
        layout.addWidget(self.arac_id_entry)

        # Müşteri telefon giriş kutusu
        self.musteri_telefon_label = QLabel("Müşteri Telefon:")
        self.musteri_telefon_entry = QLineEdit()
        layout.addWidget(self.musteri_telefon_label)
        layout.addWidget(self.musteri_telefon_entry)

        # Kiralama yap butonu
        self.kiralama_yap_button = QPushButton("Kiralama Yap")
        self.kiralama_yap_button.clicked.connect(self.kiralama_yap)
        layout.addWidget(self.kiralama_yap_button)

        # Sonuç etiketi
        self.result_label = QLabel()
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    # Kiralama yapma metodu
    def kiralama_yap(self):
        arac_id = self.arac_id_entry.text()
        musteri_telefon = self.musteri_telefon_entry.text()

        result = kiralama_sistemi.kiralama_yap(arac_id, musteri_telefon)
        self.result_label.setText(result)

# KiralamaIptalEtArayuz sınıfı tanımı
class KiralamaIptalEtArayuz(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kiralama İptal Et")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # İptal edilecek kiralamanın araç ID'si giriş kutusu
        self.arac_id_iptal_label = QLabel("İptal Edilecek Kiralamanın Araç ID'si:")
        self.arac_id_iptal_entry = QLineEdit()
        layout.addWidget(self.arac_id_iptal_label)
        layout.addWidget(self.arac_id_iptal_entry)

        # Kiralama iptal et butonu
        self.kiralama_iptal_button = QPushButton("Kiralama İptal Et")
        self.kiralama_iptal_button.clicked.connect(self.kiralama_iptal_et)
        layout.addWidget(self.kiralama_iptal_button)

        # Sonuç etiketi
        self.result_label = QLabel()
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    # Kiralama iptal etme metodu
    def kiralama_iptal_et(self):
        arac_id = self.arac_id_iptal_entry.text()

        result = kiralama_sistemi.kiralama_iptal_et(arac_id)
        self.result_label.setText(result)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kiralama_sistemi = KiralamaSistemi()  # KiralamaSistemi sınıfından bir örnek oluştur
    ana_arayuz = AnaArayuz()  # AnaArayuz sınıfından bir örnek oluştur
    ana_arayuz.show()  # Ana arayüzü göster
    sys.exit(app.exec_())  # Uygulamayı çalıştır ve event loop'a gir
