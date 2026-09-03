import ipaddress
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


class WebAnalizHatasi(ValueError):
    pass


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

    for _, _, _, _, sockaddr in adresler:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise WebAnalizHatasi('yerel veya ozel ip adreslerine erisim engellendi.')
    return adres


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


def web_analizi_yap(adres, zaman_asimi=8):
    adres = _url_dogrula(adres)
    istek = urllib.request.Request(
        adres,
        headers={'User-Agent': 'Kurt/0.3.0 (authorized security visibility assessment)'},
        method='GET',
    )
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as cevap:
            basliklar = dict(cevap.headers.items())
            durum_kodu = cevap.status
            son_url = cevap.geturl()
            govde = cevap.read(65536)
    except urllib.error.HTTPError as hata:
        basliklar = dict(hata.headers.items())
        durum_kodu = hata.code
        son_url = hata.geturl()
        govde = hata.read(65536)
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as hata:
        raise WebAnalizHatasi(f'hedefe baglanilamadi: {hata}') from hata

    son_parca = urllib.parse.urlparse(son_url)
    if son_parca.hostname and son_parca.hostname != urllib.parse.urlparse(adres).hostname:
        # urllib redirect yaptiysa ikinci hedefi de ayni guvenli kontrollerden gecir.
        _url_dogrula(son_url)

    basliklar_kucuk = {k.lower(): v for k, v in basliklar.items()}
    guvenlik_basliklari = _guvenlik_basliklari(basliklar)
    https = urllib.parse.urlparse(adres).scheme == 'https'
    puan = 0
    if 200 <= durum_kodu < 400:
        puan += 25
    if https:
        puan += 25
    puan += min(40, len(guvenlik_basliklari) * 40 / 6)
    if 'server' not in basliklar_kucuk:
        puan += 5
    if 'x-powered-by' not in basliklar_kucuk:
        puan += 5
    puan = round(min(100, puan), 1)

    tls_bilgisi = None
    if https:
        try:
            ana_makine = urllib.parse.urlparse(adres).hostname
            with socket.create_connection((ana_makine, 443), timeout=zaman_asimi) as soket:
                with ssl.create_default_context().wrap_socket(soket, server_hostname=ana_makine) as tls:
                    sertifika = tls.getpeercert()
                    bitis = sertifika.get('notAfter')
                    if bitis:
                        bitis_tarihi = datetime.strptime(bitis, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
                        tls_bilgisi = {'sertifika_bitis': bitis_tarihi.isoformat(), 'gun': max(0, (bitis_tarihi - datetime.now(timezone.utc)).days)}
        except (OSError, ssl.SSLError, ValueError):
            tls_bilgisi = {'sertifika_bitis': None, 'gun': None}

    return {
        'adres': adres,
        'son_url': son_url,
        'durum_kodu': durum_kodu,
        'icerik_turu': basliklar_kucuk.get('content-type', 'bilinmiyor'),
        'icerik_bayt': len(govde),
        'https': https,
        'guvenlik_basliklari': guvenlik_basliklari,
        'tls': tls_bilgisi,
        'puan': puan,
        'zaman': datetime.now(timezone.utc).isoformat(),
    }
