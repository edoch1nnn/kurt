# kurt

kurt guvenlik yiginindaki tespit ve gorunurluk bosluklarini analiz eden python tabanli bir purple team aracidir

## nasil calisir

githubdan projeyi alirsin python bagimliliklarini kurarsin merkezi postgresql adresini ortama tanimlarsin sonra `python main.py` dersin tarayicida `127.0.0.1:5000` acilir

veriler bilgisayara degil tanimladigin merkezi postgresql veritabanina kaydedilir bu nedenle ayni veritabani adresini kullanan farkli bilgisayarlar ayni analiz teknik telemetri ve bosluk verilerini gorur

## kurulum

```bash
git clone https://github.com/edoch1nnn/kurt.git
cd kurt
python -m pip install -r requirements.txt
```

`.env.example` dosyasini temel alip `VERITABANI_ADRESI` ve `GIZLI_ANAHTAR` degerlerini ayarla

```bash
python main.py
```

sonra tarayicidan `http://127.0.0.1:5000` adresine gir

## merkezi veritabani

kurtun ortak veri mantigi github uzerinden degil postgresql uzerinden calisir github sadece kaynak kodu tasir

postgresql sunucunun internetten erisilebilir olmasi ve dis baglantilara izin vermesi gerekir

ornek adres:

`postgresql+psycopg://kullanici:sifre@sunucu:5432/kurt`

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
