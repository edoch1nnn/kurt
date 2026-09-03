import ipaddress
import json
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

try:
    import dns.resolver
except ImportError:
    dns = None


class WebAnalizHatasi(ValueError):
    pass


class _YonlendirmeYok(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_acikici = urllib.request.build_opener(_YonlendirmeYok)


def _url_dogrula(adres):
    adres = str(adres or '').strip()
    parca = urllib.parse.urlparse(adres)
    if parca.scheme not in {'http', 'https'} or not parca.hostname:
        raise WebAnalizHatasi('gecerli bir http:// veya https:// adresi gir.')
    if parca.username or parca.password:
        raise WebAnalizHatasi('url icinde kullanici adi veya sifre kullanilamaz.')
    try:
        port = parca.port
    except ValueError as hata:
        raise WebAnalizHatasi('url portu gecersiz.') from hata
    if port not in (None, 80, 443):
        raise WebAnalizHatasi('guvenli modda yalnizca standart web portlari kullanilir.')
    try:
        adresler = socket.getaddrinfo(parca.hostname, port or (443 if parca.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as hata:
        raise WebAnalizHatasi('hedef adres cozumlenemedi.') from hata
    ipler = []
    for _, _, _, _, sockaddr in adresler:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise WebAnalizHatasi('yerel veya ozel ip adreslerine erisim engellendi.')
        ipler.append(str(ip))
    return adres, sorted(set(ipler))


def _guvenlik_basliklari(basliklar):
    beklenen = {
        'strict-transport-security': 'https zorlamasi',
        'content-security-policy': 'icerik guvenlik politikasi',
        'x-content-type-options': 'mime turu korumasi',
        'x-frame-options': 'cerceveleme korumasi',
        'referrer-policy': 'referrer politikasi',
        'permissions-policy': 'tarayici izin politikasi',
    }
    bulunan = {k.lower(): v for k, v in basliklar.items()}
    return [ad for anahtar, ad in beklenen.items() if anahtar in bulunan]


def _cerez_bulgulari(basliklar):
    sonuc = []
    for satir in basliklar.get_all('Set-Cookie', []):
        kucuk = satir.lower()
        sonuc.append({'secure': 'secure' in kucuk, 'httponly': 'httponly' in kucuk, 'samesite': 'samesite=' in kucuk})
    return sonuc


def _alan_adi(ana_makine):
    return ana_makine[4:] if ana_makine.startswith('www.') else ana_makine


def _sertifika_alanlari(sertifika):
    san = []
    for tur, deger in sertifika.get('subjectAltName', ()):
        if tur == 'DNS':
            san.append(deger.lower())
    return sorted(set(san))


def _tls_kontrol(adres, zaman_asimi):
    ana_makine = urllib.parse.urlparse(adres).hostname
    try:
        with socket.create_connection((ana_makine, 443), timeout=zaman_asimi) as soket:
            with ssl.create_default_context().wrap_socket(soket, server_hostname=ana_makine) as tls:
                sertifika = tls.getpeercert()
                bitis = sertifika.get('notAfter')
                bitis_tarihi = datetime.strptime(bitis, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc) if bitis else None
                konu = ', '.join('='.join(x) for grup in sertifika.get('subject', ()) for x in grup)
                veren = ', '.join('='.join(x) for grup in sertifika.get('issuer', ()) for x in grup)
                return {
                    'sertifika_bitis': bitis_tarihi.isoformat() if bitis_tarihi else None,
                    'sertifika_baslangic': datetime.strptime(sertifika['notBefore'], '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc).isoformat() if sertifika.get('notBefore') else None,
                    'gun': max(0, (bitis_tarihi - datetime.now(timezone.utc)).days) if bitis_tarihi else None,
                    'surum': tls.version(),
                    'sifre': tls.cipher()[0] if tls.cipher() else None,
                    'konu': konu or None,
                    'veren': veren or None,
                    'san': _sertifika_alanlari(sertifika),
                }
    except (OSError, ssl.SSLError, ValueError):
        return {'sertifika_bitis': None, 'sertifika_baslangic': None, 'gun': None, 'surum': None, 'sifre': None, 'konu': None, 'veren': None, 'san': []}


def _dns_kontrol(alan_adi):
    sonuc = {'a': [], 'aaaa': [], 'cname': [], 'mx': [], 'ns': [], 'txt': []}
    if dns is None:
        return sonuc
    for tur in sonuc:
        try:
            cevap = dns.resolver.resolve(alan_adi, tur, lifetime=3)
            if tur == 'mx':
                sonuc[tur] = sorted(str(x.exchange).rstrip('.') for x in cevap)
            elif tur == 'txt':
                sonuc[tur] = sorted(''.join(x.decode('utf-8', errors='replace') for x in r.strings) for r in cevap)
            else:
                sonuc[tur] = sorted(str(x).rstrip('.') for x in cevap)
        except Exception:
            sonuc[tur] = []
    return sonuc


def _servisler(basliklar, dns_bilgisi, html):
    bulunan = []
    server = basliklar.get('server')
    powered = basliklar.get('x-powered-by')
    if server:
        bulunan.append({'ad': server, 'kaynak': 'server basligi', 'guven': 95})
    if powered:
        bulunan.append({'ad': powered, 'kaynak': 'x-powered-by basligi', 'guven': 95})
    birlesik = ' '.join(str(x).lower() for x in basliklar.values()) + ' ' + html.lower()
    imzalar = [
        ('cloudflare', ['cf-ray', 'cf-cache-status', 'cloudflare'], 'http'),
        ('nginx', ['nginx'], 'http'),
        ('apache', ['apache'], 'http'),
        ('iis', ['microsoft-iis'], 'http'),
        ('next.js', ['__next_data__', '/_next/'], 'html'),
        ('wordpress', ['wp-content', 'wp-includes'], 'html'),
    ]
    for ad, anahtarlar, kaynak in imzalar:
        if any(x in birlesik for x in anahtarlar) and not any(x['ad'].lower() == ad for x in bulunan):
            bulunan.append({'ad': ad, 'kaynak': kaynak, 'guven': 82})
    mx = ' '.join(dns_bilgisi.get('mx', [])).lower()
    if 'outlook.com' in mx or 'microsoft' in mx:
        bulunan.append({'ad': 'microsoft 365 mail', 'kaynak': 'mx', 'guven': 88})
    if 'google.com' in mx or 'googlemail.com' in mx:
        bulunan.append({'ad': 'google workspace mail', 'kaynak': 'mx', 'guven': 88})
    return bulunan


def web_analizi_yap(adres, zaman_asimi=8):
    adres, ipler = _url_dogrula(adres)
    istek = urllib.request.Request(adres, headers={'User-Agent': 'Kurt security visibility assessment'}, method='GET')
    baslangic = time.perf_counter()
    try:
        with _acikici.open(istek, timeout=zaman_asimi) as cevap:
            basliklar = cevap.headers
            durum_kodu = cevap.status
            son_url = cevap.geturl()
            govde = cevap.read(65536)
    except urllib.error.HTTPError as hata:
        basliklar = hata.headers
        durum_kodu = hata.code
        son_url = hata.geturl()
        govde = hata.read(65536)
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as hata:
        raise WebAnalizHatasi(f'hedefe baglanilamadi: {hata}') from hata
    gecen_ms = round((time.perf_counter() - baslangic) * 1000, 1)
    konum = basliklar.get('Location')
    yonlendirme = urllib.parse.urljoin(adres, konum) if konum else None
    if yonlendirme:
        try:
            _url_dogrula(yonlendirme)
        except WebAnalizHatasi:
            yonlendirme = None
    basliklar_kucuk = {k.lower(): v for k, v in basliklar.items()}
    guvenlik_basliklari = _guvenlik_basliklari(basliklar)
    cerezler = _cerez_bulgulari(basliklar)
    https = urllib.parse.urlparse(adres).scheme == 'https'
    tls_bilgisi = _tls_kontrol(adres, zaman_asimi) if https else None
    alan_adi = urllib.parse.urlparse(adres).hostname
    kok_alan = _alan_adi(alan_adi)
    dns_bilgisi = _dns_kontrol(kok_alan)
    html = govde.decode('utf-8', errors='ignore')
    servisler = _servisler(basliklar, dns_bilgisi, html)
    subdomainler = []
    if tls_bilgisi:
        for ad in tls_bilgisi.get('san', []):
            temiz = ad.lstrip('*.')
            if temiz.endswith('.' + kok_alan) and temiz != kok_alan:
                subdomainler.append(temiz)
    subdomainler = sorted(set(subdomainler))

    puan = 0.0
    if 200 <= durum_kodu < 400:
        puan += 20
    if https:
        puan += 25
    puan += min(35, len(guvenlik_basliklari) * 35 / 6)
    if 'server' not in basliklar_kucuk:
        puan += 5
    if 'x-powered-by' not in basliklar_kucuk:
        puan += 5
    if not cerezler or all(x['secure'] and x['httponly'] and x['samesite'] for x in cerezler):
        puan += 10
    puan = round(min(100, puan), 1)

    bulgular = []
    if not https:
        bulgular.append({'kod': 'WEB-001', 'seviye': 'yuksek', 'baslik': 'https etkin degil', 'aciklama': 'iletisim sifrelenmiyor olabilir.', 'onerme': 'https ve guvenli yonlendirme kullan.'})
    eksik = [x for x in ('https zorlamasi', 'icerik guvenlik politikasi', 'mime turu korumasi', 'cerceveleme korumasi', 'referrer politikasi', 'tarayici izin politikasi') if x not in guvenlik_basliklari]
    for sira, ad in enumerate(eksik, 1):
        bulgular.append({'kod': f'WEB-{sira+1:03d}', 'seviye': 'orta', 'baslik': f'eksik guvenlik basligi: {ad}', 'aciklama': 'tarayici guvenlik katmani gelistirilebilir.', 'onerme': 'uygun http guvenlik basligini ekle ve politikasini ortamina gore ayarla.'})
    if 'server' in basliklar_kucuk or 'x-powered-by' in basliklar_kucuk:
        bulgular.append({'kod': 'WEB-010', 'seviye': 'dusuk', 'baslik': 'sunucu bilgisi gorunuyor', 'aciklama': 'yanit basliklari teknoloji bilgisi aciga cikariyor olabilir.', 'onerme': 'gereksiz Server ve X-Powered-By bilgisini kaldir.'})
    for i, cerez in enumerate(cerezler, 1):
        if not cerez['secure'] or not cerez['httponly'] or not cerez['samesite']:
            bulgular.append({'kod': f'WEB-02{i}', 'seviye': 'orta', 'baslik': 'cerez guvenlik nitelikleri eksik', 'aciklama': f'{i}. cerez beklenen guvenlik niteliklerinin tamamini tasimiyor.', 'onerme': 'oturum cerezlerinde Secure, HttpOnly ve uygun SameSite politikasini kullan.'})
            break
    if tls_bilgisi and tls_bilgisi['gun'] is not None and tls_bilgisi['gun'] <= 30:
        bulgular.append({'kod': 'TLS-001', 'seviye': 'yuksek' if tls_bilgisi['gun'] <= 7 else 'orta', 'baslik': 'sertifika yakinda sona eriyor', 'aciklama': f'sertifikanin yaklasik {tls_bilgisi["gun"]} gun omru kalmis.', 'onerme': 'sertifikayi zamaninda yenile.'})
    if tls_bilgisi and tls_bilgisi.get('san'):
        bulgular.append({'kod': 'TLS-010', 'seviye': 'bilgi', 'baslik': 'sertifikada ek alan adlari bulundu', 'aciklama': f'{len(tls_bilgisi["san"])} adet SAN kaydi goruldu.', 'onerme': 'sertifikadaki alan adlarini aktif envanterinle karsilastir ve kullanilmayanlari sonraki yenilemede temizle.'})
    if dns_bilgisi.get('txt') and not any('v=spf1' in x.lower() for x in dns_bilgisi['txt']):
        bulgular.append({'kod': 'DNS-001', 'seviye': 'orta', 'baslik': 'spf kaydi bulunamadi', 'aciklama': 'kok alan adinda SPF kaydi tespit edilemedi.', 'onerme': 'mail gonderen sunucularini belirleyip uygun bir SPF politikasi tanimla.'})
    if dns_bilgisi.get('txt') and not any('v=dmarc1' in x.lower() for x in dns_bilgisi['txt']):
        bulgular.append({'kod': 'DNS-002', 'seviye': 'orta', 'baslik': 'dmarc kaydi bulunamadi', 'aciklama': 'kok alan adinda DMARC kaydi tespit edilemedi.', 'onerme': 'mail altyapini kontrol edip uygun bir DMARC politikasi olustur.'})
    if yonlendirme:
        bulgular.append({'kod': 'WEB-020', 'seviye': 'bilgi', 'baslik': 'yonlendirme bulundu', 'aciklama': 'hedef bir Location yaniti dondu.', 'onerme': 'yonlendirme hedefinin de beklenen TLS ve guvenlik politikalarini uyguladigini kontrol et.'})

    return {
        'adres': adres,
        'son_url': son_url,
        'yonlendirme': yonlendirme,
        'ipler': ipler,
        'alan_adi': alan_adi,
        'kok_alan': kok_alan,
        'subdomainler': subdomainler,
        'dns': dns_bilgisi,
        'durum_kodu': durum_kodu,
        'icerik_turu': basliklar_kucuk.get('content-type', 'bilinmiyor'),
        'icerik_bayt': len(govde),
        'yanit_suresi_ms': gecen_ms,
        'https': https,
        'guvenlik_basliklari': guvenlik_basliklari,
        'cerezler': cerezler,
        'sunucu': basliklar_kucuk.get('server'),
        'x_powered_by': basliklar_kucuk.get('x-powered-by'),
        'servisler': servisler,
        'teknolojiler': servisler,
        'sertifika': tls_bilgisi,
        'tls': tls_bilgisi,
        'puan': puan,
        'bulgular': bulgular,
        'zaman': datetime.now(timezone.utc).isoformat(),
    }
