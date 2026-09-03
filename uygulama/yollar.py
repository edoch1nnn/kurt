from flask import jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError
from uygulama import veritabani
from uygulama.modeller import Analiz, Bosluk, Teknik, Telemetri
from uygulama.hizmetler.analiz import analiz_yap, baslangic_verisi, TEMEL_TELEMETRI

def _hata(mesaj, kod=400):
    veritabani.session.rollback()
    return jsonify({'basarili': False, 'hata': mesaj}), kod

def kayit_yollari(uygulama, surum='0.2.1'):
    @uygulama.get('/')
    def ana_sayfa():
        baslangic_verisi()
        analizler = Analiz.query.order_by(Analiz.tarih.desc()).limit(8).all()
        return render_template('panel.html', analizler=analizler, surum=surum)

    @uygulama.get('/teknikler')
    def teknikler():
        baslangic_verisi()
        return render_template('teknikler.html', teknikler=Teknik.query.order_by(Teknik.teknik_id).all(), surum=surum)

    @uygulama.get('/bosluklar')
    def bosluklar():
        son_analiz = Analiz.query.order_by(Analiz.tarih.desc()).first()
        liste = Bosluk.query.filter_by(analiz_id=son_analiz.id).order_by(Bosluk.id.desc()).all() if son_analiz else []
        return render_template('bosluklar.html', bosluklar=liste, son_analiz=son_analiz, surum=surum)

    @uygulama.get('/telemetri')
    def telemetri():
        baslangic_verisi()
        return render_template('telemetri.html', telemetriler=Telemetri.query.order_by(Telemetri.ad).all(), surum=surum)

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
