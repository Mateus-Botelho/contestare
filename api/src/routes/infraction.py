from flask import Blueprint, jsonify, request, session
from src.models.infraction import Infraction, db
from src.models.user import User
from datetime import datetime, timedelta
import os
import uuid
import random

infraction_bp = Blueprint('infraction', __name__)

def analyze_infraction(infraction_data):
    """
    Simula análise jurídica baseada no CTB, CDC e Código Civil
    """
    arguments = []
    success_probability = 0
    
    # Análise baseada no tipo de infração
    infraction_type = infraction_data.get('infraction_type', '').lower()
    
    if 'velocidade' in infraction_type:
        arguments.append("Possível erro na calibração do equipamento de medição")
        arguments.append("Verificação da sinalização adequada no local")
        arguments.append("Análise da margem de erro do radar")
        success_probability += 25
    
    if 'estacionamento' in infraction_type:
        arguments.append("Verificação da sinalização de proibição")
        arguments.append("Análise do horário de funcionamento da restrição")
        arguments.append("Competência do agente autuador")
        success_probability += 30
    
    if 'semaforo' in infraction_type or 'sinal' in infraction_type:
        arguments.append("Verificação do funcionamento do semáforo")
        arguments.append("Análise da visibilidade da sinalização")
        arguments.append("Tempo de amarelo adequado conforme CTB")
        success_probability += 20
    
    # Análise de prazos (CDC)
    date_infraction = datetime.fromisoformat(infraction_data.get('date_infraction'))
    date_notification = datetime.fromisoformat(infraction_data.get('date_notification'))
    
    days_diff = (date_notification - date_infraction).days
    
    if days_diff > 30:
        arguments.append("Notificação fora do prazo legal de 30 dias (Art. 280 CTB)")
        success_probability += 40
    
    if days_diff > 60:
        arguments.append("Violação grave do prazo de notificação")
        success_probability += 20
    
    # Análise do órgão autuador
    issuing_agency = infraction_data.get('issuing_agency', '').lower()
    
    if 'municipal' in issuing_agency and 'rodovia' in infraction_data.get('location', '').lower():
        arguments.append("Possível incompetência do órgão municipal em rodovia estadual/federal")
        success_probability += 35
    
    # Análise de valor (CDC - Direito do Consumidor)
    value = float(infraction_data.get('value', 0))
    
    if value > 1000:
        arguments.append("Valor desproporcional - análise sob ótica do CDC")
        success_probability += 15
    
    # Argumentos gerais sempre aplicáveis
    arguments.extend([
        "Verificação da regularidade do processo administrativo",
        "Análise da presunção de legitimidade do ato administrativo",
        "Direito ao contraditório e ampla defesa (CF/88)",
        "Verificação da tipicidade da conduta"
    ])
    
    # Limitar probabilidade entre 15% e 95%
    success_probability = min(95, max(15, success_probability + random.randint(-10, 15)))
    
    return {
        'success_probability': success_probability,
        'legal_arguments': '; '.join(arguments),
        'main_arguments': arguments[:3]  # Top 3 argumentos
    }

def generate_contest_document(infraction, analysis):
    """
    Gera documento de contestação profissional
    """
    template = f"""
CONTESTAÇÃO DE AUTO DE INFRAÇÃO DE TRÂNSITO

Ao Ilustríssimo Senhor
Diretor da JARI - Junta Administrativa de Recursos de Infrações
{infraction.issuing_agency}

Auto de Infração nº: {infraction.notification_number}
Placa do Veículo: {infraction.vehicle_plate}
Data da Infração: {infraction.date_infraction.strftime('%d/%m/%Y')}

O(A) requerente, devidamente qualificado(a), vem, respeitosamente, perante Vossa Senhoria, 
apresentar CONTESTAÇÃO ao Auto de Infração em epígrafe, pelos fatos e fundamentos jurídicos 
que passa a expor:

DOS FATOS

Em {infraction.date_infraction.strftime('%d/%m/%Y')}, foi lavrado o Auto de Infração nº {infraction.notification_number}, 
imputando ao requerente a prática da infração: {infraction.infraction_type}, no valor de R$ {infraction.value:.2f}.

DO DIREITO

1. DA NULIDADE DO AUTO DE INFRAÇÃO

{analysis['legal_arguments']}

2. DOS PRINCÍPIOS CONSTITUCIONAIS

O presente auto de infração viola os princípios constitucionais do contraditório e da ampla defesa, 
previstos no art. 5º, LV, da Constituição Federal.

3. DO CÓDIGO DE TRÂNSITO BRASILEIRO

Conforme disposto no CTB, Lei nº 9.503/97, o processo administrativo deve observar rigorosamente 
os prazos e formalidades legais.

4. DO CÓDIGO DE DEFESA DO CONSUMIDOR

Aplicam-se ao caso as disposições do CDC, Lei nº 8.078/90, especialmente quanto à 
proporcionalidade e razoabilidade das penalidades.

DO PEDIDO

Diante do exposto, requer-se:

a) O acolhimento da presente contestação;
b) A anulação do Auto de Infração nº {infraction.notification_number};
c) O arquivamento definitivo do processo.

Termos em que pede deferimento.

Local e Data: ________________

_________________________________
Assinatura do Requerente

DOCUMENTOS ANEXOS:
- Cópia do documento de identidade
- Cópia do documento do veículo
- Cópia da notificação de infração
"""
    
    return template

