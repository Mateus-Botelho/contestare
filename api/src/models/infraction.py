from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Infraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Dados da infração
    notification_number = db.Column(db.String(50), nullable=False)
    infraction_type = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date_infraction = db.Column(db.DateTime, nullable=False)
    date_notification = db.Column(db.DateTime, nullable=False)
    
    # Dados do veículo
    vehicle_plate = db.Column(db.String(10), nullable=False)
    vehicle_model = db.Column(db.String(100))
    
    # Dados do local
    location = db.Column(db.String(200), nullable=False)
    issuing_agency = db.Column(db.String(100), nullable=False)
    
    # Status e análise
    status = db.Column(db.String(50), default='pending')  # pending, analyzed, contested, resolved
    success_probability = db.Column(db.Float)
    legal_arguments = db.Column(db.Text)
    
    # Arquivos
    notification_file = db.Column(db.String(200))
    contest_document = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Infraction {self.notification_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_number': self.notification_number,
            'infraction_type': self.infraction_type,
            'value': self.value,
            'date_infraction': self.date_infraction.isoformat() if self.date_infraction else None,
            'date_notification': self.date_notification.isoformat() if self.date_notification else None,
            'vehicle_plate': self.vehicle_plate,
            'vehicle_model': self.vehicle_model,
            'location': self.location,
            'issuing_agency': self.issuing_agency,
            'status': self.status,
            'success_probability': self.success_probability,
            'legal_arguments': self.legal_arguments,
            'notification_file': self.notification_file,
            'contest_document': self.contest_document,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

