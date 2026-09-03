# kurt

kurt, yetkili oldugun web sistemlerinin disaridan gorunen guvenlik ve gorunurluk durumunu inceleyen python tabanli bir purple team aracidir.

amac basit: bir web sisteminin disaridan hangi sinyalleri verdigini toplamak, guvenlik gorunurlugunu puanlamak, tespit bosluklarini gostermek ve istersen gemini ile bulgular icin daha anlamli savunma onerileri uretmek.

## özellikler

- gercek web adresleri icin kontrollu gorunurluk analizi
- HTTP durum kodu ve yanit suresi kontrolu
- HTTPS ve TLS sertifika kontrolu
- temel guvenlik basliklari kontrolu
- cookie guvenlik nitelikleri kontrolu
- server ve x-powered-by bilgi sizintisi kontrolu
- DNS kayitlari ve sertifika SAN sinyalleri
- IP, servis ve teknoloji sinyalleri
- bulgu bazli gorunurluk puani
- tespit bosluklari sayfasi
- Gemini destekli savunma onerileri
- Gemini kullanilamazsa yerel onerilerle devam etme
- SQLite ile kolay yerel kullanim
- PostgreSQL ile ortak runtime verisi kullanabilme

bu mod **port taramasi, brute force, exploit, dizin taramasi veya zafiyet istismari yapmaz.** web analizi kontrollu isteklerle disaridan gorunen sinyalleri incelemek icin tasarlanmistir.

## 1. gereksinimler

bilgisayarinda sunlar kurulu olmali:

- python 3.10 veya daha yeni bir surum
- git
- internet baglantisi

## 2. projeyi indir

powershell veya terminal ac:

```powershell
git clone https://github.com/edoch1nnn/kurt.git
cd kurt
```

zaten indirdiysan sadece proje klasorune gir:

```powershell
cd kurt
```

## 3. kutuphaneleri kur

```powershell
python -m pip install -r requirements.txt
```

python komutu calismiyorsa windows'ta sunu dene:

```powershell
py -m pip install -r requirements.txt
```

## 4. ortam dosyasini olustur

`.env.example` dosyasini `.env` olarak kopyala:

```powershell
copy .env.example .env
```

linux/mac kullaniyorsan:

```bash
cp .env.example .env
```

`.env` dosyasini ac ve su ayarlari kontrol et:

```env
VERITABANI_ADRESI=sqlite:///kurt.db
GIZLI_ANAHTAR=kendi-gizli-anahtarini-yaz
HOST=127.0.0.1
PORT=5000
GUNLUK_SEVIYESI=INFO

GEMINI_API_KEY=
AI_MODEL=gemini-2.5-flash
```

## 5. gemini'yi bagla

gemini onerilerini kullanmak istiyorsan google ai studio uzerinden kendi Gemini API anahtarini olustur ve sadece kendi bilgisayarindaki `.env` dosyasina yaz.

```env
GEMINI_API_KEY=buraya_kendi_gemini_anahtarini_yaz
AI_MODEL=gemini-2.5-flash
```

gemini anahtari tanimli degilse kurt yine calisir. bu durumda ai yerine yerel savunma onerileri kullanilir.

## 6. uygulamayi baslat

```powershell
python main.py
```

veya:

```powershell
py main.py
```

uygulama basladiktan sonra tarayicidan:

`http://127.0.0.1:5000`

adresini ac.

## 7. ilk analizi yap

panelde URL alanina yetkili oldugun bir hedef gir:

```text
https://example.com
```

ardindan `analizi baslat` butonuna bas.

kurt hedefe kontrollu bir web istegi gonderir ve elde ettigi dis gorunurluk sinyallerini panelde gosterir.

## 8. sonuclari incele

analizden sonra su bolumleri kontrol et:

- genel durum
- HTTP durumu
- HTTPS
- IP adresleri
- servis sinyalleri
- teknoloji sinyalleri
- sertifika bilgileri
- DNS kayitlari
- guvenlik basliklari
- bulunan bulgular
- gorunurluk puani
- Gemini ozet ve oncelikleri

`t espitler` sayfasinda kaydedilen bulgulari ve tespit bosluklarini ayrica inceleyebilirsin.

## 9. gemini calismiyorsa

panelde su tarz bir mesaj gorursen:

```text
ai kullanilamadi, yerel oneriler kullanildi
```

uygulama tamamen bozulmus demek degildir.

sirayla sunlari kontrol et:

1. `.env` dosyasi proje klasorunde mi
2. `GEMINI_API_KEY` dogru yazilmis mi
3. API anahtarinin basinda veya sonunda bosluk var mi
4. kullandigin model adi dogru mu
5. internet baglantin var mi
6. uygulamayi `.env` degisikliginden sonra yeniden baslattin mi

ornek:

```env
GEMINI_API_KEY=senin_anahtarin
AI_MODEL=gemini-2.5-flash
```

API anahtarini degistirdikten sonra `python main.py` islemini kapatip tekrar baslat.

## 10. saglik kontrolu

uygulamanin ve veritabaninin ayakta olup olmadigini kontrol etmek icin:

`http://127.0.0.1:5000/saglik`

adresini ac.

basarili bir kurulumda `durum` alaninin `iyi` oldugunu gorursun.

## veritabani

kurt varsayilan olarak SQLite kullanir:

```env
VERITABANI_ADRESI=sqlite:///kurt.db
```

tek bilgisayar ve gelistirme icin bu yeterlidir.

ortak runtime verileri icin PostgreSQL kullanabilirsin:

```env
VERITABANI_ADRESI=postgresql+psycopg://kullanici:sifre@sunucu:5432/kurt
```

**github veritabani degildir.** github kaynak kodu ve proje dosyalarini tutar. analiz kayitlari SQLite veya PostgreSQL tarafinda tutulur.

## guvenlik notu

kurt'u sadece sahibi oldugun veya yazili yetkin bulunan sistemlerde kullan.

kurt'un amaci istismar etmek degil, disaridan gorunen guvenlik sinyallerini ve savunma gorunurlugunu anlamaktir.

uygulama su tip aktif saldirgan islemleri yapmaz:

- port taramasi
- brute force
- exploit denemesi
- dizin brute force
- kimlik bilgisi denemesi
- yuksek hacimli istek gonderme

## test

```powershell
python -m unittest discover -s testler -p 'test_*.py'
```

not: testler klasoru yoksa bu komut sonuc vermeyebilir. bu durumda once uygulamanin normal baslatilmasini ve `/saglik` adresini kontrol et.

## gelistirme

kod yapisi kabaca su sekildedir:

```text
kurt/
├── main.py
├── requirements.txt
├── .env.example
├── uygulama/
│   ├── modeller.py
│   ├── yollar.py
│   └── hizmetler/
│       ├── analiz.py
│       ├── web_analiz.py
│       └── ai_oneriler.py
├── sablonlar/
└── static/
```

web analiz motoru dis gorunurluk sinyallerini toplar. analiz katmani bunlari puanlar. ai katmani ise verilen bulgular uzerinden savunma odakli oneriler uretir.

## surum

`0.3.1`

## lisans

MIT
