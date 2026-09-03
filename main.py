import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from flask import Flask
from uygulama import veritabani
from uygulama.yollar import kayit_yollari

load_dotenv()

veritabani_adresi = os.getenv('VERITABANI_ADRESI', '').strip()

if veritabani_adresi.startswith('postgres://'):
    veritabani_adresi = 'postgresql+psycopg://' + veritabani_adresi[len('postgres://'):]
elif veritabani_adresi.startswith('postgresql://'):
    veritabani_adresi = 'postgresql+psycopg://' + veritabani_adresi[len('postgresql://'):]

if not veritabani_adresi:
    raise RuntimeError('VERITABANI_ADRESI tanimli degil .env dosyasini doldur')

parcalanmis = urlparse(veritabani_adresi)
if parcalanmis.scheme != 'postgresql+psycopg' or not parcalanmis.hostname:
    raise RuntimeError('VERITABANI_ADRESI gecersiz postgresql+psycopg://kullanici:sifre@sunucu:5432/veritabani biciminde olmali')

uygulama = Flask(__name__, template_folder='sablonlar', static_folder='static')
uygulama.config['SQLALCHEMY_DATABASE_URI'] = veritabani_adresi
uygulama.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
uygulama.config['SECRET_KEY'] = os.getenv('GIZLI_ANAHTAR', 'kurt-gelisme-anahtari')
veritabani.init_app(uygulama)
kayit_yollari(uygulama)

with uygulama.app_context():
    veritabani.create_all()

if __name__ == '__main__':
    uygulama.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
