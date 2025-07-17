import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.infraction import Infraction
from src.models.contract import Contract, UserContract
from src.models.payment import Payment, Subscription

# Importar blueprints
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.infraction import infraction_bp
from src.routes.contract import contract_bp
from src.routes.payment import payment_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'contestare_doc_express_secret_key_2024'

# Habilitar CORS para todas as rotas
from dotenv import load_dotenv
load_dotenv()  # ADICIONAR ESTA LINHA!

import os
print("=== DEBUG CORS ===")
print(f"CORS_ORIGINS raw: {os.getenv('CORS_ORIGINS')}")
cors_origins = os.getenv('CORS_ORIGINS', '').split(',')
print(f"CORS Origins list: {cors_origins}")
print("==================")

CORS(app, origins=cors_origins, supports_credentials=True)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(infraction_bp, url_prefix='/api')
app.register_blueprint(contract_bp, url_prefix='/api')
app.register_blueprint(payment_bp, url_prefix='/api')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Criar tabelas
with app.app_context():
    db.create_all()
    # Inicializar contratos populares
    from src.routes.contract import init_contracts, init_additional_contracts
    init_contracts()
    init_additional_contracts()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da API"""
    return {
        'status': 'healthy',
        'service': 'Contestare Doc Express API',
        'version': '1.0.0'
    }

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

