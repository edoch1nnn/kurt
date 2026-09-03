from uygulama import veritabani
from uygulama.modeller import Analiz, Bosluk, Teknik, Telemetri, Tespit

TEMEL_TELEMETRI = ['surec_olusturma', 'komut_satiri', 'ust_surec', 'ag_baglantisi', 'dosya_olusturma']

VARSAYILAN_TEKNIKLER = [
    ('T1059.001', 'PowerShell calistirma', 'Windows', ['surec_olusturma', 'komut_satiri', 'ust_surec']),
    ('T1053.005', 'Zamanlanmis gorev', 'Windows', ['surec_olusturma', 'komut_satiri', 'dosya_olusturma']),
    ('T1055', 'Surec enjeksiyonu', 'Windows', ['surec_olusturma', 'ust_surec']),
    ('T1071.001', 'Web protokolleri uzerinden iletisim', 'Windows Linux', ['ag_baglantisi']),
    ('T1105', 'Arac aktarimi', 'Windows Linux', ['ag_baglantisi', 'dosya_olusturma']),
    ('T1021.004', 'SSH ile uzaktan erisim', 'Linux', ['ag_baglantisi', 'komut_satiri']),
    ('T1562.001', 'Savunma mekanizmalarini bozma', 'Windows Linux', ['surec_olusturma', 'komut_satiri']),
    ('T1087', 'Hesap kesfi', 'Windows Linux', ['surec_olusturma', 'komut_satiri']),
]

def baslangic_verisi():
    for teknik_id, ad, platform, gerekli in VARSAYILAN_TEKNIKLER:
        if not Teknik.query.filter_by(teknik_id=teknik_id).first():
            veritabani.session.add(Teknik(teknik_id=teknik_id, ad=ad, platform=platform, gerekli_telemetri=','.join(gerekli), aciklama=f'{ad} icin gorunurluk ve tespit kapsamini olcer.'))
    kaynaklar = [('surec_olusturma','Surec kayitlari'),('komut_satiri','Komut satiri kayitlari'),('ust_surec','Ust surec iliskisi'),('ag_baglantisi','Ag baglanti kayitlari'),('dosya_olusturma','Dosya hareketleri'),('powershell_gunlugu','PowerShell gunlukleri'),('denetim_gunlugu','Denetim gunlukleri')]
    for ad, kaynak in kaynaklar:
        if not Telemetri.query.filter_by(ad=ad).first():
            veritabani.session.add(Telemetri(ad=ad, kaynak=kaynak, kalite=75))
    veritabani.session.commit()

def durum_belirle(skor):
    if skor >= 85: return 'iyi'
    if skor >= 65: return 'orta'
    if skor >= 45: return 'zayif'
    return 'kritik'

def analiz_yap(ad, telemetri, tespitler):
    baslangic_verisi()
    telemetri = set(telemetri or [])
    tespitler = set(tespitler or [])
    teknikler = Teknik.query.all()
    if not teknikler:
        return None
    toplam = 0
    kayitlar = []
    for teknik in teknikler:
        gerekli = [x for x in teknik.gerekli_telemetri.split(',') if x]
        mevcut = sum(x in telemetri for x in gerekli)
        telemetri_skoru = (mevcut / len(gerekli) * 100) if gerekli else 100
        anahtarlar = {teknik.teknik_id.lower(), teknik.ad.lower().split()[0]}
        tespit_skoru = 100 if any(x in tespitler for x in anahtarlar) else 0
        korelasyon = min(100, 40 + mevcut * 20)
        gorunurluk = telemetri_skoru * 0.8 + korelasyon * 0.2
        skor = telemetri_skoru * 0.4 + tespit_skoru * 0.4 + korelasyon * 0.1 + gorunurluk * 0.1
        toplam += skor
        kayitlar.append((teknik, skor, telemetri_skoru, tespit_skoru))
    genel = toplam / len(kayitlar)
    analiz = Analiz(ad=ad or 'adsiz analiz', skor=genel, durum=durum_belirle(genel), telemetri_skoru=genel, tespit_skoru=genel, korelasyon_skoru=genel, gorunurluk_skoru=genel)
    veritabani.session.add(analiz)
    veritabani.session.flush()
    for teknik, skor, telemetri_skoru, tespit_skoru in kayitlar:
        if skor < 85:
            if telemetri_skoru < 85:
                tur = 'telemetri'
                onerme = f'{teknik.ad} icin eksik telemetri kaynaklarini etkinlestir ve komut satiri ile ust surec iliskisini kaydet.'
            elif tespit_skoru < 85:
                tur = 'tespit'
                onerme = f'{teknik.ad} icin tespit kurali ekle ve ilgili olaylari teknik kimligi ile eslestir.'
            else:
                tur = 'korelasyon'
                onerme = f'{teknik.ad} icin birden fazla dusuk oncelikli olayi zincirleyen korelasyon kurali ekle.'
            seviye = 'kritik' if skor < 45 else 'yuksek' if skor < 65 else 'orta'
            veritabani.session.add(Bosluk(teknik=teknik.teknik_id, ad=teknik.ad, seviye=seviye, tur=tur, onerme=onerme, analiz_id=analiz.id))
    veritabani.session.commit()
    return analiz
