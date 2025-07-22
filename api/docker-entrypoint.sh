#!/bin/bash
set -e

echo "🚀 Iniciando Contestare Doc Express..."

# Verificar se pasta do banco existe
if [ ! -d "/app/src/database" ]; then
    echo "📁 Criando diretório do banco de dados..."
    mkdir -p /app/src/database
fi

# Verificar/criar banco de dados
if [ ! -f "/app/src/database/contestare.db" ]; then
    echo "🗄️ Criando banco de dados..."
    python -c "
from src.main import app
with app.app_context():
    from src.models.user import db
    db.create_all()
    print('✅ Banco de dados criado com sucesso!')
"
else
    echo "✅ Banco de dados já existe"
fi

# Verificar se banco está funcionando
echo "🔍 Verificando integridade do banco..."
python -c "
from src.main import app
with app.app_context():
    from src.models.user import db
    try:
        db.engine.execute('SELECT 1')
        print('✅ Banco de dados funcionando!')
    except Exception as e:
        print(f'❌ Erro no banco: {e}')
        exit(1)
"

echo "🌟 Contestare Doc Express iniciado com sucesso!"
exec "$@"