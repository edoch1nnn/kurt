# kurt v0.2.1

kurt guvenlik yiginindaki mitre att&ck gorunurluk tespit ve korelasyon bosluklarini analiz eden python tabanli bir purple team aracidir

## mimari

kurt iki veritabani modunu destekler:

- **sqlite:** ilk kurulum, gelistirme ve tek bilgisayar testi icin. veriler `kurt.db` dosyasinda tutulur
- **postgresql:** merkezi kullanim icin. birden fazla terminal ayni PostgreSQL veritabanina baglanarak ortak analiz verilerini gorur

**github veritabani degildir.** github kaynak kodunu ve statik proje dosyalarini tasir. ortak calisma verileri PostgreSQL'de tutulur.

akıs:

`github -> kurt kodu -> sqlite veya merkezi postgresql -> analizler`

## ne yapiyor

kurt bir saldiri gerceklestirme araci degildir. mevcut telemetri ve tespit yeteneklerini puanlar ve hangi tekniklerde kor noktalar oldugunu gosterir

`mitre teknigi -> gerekli telemetri -> mevcut telemetri -> tespit -> korelasyon -> skor -> bosluk`

## hizli baslangic

powershell:

```powershell
git clone https://github.com/edoch1nnn/kurt.git
cd kurt
python -m pip install -r requirements.txt
copy .env.example .env
python main.py
```

veya:

```powershell
powershell -ExecutionPolicy Bypass -File .\baslat.ps1
```

sonra tarayicidan:

`http://127.0.0.1:5000`

## yerel sqlite modu

varsayilan `.env`:

```env
VERITABANI_ADRESI=sqlite:///kurt.db
GIZLI_ANAHTAR=kurt-gelisme-anahtari-2026
HOST=127.0.0.1
PORT=5000
GUNLUK_SEVIYESI=INFO
```

ilk calistirmada proje klasorunde `kurt.db` olusur.

## merkezi postgresql modu

merkezi kullanim icin gercek bir PostgreSQL sunucusu gerekir. `.env` icindeki adresi degistir:

```env
VERITABANI_ADRESI=postgresql+psycopg://kullanici:sifre@sunucu:5432/kurt
```

`postgres://...` veya `postgresql://...` adresleri de kabul edilir ve uygulama bunlari `postgresql+psycopg://...` bicimine cevirir.

sifre icinde `@`, `/`, `#`, `?` gibi URL karakterleri varsa URL encode edilmelidir.

ayni PostgreSQL adresini kullanan terminaller ayni merkezi analiz kayitlarini gorur.

**uyari:** `.env` dosyasini githuba yukleme. icinde veritabani sifresi olabilir.

## saglik kontrolu

uygulama acildiktan sonra:

`http://127.0.0.1:5000/saglik`

ornek sqlite cevabi:

```json
{"durum":"iyi","surum":"0.2.1","veritabani":"bagli","tur":"sqlite"}
```

## test

```powershell
python -m unittest discover -s testler -p 'test_*.py'
```

testler sqlite kullanir. merkezi PostgreSQL baglantisini test etmek icin `.env`yi PostgreSQL adresine ayarlayip `/saglik` endpointini kontrol et.

## github + merkezi veritabani nasil calisir

birinci bilgisayar:

```text
kurt kodu <- github
       |
       +--> merkezi PostgreSQL
```

ikinci bilgisayar:

```text
kurt kodu <- github
       |
       +--> ayni merkezi PostgreSQL
```

kodun guncellenmesi `git pull` ile, ortak verilerin guncellenmesi ise PostgreSQL uzerinden olur.

## surum

`0.2.1`

## lisans

MIT
