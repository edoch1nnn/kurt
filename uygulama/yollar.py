from flask import jsonify, render_template, request
from uygulama import veritabani
from uygulama.modeller import Analiz, Bosluk, Teknik, Telemetri
from uygulama.hizmetler.analiz import analiz_yap, baslangic_verisi, TEMEL_TELEMETRI

def kayit_yollari(uygulama):
    @uygulama.get('/')
    def ana_sayfa():
        baslangic_verisi()
        analizler = Analiz.query.order_by(Analiz.tarih.desc()).limit(8).all()
        return render_template('panel.html', analizler=analizler)

    @uygulama.get('/teknikler')
    def teknikler():
        baslangic_verisi()
        return render_template('teknikler.html', teknikler=Teknik.query.order_by(Teknik.teknik_id).all())

    @uygulama.get('/bosluklar')
    def bosluklar():
        return render_template('bosluklar.html', bosluklar=Bosluk.query.order_by(Bosluk.id.desc()).all())

    @uygulama.get('/telemetri')
    def telemetri():
        baslangic_verisi()
        return render_template('telemetri.html', telemetriler=Telemetri.query.order_by(Telemetri.ad).all())

    @uygulama.post('/api/analiz')
    def api_analiz():
        veri = request.get_json(silent=True) or {}
        analiz = analiz_yap(veri.get('ad'), veri.get('telemetri', TEMEL_TELEMETRI), veri.get('tespitler', []))
        return jsonify({'basarili': True, 'id': analiz.id, 'skor': round(analiz.skor, 2), 'durum': analiz.durum})

    @uygulama.get('/api/istatistik')
    def api_istatistik():
        baslangic_verisi()
        analizler = Analiz.query.all()
        return jsonify({'analiz': len(analizler), 'teknik': Teknik.query.count(), 'bosluk': Bosluk.query.count(), 'telemetri': Telemetri.query.count(), 'ortalama': round(sum(x.skor for x in analizler) / len(analizler), 2) if analizler else 0})
