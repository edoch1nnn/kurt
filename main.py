import os
import logging
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from flask import Flask, jsonify
from sqlalchemy import text

from uygulama import veritabani
from uygulama.yollar import kayit_yollari

load_dotenv()

surum = '0.3.1'
veritabani_adresi = os.getenv('VERITABANI_ADRESI', 'sqlite:///kurt.db').strip()

if veritabani_adresi.startswith('postgres://'):
    veritabani_adresi = 'postgresql+psycopg://' + veritabani_adresi[len('postgres://'):]
elif veritabani_adresi.startswith('postgresql://'):
    veritabani_adresi = 'postgresql+psycopg://' + veritabani_adresi[len('postgresql://'):]

try:
    veritabani_url = make_url(veritabani_adresi)
except Exception as hata:
    raise RuntimeError(
        'VERITABANI_ADRESI okunamadi. SQLite icin sqlite:///kurt.db, PostgreSQL icin '
        'postgresql+psycopg://kullanici:sifre@sunucu:5432/kurt kullan.'
    ) from hata

izinli_semler = {'sqlite', 'postgresql+psycopg'}
if veritabani_url.drivername not in izinli_semler:
    raise RuntimeError(
        'VERITABANI_ADRESI sadece sqlite:///kurt.db veya '
        'postgresql+psycopg://kullanici:sifre@sunucu:5432/kurt olabilir.'
    )

if veritabani_url.drivername == 'postgresql+psycopg' and not veritabani_url.host:
    raise RuntimeError('PostgreSQL adresinde sunucu/host eksik.')

logging.basicConfig(
    level=os.getenv('GUNLUK_SEVIYESI', 'INFO').upper(),
    format='%(asctime)s | kurt | %(levelname)s | %(message)s',
)
gunluk = logging.getLogger('kurt')

uygulama = Flask(__name__, template_folder='sablonlar', static_folder='static')
uygulama.config.update(
    SQLALCHEMY_DATABASE_URI=veritabani_adresi,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv('GIZLI_ANAHTAR', 'kurt-gelisme-anahtari'),
    JSON_SORT_KEYS=False,
)

if veritabani_url.drivername == 'postgresql+psycopg':
    uygulama.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,
    }

veritabani.init_app(uygulama)
kayit_yollari(uygulama, surum)


@uygulama.get('/saglik')
def saglik():
    try:
        veritabani.session.execute(text('SELECT 1'))
        return jsonify({
            'durum': 'iyi',
            'surum': surum,
            'veritabani': 'bagli',
            'tur': 'postgresql' if veritabani_url.drivername == 'postgresql+psycopg' else 'sqlite',
        })
    except SQLAlchemyError as hata:
        veritabani.session.rollback()
        gunluk.exception('veritabani saglik kontrolu basarisiz')
        return jsonify({'durum': 'hata', 'surum': surum, 'veritabani': 'bagli degil', 'hata': str(hata)}), 503


with uygulama.app_context():
    try:
        veritabani.create_all()
        gunluk.info(
            'kurt %s basladi | veritabani=%s',
            surum,
            'postgresql' if veritabani_url.drivername == 'postgresql+psycopg' else 'sqlite',
        )
    except SQLAlchemyError as hata:
        gunluk.exception('veritabani tablolarini olusturma basarisiz')
        raise RuntimeError(f'veritabani baslatilamadi: {hata}') from hata

if __name__ == '__main__':
    uygulama.run(
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
        debug=False,
    )
