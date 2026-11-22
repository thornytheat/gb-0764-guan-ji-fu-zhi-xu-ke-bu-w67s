from flask import Flask
from app.problem import DeskError
from app.routes import rights
from app.settings import LEDGER
from app.vault.database import Vault
from app.desk import desk


def create_app(path=LEDGER):
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config['MAX_CONTENT_LENGTH'] = 1024*1024
    app.vault = Vault(path)
    app.register_blueprint(rights)
    app.register_blueprint(desk)

    @app.errorhandler(DeskError)
    def problem(exc):
        return {'error':exc.code,'message':str(exc)},exc.status

    @app.get('/healthz')
    def health():
        return {'status':'ok'}

    return app
