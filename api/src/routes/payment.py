from flask import Blueprint, jsonify, request, session
from src.models.payment import Payment, Subscription, db
from src.models.user import User
from datetime import datetime, timedelta
import uuid
import random

payment_bp = Blueprint('payment', __name__)

PIX_KEY = "057.195.456-11"

def generate_transaction_id():
    """Gera ID único para transação"""
    return f"TXN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"

def simulate_pix_payment(amount, pix_key):
    """Simula processamento de pagamento PIX"""
    # Simula aprovação automática para demonstração
    return {
        'status': 'approved',
        'transaction_id': f"PIX_{uuid.uuid4().hex[:12].upper()}",
        'message': 'Pagamento PIX aprovado com sucesso'
    }

def simulate_card_payment(amount, card_data):
    """Simula processamento de pagamento com cartão"""
    # Simula aprovação com 90% de chance
    success = random.random() > 0.1
    
    if success:
        return {
            'status': 'approved',
            'transaction_id': f"CARD_{uuid.uuid4().hex[:12].upper()}",
            'message': 'Pagamento aprovado com sucesso'
        }
    else:
        return {
            'status': 'rejected',
            'transaction_id': None,
            'message': 'Pagamento rejeitado - verifique os dados do cartão'
        }

@payment_bp.route('/payment/pix', methods=['POST'])
def process_pix_payment():
    """Processa pagamento via PIX"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        data = request.json
        
        # Validações
        required_fields = ['amount', 'service_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Valor deve ser maior que zero'}), 400
        
        # Criar registro de pagamento
        payment = Payment(
            user_id=session['user_id'],
            amount=amount,
            payment_method='pix',
            service_type=data['service_type'],
            reference_id=data.get('reference_id'),
            transaction_id=generate_transaction_id(),
            pix_key=PIX_KEY
        )
        
        db.session.add(payment)
        db.session.flush()
        
        # Simular processamento PIX
        pix_result = simulate_pix_payment(amount, PIX_KEY)
        
        if pix_result['status'] == 'approved':
            payment.payment_status = 'approved'
            payment.paid_at = datetime.utcnow()
            payment.pix_transaction_id = pix_result['transaction_id']
            
            # Atualizar status do usuário se for plano premium
            if data['service_type'] == 'premium_plan':
                user = User.query.get(session['user_id'])
                user.is_premium = True
                
                # Criar assinatura
                subscription = Subscription(
                    user_id=session['user_id'],
                    plan_type='premium',
                    monthly_amount=amount,
                    end_date=datetime.utcnow() + timedelta(days=30)
                )
                db.session.add(subscription)
        else:
            payment.payment_status = 'rejected'
        
        payment.gateway_response = str(pix_result)
        
        db.session.commit()
        
        return jsonify({
            'message': pix_result['message'],
            'payment': payment.to_dict(),
            'status': pix_result['status']
        }), 200 if pix_result['status'] == 'approved' else 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/payment/card', methods=['POST'])
def process_card_payment():
    """Processa pagamento via cartão"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        data = request.json
        
        # Validações
        required_fields = ['amount', 'service_type', 'card_number', 'card_holder', 'expiry_date', 'cvv']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Valor deve ser maior que zero'}), 400
        
        # Validar número do cartão (básico)
        card_number = data['card_number'].replace(' ', '').replace('-', '')
        if len(card_number) < 13 or len(card_number) > 19:
            return jsonify({'error': 'Número do cartão inválido'}), 400
        
        # Determinar bandeira
        card_brand = 'visa'
        if card_number.startswith('5'):
            card_brand = 'mastercard'
        elif card_number.startswith('4'):
            card_brand = 'visa'
        elif card_number.startswith('3'):
            card_brand = 'amex'
        
        # Criar registro de pagamento
        payment = Payment(
            user_id=session['user_id'],
            amount=amount,
            payment_method='credit_card',
            service_type=data['service_type'],
            reference_id=data.get('reference_id'),
            transaction_id=generate_transaction_id(),
            card_last_digits=card_number[-4:],
            card_brand=card_brand
        )
        
        db.session.add(payment)
        db.session.flush()
        
        # Simular processamento do cartão
        card_result = simulate_card_payment(amount, data)
        
        if card_result['status'] == 'approved':
            payment.payment_status = 'approved'
            payment.paid_at = datetime.utcnow()
            
            # Atualizar status do usuário se for plano premium
            if data['service_type'] == 'premium_plan':
                user = User.query.get(session['user_id'])
                user.is_premium = True
                
                # Criar assinatura
                subscription = Subscription(
                    user_id=session['user_id'],
                    plan_type='premium',
                    monthly_amount=amount,
                    end_date=datetime.utcnow() + timedelta(days=30)
                )
                db.session.add(subscription)
        else:
            payment.payment_status = 'rejected'
        
        payment.gateway_response = str(card_result)
        
        db.session.commit()
        
        return jsonify({
            'message': card_result['message'],
            'payment': payment.to_dict(),
            'status': card_result['status']
        }), 200 if card_result['status'] == 'approved' else 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/payments', methods=['GET'])
