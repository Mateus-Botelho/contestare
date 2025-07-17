from src.main import app
with app.app_context():
    from src.models.user import db
    db.create_all()
    print('✅ Banco criado!')
