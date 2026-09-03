# kurt v0.3.0

kurt, yetkili oldugun web sistemlerinin disaridan gorunen guvenlik ve gorunurluk durumunu inceleyen python tabanli bir purple team aracidir.

## v0.3.0 ne getirdi

artık panelde `https://site-adresi` girerek gercek bir web sistemine tek bir kontrollu HTTP istegi yapabilirsin.

kontroller:

- HTTP durum kodu
- HTTPS kullanimi
- temel guvenlik basliklari
- server ve x-powered-by bilgi sizintisi kontrolu
- TLS sertifika bitis tarihi
- icerik turu ve alinan veri boyutu
- basit gorunurluk puani

bu mod **port taramasi, brute force, exploit, dizin taramasi veya zafiyet istismari yapmaz.** yalnizca tek bir web istegiyle pasif dis gorunurluk kontrolu yapar.

## kullanim

```powershell
git clone https://github.com/edoch1nnn/kurt.git
cd kurt
python -m pip install -r requirements.txt
copy .env.example .env
python main.py
```

sonra:

`http://127.0.0.1:5000`

panelde:

```text
https://example.com
```

gibi bir adres girip `analizi baslat` butonuna bas.

## hedef guvenligi

kurt v0.3.0 yerel, loopback, private, link-local, multicast ve rezerve IP adreslerine erisimi engeller. Yalnizca standart HTTP/HTTPS portlari kabul edilir.

yalnizca sahibi oldugun veya yazili yetkin bulunan sistemleri analiz et. bir sistemi izinsiz otomatik olarak yoklamak yerine ilgili sistem sahibinden izin al.

## veritabani

sqlite tek bilgisayar ve gelistirme icin, postgresql ise ortak runtime verileri icin kullanilabilir.

**github veritabani degildir.** kaynak kodu githubdan, analiz kayitlari ise sqlite veya merkezi postgresql'den gelir.

## saglik kontrolu

`http://127.0.0.1:5000/saglik`

## test

```powershell
python -m unittest discover -s testler -p 'test_*.py'
```

## surum

`0.3.0`

## lisans

MIT
