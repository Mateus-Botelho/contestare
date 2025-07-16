from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Dados do pagamento
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # pix, credit_card, debit_card
    payment_status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, refunded
    
    # Dados específicos do PIX
    pix_key = db.Column(db.String(100))  # 057.195.456-11
    pix_transaction_id = db.Column(db.String(100))
    
    # Dados do cartão (se aplicável)
    card_last_digits = db.Column(db.String(4))
    card_brand = db.Column(db.String(50))
    
    # Referência do que foi comprado
    service_type = db.Column(db.String(50), nullable=False)  # infraction_contest, contract_purchase, premium_plan
    reference_id = db.Column(db.Integer)  # ID da infração, contrato ou plano
    
    # Dados da transação
    transaction_id = db.Column(db.String(100), unique=True)
    gateway_response = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'pix_key': self.pix_key,
            'pix_transaction_id': self.pix_transaction_id,
            'card_last_digits': self.card_last_digits,
            'card_brand': self.card_brand,
            'service_type': self.service_type,
            'reference_id': self.reference_id,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Dados da assinatura
    plan_type = db.Column(db.String(50), nullable=False)  # premium
    status = db.Column(db.String(50), default='active')  # active, cancelled, expired
    
    # Datas
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # Pagamento recorrente
    monthly_amount = db.Column(db.Float, nullable=False)
    auto_renew = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Subscription {self.user_id}-{self.plan_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_type': self.plan_type,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'monthly_amount': self.monthly_amount,
            'auto_renew': self.auto_renew
        }