def get_user_payments():
    """Lista pagamentos do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    payments = Payment.query.filter_by(user_id=session['user_id']).order_by(
        Payment.created_at.desc()
    ).all()
    
    return jsonify([payment.to_dict() for payment in payments])

@payment_bp.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Obtém detalhes de um pagamento específico"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    payment = Payment.query.filter_by(
        id=payment_id,
        user_id=session['user_id']
    ).first()
    
    if not payment:
        return jsonify({'error': 'Pagamento não encontrado'}), 404
    
    return jsonify(payment.to_dict())

@payment_bp.route('/subscription', methods=['GET'])
def get_user_subscription():
    """Obtém assinatura ativa do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    subscription = Subscription.query.filter_by(
        user_id=session['user_id'],
        status='active'
    ).first()
    
    if not subscription:
        return jsonify({'message': 'Nenhuma assinatura ativa'}), 404
    
    # Verificar se expirou
    if subscription.end_date < datetime.utcnow():
        subscription.status = 'expired'
        user = User.query.get(session['user_id'])
        user.is_premium = False
        db.session.commit()
        return jsonify({'message': 'Assinatura expirada'}), 404
    
    return jsonify(subscription.to_dict())

@payment_bp.route('/subscription/cancel', methods=['POST'])
def cancel_subscription():
    """Cancela assinatura do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        subscription = Subscription.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({'error': 'Nenhuma assinatura ativa encontrada'}), 404
        
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        
        # Manter premium até o fim do período pago
        # user = User.query.get(session['user_id'])
        # user.is_premium = False
        
        db.session.commit()
        
        return jsonify({
            'message': 'Assinatura cancelada com sucesso',
            'subscription': subscription.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/pricing', methods=['GET'])
def get_pricing():
    """Retorna informações de preços"""
    return jsonify({
        'single_contest': {
            'price': 19.90,
            'description': 'Contestação única de infração',
            'features': [
                '1 contestação de infração',
                'Análise jurídica completa',
                'Documento profissional',
                'Suporte por email',
                'Garantia de qualidade'
            ]
        },
        'premium_plan': {
            'price': 69.90,
            'description': 'Plano premium mensal',
            'features': [
                'Contestações ilimitadas',
                'Biblioteca completa de contratos',
                'Suporte prioritário por telefone',
                'Acompanhamento de prazos',
                'Análise jurídica avançada',
                'Relatórios detalhados',
                'Acesso a atualizações legislativas'
            ]
        },
        'pix_key': PIX_KEY
    })

@payment_bp.route('/payment/simulate', methods=['POST'])
def simulate_payment():
    """Endpoint para simular pagamentos em desenvolvimento"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        data = request.json
        
        # Criar pagamento simulado aprovado
        payment = Payment(
            user_id=session['user_id'],
            amount=float(data.get('amount', 19.90)),
            payment_method='pix',
            payment_status='approved',
            service_type=data.get('service_type', 'infraction_contest'),
            reference_id=data.get('reference_id'),
            transaction_id=generate_transaction_id(),
            pix_key=PIX_KEY,
            paid_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        
        # Se for premium, ativar
        if data.get('service_type') == 'premium_plan':
            user = User.query.get(session['user_id'])
            user.is_premium = True
            
            subscription = Subscription(
                user_id=session['user_id'],
                plan_type='premium',
                monthly_amount=payment.amount,
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pagamento simulado com sucesso',
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

