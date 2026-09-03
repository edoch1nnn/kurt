from datetime import datetime, timezone
from uygulama import veritabani

class Analiz(veritabani.Model):
    id = veritabani.Column(veritabani.Integer, primary_key=True)
    ad = veritabani.Column(veritabani.String(160), nullable=False)
    skor = veritabani.Column(veritabani.Float, nullable=False)
    durum = veritabani.Column(veritabani.String(30), nullable=False)
    telemetri_skoru = veritabani.Column(veritabani.Float, nullable=False, default=0)
    tespit_skoru = veritabani.Column(veritabani.Float, nullable=False, default=0)
    korelasyon_skoru = veritabani.Column(veritabani.Float, nullable=False, default=0)
    gorunurluk_skoru = veritabani.Column(veritabani.Float, nullable=False, default=0)
    tarih = veritabani.Column(veritabani.DateTime, default=lambda: datetime.now(timezone.utc))

class Teknik(veritabani.Model):
    id = veritabani.Column(veritabani.Integer, primary_key=True)
    teknik_id = veritabani.Column(veritabani.String(30), unique=True, nullable=False)
    ad = veritabani.Column(veritabani.String(160), nullable=False)
    platform = veritabani.Column(veritabani.String(160), nullable=False)
    gerekli_telemetri = veritabani.Column(veritabani.Text, nullable=False)
    aciklama = veritabani.Column(veritabani.Text, nullable=False, default='')

class Bosluk(veritabani.Model):
    id = veritabani.Column(veritabani.Integer, primary_key=True)
    teknik = veritabani.Column(veritabani.String(30), nullable=False)
    ad = veritabani.Column(veritabani.String(160), nullable=False)
    seviye = veritabani.Column(veritabani.String(30), nullable=False)
    tur = veritabani.Column(veritabani.String(40), nullable=False)
    onerme = veritabani.Column(veritabani.Text, nullable=False)
    analiz_id = veritabani.Column(veritabani.Integer, nullable=False)

class WebAnalizDetay(veritabani.Model):
    id = veritabani.Column(veritabani.Integer, primary_key=True)
    analiz_id = veritabani.Column(veritabani.Integer, unique=True, nullable=False)
    veri = veritabani.Column(veritabani.Text, nullable=False)

class Telemetri(veritabani.Model):
    id = veritabani.Column(veritabani.Integer, primary_key=True)
    ad = veritabani.Column(veritabani.String(120), unique=True, nullable=False)
    kaynak = veritabani.Column(veritabani.String(120), nullable=False)
    etkin = veritabani.Column(veritabani.Boolean, default=True, nullable=False)
    kalite = veritabani.Column(veritabani.Integer, default=70, nullable=False)

class Tespit(veritabani.Model):
    id = veritabani.Column(veritabani.Integer, primary_key=True)
    ad = veritabani.Column(veritabani.String(160), nullable=False)
    teknik = veritabani.Column(veritabani.String(30), nullable=False)
    kural_turu = veritabani.Column(veritabani.String(40), nullable=False)
    etkin = veritabani.Column(veritabani.Boolean, default=True, nullable=False)
    guc = veritabani.Column(veritabani.Integer, default=70, nullable=False)

class Kural(veritabani.Model):
    id = veritabani.Column(veritabani.Integer, primary_key=True)
    ad = veritabani.Column(veritabani.String(180), nullable=False)
    teknik = veritabani.Column(veritabani.String(30), nullable=False)
    icerik = veritabani.Column(veritabani.Text, nullable=False)
    kaynak = veritabani.Column(veritabani.String(60), default='sigma', nullable=False)
