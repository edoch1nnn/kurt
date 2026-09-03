# kurt v0.2.0

kurt guvenlik yiginindaki tespit ve gorunurluk bosluklarini analiz eden python tabanli bir purple team aracidir

## nasil calisir

githubdan projeyi alirsin python bagimliliklarini kurarsin `.env` dosyasina merkezi postgresql adresini yazarsin sonra `python main.py` dersin tarayicida `127.0.0.1:5000` acilir

veriler bilgisayara degil tanimladigin merkezi postgresql veritabanina kaydedilir bu nedenle ayni veritabani adresini kullanan farkli bilgisayarlar ayni analiz teknik telemetri ve bosluk verilerini gorur

## kurulum

```powershell
git clone https://github.com/edoch1nnn/kurt.git
cd kurt
python -m pip install -r requirements.txt
copy .env.example .env
```

`.env` dosyasini acip `VERITABANI_ADRESI` ve `GIZLI_ANAHTAR` degerlerini doldur

```powershell
python main.py
```

sonra tarayicidan `http://127.0.0.1:5000` adresine gir

## veritabani adresi

kurt `postgresql://` ve `postgres://` adreslerini otomatik olarak `postgresql+psycopg://` bicimine cevirir

ornek:

`postgresql+psycopg://kullanici:sifre@sunucu:5432/kurt`

sifrede `@`, `#`, `:` gibi ozel karakterler varsa url kodlamasi kullan

veritabani adresini githuba yukleme `.env` dosyasini repoya koyma

## kapsam

- mitre att&ck tekniklerinin kapsamini puanlama
- telemetri eksigi bulma
- tespit eksigi bulma
- korelasyon eksigi bulma
- merkezi analiz kaydi
- telemetri kaynaklari
- tespit bosluklari
- yerel web arayuzu

## lisans

MIT
