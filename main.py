import os
from flask import Flask
from uygulama import veritabani
from uygulama.yollar import kayit_yollari

uygulama = Flask(__name__, template_folder='sablonlar', static_folder='static')
uygulama.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('VERITABANI_ADRESI', '')
uygulama.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
uygulama.config['GIZLI_ANAHTAR'] = os.getenv('GIZLI_ANAHTAR', 'kurt-gelisme-anahtari')
veritabani.init_app(uygulama)
kayit_yollari(uygulama)

with uygulama.app_context():
    if not uygulama.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError('VERITABANI_ADRESI tanimli degil')
    veritabani.create_all()

if __name__ == '__main__':
    uygulama.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