@infraction_bp.route('/infractions', methods=['POST'])
def create_infraction():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        data = request.json
        
        # Validações
        required_fields = ['notification_number', 'infraction_type', 'value', 
                          'date_infraction', 'date_notification', 'vehicle_plate', 
                          'location', 'issuing_agency']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se já existe
        existing = Infraction.query.filter_by(
            notification_number=data['notification_number'],
            user_id=session['user_id']
        ).first()
        
        if existing:
            return jsonify({'error': 'Infração já cadastrada'}), 400
        
        # Criar infração
        infraction = Infraction(
            user_id=session['user_id'],
            notification_number=data['notification_number'],
            infraction_type=data['infraction_type'],
            value=float(data['value']),
            date_infraction=datetime.fromisoformat(data['date_infraction']),
            date_notification=datetime.fromisoformat(data['date_notification']),
            vehicle_plate=data['vehicle_plate'],
            vehicle_model=data.get('vehicle_model'),
            location=data['location'],
            issuing_agency=data['issuing_agency'],
            notification_file=data.get('notification_file')
        )
        
        db.session.add(infraction)
        db.session.flush()  # Para obter o ID
        
        # Realizar análise jurídica
        analysis = analyze_infraction(data)
        
        infraction.success_probability = analysis['success_probability']
        infraction.legal_arguments = analysis['legal_arguments']
        infraction.status = 'analyzed'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Infração analisada com sucesso',
            'infraction': infraction.to_dict(),
            'analysis': analysis
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@infraction_bp.route('/infractions', methods=['GET'])
def get_infractions():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    infractions = Infraction.query.filter_by(user_id=session['user_id']).all()
    return jsonify([infraction.to_dict() for infraction in infractions])

@infraction_bp.route('/infractions/<int:infraction_id>', methods=['GET'])
def get_infraction(infraction_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    infraction = Infraction.query.filter_by(
        id=infraction_id, 
        user_id=session['user_id']
    ).first()
    
    if not infraction:
        return jsonify({'error': 'Infração não encontrada'}), 404
    
    return jsonify(infraction.to_dict())

@infraction_bp.route('/infractions/<int:infraction_id>/contest', methods=['POST'])
def generate_contest(infraction_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        infraction = Infraction.query.filter_by(
            id=infraction_id, 
            user_id=session['user_id']
        ).first()
        
        if not infraction:
            return jsonify({'error': 'Infração não encontrada'}), 404
        
        if infraction.status != 'analyzed':
            return jsonify({'error': 'Infração deve estar analisada'}), 400
        
        # Gerar documento de contestação
        analysis = {
            'legal_arguments': infraction.legal_arguments,
            'success_probability': infraction.success_probability
        }
        
        contest_document = generate_contest_document(infraction, analysis)
        
        # Salvar documento (simulado)
        filename = f"contestacao_{infraction.notification_number}_{uuid.uuid4().hex[:8]}.txt"
        infraction.contest_document = filename
        infraction.status = 'contested'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Documento de contestação gerado com sucesso',
            'document': contest_document,
            'filename': filename,
            'infraction': infraction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@infraction_bp.route('/infractions/<int:infraction_id>/analyze', methods=['POST'])
def reanalyze_infraction(infraction_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        infraction = Infraction.query.filter_by(
            id=infraction_id, 
            user_id=session['user_id']
        ).first()
        
        if not infraction:
            return jsonify({'error': 'Infração não encontrada'}), 404
        
        # Realizar nova análise
        infraction_data = {
            'infraction_type': infraction.infraction_type,
            'date_infraction': infraction.date_infraction.isoformat(),
            'date_notification': infraction.date_notification.isoformat(),
            'issuing_agency': infraction.issuing_agency,
            'location': infraction.location,
            'value': infraction.value
        }
        
        analysis = analyze_infraction(infraction_data)
        
        infraction.success_probability = analysis['success_probability']
        infraction.legal_arguments = analysis['legal_arguments']
        infraction.status = 'analyzed'
        infraction.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Infração reanalisada com sucesso',
            'infraction': infraction.to_dict(),
            'analysis': analysis
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

