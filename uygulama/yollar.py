import json
from flask import jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError
from uygulama import veritabani
from uygulama.modeller import Analiz, Bosluk, Teknik, Telemetri, WebAnalizDetay
from uygulama.hizmetler.analiz import analiz_yap, baslangic_verisi, TEMEL_TELEMETRI
from uygulama.hizmetler.ai_oneriler import ai_onerileri_getir
from uygulama.hizmetler.web_analiz import WebAnalizHatasi, web_analizi_yap


def _hata(mesaj, kod=400):
    veritabani.session.rollback()
    return jsonify({'basarili': False, 'hata': mesaj}), kod


def kayit_yollari(uygulama, surum='0.3.1'):
    @uygulama.get('/')
    def ana_sayfa():
        baslangic_verisi()
        analizler = Analiz.query.order_by(Analiz.tarih.desc()).limit(8).all()
        return render_template('panel.html', analizler=analizler, surum=surum)

    @uygulama.get('/teknikler')
    def teknikler():
        baslangic_verisi()
        return render_template('teknikler.html', teknikler=Teknik.query.order_by(Teknik.teknik_id).all(), surum=surum)

    @uygulama.get('/tespitler')
    def tespitler():
        son_analiz = Analiz.query.order_by(Analiz.tarih.desc()).first()
        liste = Bosluk.query.filter_by(analiz_id=son_analiz.id).order_by(Bosluk.id.desc()).all() if son_analiz else []
        detay = WebAnalizDetay.query.filter_by(analiz_id=son_analiz.id).first() if son_analiz else None
        veri = json.loads(detay.veri) if detay else {}
        return render_template('tespitler.html', tespitler=liste, detay=veri, son_analiz=son_analiz, surum=surum)

    @uygulama.get('/bosluklar')
    def eski_bosluklar():
        return tespitler()

    @uygulama.get('/telemetri')
    def telemetri():
        baslangic_verisi()
        return render_template('telemetri.html', telemetriler=Telemetri.query.order_by(Telemetri.ad).all(), surum=surum)

    @uygulama.post('/api/web-analiz')
    def api_web_analiz():
        veri = request.get_json(silent=True)
        if not isinstance(veri, dict):
            return _hata('json govdesi gerekli')
        adres = veri.get('adres', '')
        if not isinstance(adres, str) or not adres.strip():
            return _hata('analiz edilecek url gerekli')
        try:
            bulgular = web_analizi_yap(adres.strip())
            durum = 'iyi' if bulgular['puan'] >= 85 else 'iyilestirilmeli' if bulgular['puan'] >= 60 else 'kritik'
            analiz = Analiz(
                ad=f'web: {bulgular["adres"]}',
                skor=bulgular['puan'],
                durum=durum,
                telemetri_skoru=100 if bulgular['https'] else 50,
                tespit_skoru=bulgular['puan'],
                korelasyon_skoru=100 if len(bulgular['bulgular']) <= 2 else 60,
                gorunurluk_skoru=bulgular['puan'],
            )
            veritabani.session.add(analiz)
            veritabani.session.flush()

            ai = ai_onerileri_getir(bulgular)
            ai_map = {x['kod']: x['onerme'] for x in ai['oncelikler']}
            for bulgu in bulgular['bulgular']:
                onerme = ai_map.get(bulgu['kod'], bulgu['onerme'])
                veritabani.session.add(Bosluk(
                    teknik=bulgu['kod'],
                    ad=bulgu['baslik'],
                    seviye=bulgu['seviye'],
                    tur='web',
                    onerme=onerme,
                    analiz_id=analiz.id,
                ))

            kayit = dict(bulgular)
            kayit['ai'] = ai
            veritabani.session.add(WebAnalizDetay(
                analiz_id=analiz.id,
                veri=json.dumps(kayit, ensure_ascii=False),
            ))
            veritabani.session.commit()
            return jsonify({
                'basarili': True,
                'id': analiz.id,
                'skor': round(bulgular['puan'], 2),
                'durum': durum,
                'bulgular': kayit,
                'not': 'bu mod tek bir kontrollu web istegi ve dusuk etkili dns gorunum kontrolleri yapar.',
            })
        except WebAnalizHatasi as hata:
            return _hata(str(hata), 400)
        except (SQLAlchemyError, RuntimeError, TypeError, ValueError) as hata:
            return _hata(f'web analizi kaydedilemedi: {hata}', 500)

    @uygulama.get('/api/tespitler')
    def api_tespitler():
        son_analiz = Analiz.query.order_by(Analiz.tarih.desc()).first()
        if not son_analiz:
            return jsonify({'basarili': True, 'analiz': None, 'tespitler': [], 'detay': {}})
        detay = WebAnalizDetay.query.filter_by(analiz_id=son_analiz.id).first()
        veri = json.loads(detay.veri) if detay else {}
        tespitler = Bosluk.query.filter_by(analiz_id=son_analiz.id).order_by(Bosluk.id.desc()).all()
        return jsonify({
            'basarili': True,
            'analiz': {
                'id': son_analiz.id,
                'ad': son_analiz.ad,
                'skor': son_analiz.skor,
                'durum': son_analiz.durum,
                'tarih': son_analiz.tarih.isoformat() if son_analiz.tarih else None,
            },
            'tespitler': [
                {'kod': x.teknik, 'ad': x.ad, 'seviye': x.seviye, 'tur': x.tur, 'onerme': x.onerme}
                for x in tespitler
            ],
            'detay': veri,
        })

    @uygulama.post('/api/analiz')
    def api_analiz():
        veri = request.get_json(silent=True)
        if not isinstance(veri, dict):
            return _hata('json govdesi gerekli')
        ad = veri.get('ad', 'adsiz analiz')
        if not isinstance(ad, str) or not ad.strip():
            return _hata('analiz adi bos olamaz')
        try:
            analiz = analiz_yap(ad, veri.get('telemetri', TEMEL_TELEMETRI), veri.get('tespitler', []))
            return jsonify({'basarili': True, 'surum': surum, 'id': analiz.id, 'skor': round(analiz.skor, 2), 'durum': analiz.durum})
        except (SQLAlchemyError, RuntimeError) as hata:
            return _hata(f'analiz basarisiz: {hata}', 500)

    @uygulama.get('/api/istatistik')
    def api_istatistik():
        try:
            baslangic_verisi()
            analizler = Analiz.query.all()
            son_analiz = Analiz.query.order_by(Analiz.tarih.desc()).first()
            bosluk_sayisi = Bosluk.query.filter_by(analiz_id=son_analiz.id).count() if son_analiz else 0
            return jsonify({
                'surum': surum,
                'analiz': len(analizler),
                'teknik': Teknik.query.count(),
                'bosluk': bosluk_sayisi,
                'telemetri': Telemetri.query.count(),
                'ortalama': round(sum(x.skor for x in analizler) / len(analizler), 2) if analizler else 0,
            })
        except SQLAlchemyError as hata:
            return _hata(f'istatistik okunamadi: {hata}', 500)
