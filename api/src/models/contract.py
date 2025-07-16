from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações do contrato
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # civil, trabalhista, comercial, etc.
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)  # Conteúdo do contrato em formato editável
    
    # Metadados
    price = db.Column(db.Float, default=19.90)
    is_premium = db.Column(db.Boolean, default=False)
    popularity_score = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contract {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'content': self.content,
            'price': self.price,
            'is_premium': self.is_premium,
            'popularity_score': self.popularity_score,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserContract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    
    # Conteúdo personalizado pelo usuário
    customized_content = db.Column(db.Text)
    
    # Status da compra/uso
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_downloaded = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<UserContract {self.user_id}-{self.contract_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'contract_id': self.contract_id,
            'customized_content': self.customized_content,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'is_downloaded': self.is_downloaded,
            'download_count': self.download_count
        }

