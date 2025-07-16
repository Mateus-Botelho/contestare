from flask import Blueprint, jsonify, request, session
from src.models.contract import Contract, UserContract, db
from src.models.user import User
from datetime import datetime

contract_bp = Blueprint('contract', __name__)

# Dados de contratos populares para popular o sistema
POPULAR_CONTRACTS = [
    {
        'title': 'Contrato de Locação Residencial',
        'category': 'civil',
        'description': 'Contrato completo para locação de imóveis residenciais com todas as cláusulas necessárias.',
        'price': 19.90,
        'content': '''CONTRATO DE LOCAÇÃO RESIDENCIAL

LOCADOR: [NOME_LOCADOR], [QUALIFICAÇÃO_LOCADOR]
LOCATÁRIO: [NOME_LOCATARIO], [QUALIFICAÇÃO_LOCATARIO]

CLÁUSULA 1ª - DO OBJETO
O LOCADOR dá em locação ao LOCATÁRIO o imóvel situado em [ENDERECO_IMOVEL].

CLÁUSULA 2ª - DO PRAZO
O prazo de locação é de [PRAZO_LOCACAO], iniciando-se em [DATA_INICIO].

CLÁUSULA 3ª - DO VALOR
O valor mensal da locação é de R$ [VALOR_ALUGUEL].

[DEMAIS_CLAUSULAS]'''
    },
    {
        'title': 'Contrato de Prestação de Serviços',
        'category': 'comercial',
        'description': 'Modelo para prestação de serviços profissionais com definição de escopo e responsabilidades.',
        'price': 19.90,
        'content': '''CONTRATO DE PRESTAÇÃO DE SERVIÇOS

CONTRATANTE: [NOME_CONTRATANTE]
CONTRATADO: [NOME_CONTRATADO]

CLÁUSULA 1ª - DO OBJETO
O CONTRATADO prestará os seguintes serviços: [DESCRICAO_SERVICOS]

CLÁUSULA 2ª - DO PRAZO
Os serviços serão executados no prazo de [PRAZO_EXECUCAO].

CLÁUSULA 3ª - DO VALOR
O valor total dos serviços é de R$ [VALOR_TOTAL].'''
    },
    {
        'title': 'Contrato de Compra e Venda',
        'category': 'civil',
        'description': 'Contrato para compra e venda de bens móveis e imóveis.',
        'price': 19.90,
        'content': '''CONTRATO DE COMPRA E VENDA

VENDEDOR: [NOME_VENDEDOR]
COMPRADOR: [NOME_COMPRADOR]

CLÁUSULA 1ª - DO OBJETO
O VENDEDOR vende ao COMPRADOR [DESCRICAO_BEM].

CLÁUSULA 2ª - DO PREÇO
O preço total é de R$ [VALOR_TOTAL].'''
    },
    {
        'title': 'Contrato de Trabalho',
        'category': 'trabalhista',
        'description': 'Modelo de contrato de trabalho com todas as cláusulas trabalhistas.',
        'price': 19.90,
        'is_premium': True,
        'content': '''CONTRATO DE TRABALHO

EMPREGADOR: [NOME_EMPREGADOR]
EMPREGADO: [NOME_EMPREGADO]

CLÁUSULA 1ª - DA FUNÇÃO
O EMPREGADO exercerá a função de [CARGO].

CLÁUSULA 2ª - DO SALÁRIO
O salário mensal é de R$ [SALARIO].'''
    },
    {
        'title': 'Contrato de Sociedade',
        'category': 'empresarial',
        'description': 'Contrato para constituição de sociedade empresarial.',
        'price': 19.90,
        'is_premium': True,
        'content': '''CONTRATO DE CONSTITUIÇÃO DE SOCIEDADE

SÓCIOS: [NOMES_SOCIOS]

CLÁUSULA 1ª - DA DENOMINAÇÃO
A sociedade terá a denominação [NOME_EMPRESA].

CLÁUSULA 2ª - DO CAPITAL
O capital social é de R$ [CAPITAL_SOCIAL].'''
    }
]

def init_contracts():
    """Inicializa contratos populares no banco de dados"""
    for contract_data in POPULAR_CONTRACTS:
        existing = Contract.query.filter_by(title=contract_data['title']).first()
        if not existing:
            contract = Contract(**contract_data)
            db.session.add(contract)
    
    try:
        db.session.commit()
    except:
        db.session.rollback()

@contract_bp.route('/contracts', methods=['GET'])
def get_contracts():
    """Lista todos os contratos disponíveis"""
    category = request.args.get('category')
    is_premium = request.args.get('is_premium')
    
    query = Contract.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if is_premium is not None:
        query = query.filter_by(is_premium=is_premium.lower() == 'true')
    
    contracts = query.order_by(Contract.popularity_score.desc()).all()
    
    return jsonify([contract.to_dict() for contract in contracts])

@contract_bp.route('/contracts/<int:contract_id>', methods=['GET'])
def get_contract(contract_id):
    """Obtém detalhes de um contrato específico"""
    contract = Contract.query.get_or_404(contract_id)
    
    if not contract.is_active:
        return jsonify({'error': 'Contrato não disponível'}), 404
    
    return jsonify(contract.to_dict())

@contract_bp.route('/contracts/<int:contract_id>/purchase', methods=['POST'])
def purchase_contract(contract_id):
    """Compra um contrato"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        contract = Contract.query.get_or_404(contract_id)
        user = User.query.get(session['user_id'])
        
        if not contract.is_active:
            return jsonify({'error': 'Contrato não disponível'}), 404
        
        # Verificar se é premium e usuário tem acesso
        if contract.is_premium and not user.is_premium:
            return jsonify({'error': 'Contrato premium requer assinatura premium'}), 403
        
        # Verificar se já comprou
        existing_purchase = UserContract.query.filter_by(
            user_id=session['user_id'],
            contract_id=contract_id
        ).first()
        
        if existing_purchase:
            return jsonify({'error': 'Contrato já adquirido'}), 400
        
        # Criar registro de compra
        user_contract = UserContract(
            user_id=session['user_id'],
            contract_id=contract_id,
            customized_content=contract.content  # Cópia inicial
        )
        
        # Aumentar popularidade
        contract.popularity_score += 1
        
        db.session.add(user_contract)
        db.session.commit()
        
        return jsonify({
            'message': 'Contrato adquirido com sucesso',
            'user_contract': user_contract.to_dict(),
            'contract': contract.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contract_bp.route('/my-contracts', methods=['GET'])
def get_user_contracts():
    """Lista contratos do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    user_contracts = db.session.query(UserContract, Contract).join(
        Contract, UserContract.contract_id == Contract.id
    ).filter(UserContract.user_id == session['user_id']).all()
    
    result = []
    for user_contract, contract in user_contracts:
        contract_data = contract.to_dict()
        contract_data['user_contract'] = user_contract.to_dict()
        result.append(contract_data)
    
    return jsonify(result)

@contract_bp.route('/my-contracts/<int:user_contract_id>', methods=['GET'])
def get_user_contract(user_contract_id):
    """Obtém contrato específico do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    user_contract = UserContract.query.filter_by(
        id=user_contract_id,
        user_id=session['user_id']
    ).first()
    
    if not user_contract:
        return jsonify({'error': 'Contrato não encontrado'}), 404
    
    contract = Contract.query.get(user_contract.contract_id)
    
    return jsonify({
        'user_contract': user_contract.to_dict(),
        'contract': contract.to_dict()
    })

@contract_bp.route('/my-contracts/<int:user_contract_id>/customize', methods=['PUT'])
def customize_contract(user_contract_id):
    """Personaliza o conteúdo de um contrato"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user_contract = UserContract.query.filter_by(
            id=user_contract_id,
            user_id=session['user_id']
        ).first()
        
        if not user_contract:
            return jsonify({'error': 'Contrato não encontrado'}), 404
        
        data = request.json
        
        if 'customized_content' in data:
            user_contract.customized_content = data['customized_content']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Contrato personalizado com sucesso',
            'user_contract': user_contract.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contract_bp.route('/my-contracts/<int:user_contract_id>/download', methods=['POST'])
def download_contract(user_contract_id):
    """Marca contrato como baixado e incrementa contador"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user_contract = UserContract.query.filter_by(
            id=user_contract_id,
            user_id=session['user_id']
        ).first()
        
        if not user_contract:
            return jsonify({'error': 'Contrato não encontrado'}), 404
        
        user_contract.is_downloaded = True
        user_contract.download_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Download registrado com sucesso',
            'content': user_contract.customized_content,
            'download_count': user_contract.download_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contract_bp.route('/categories', methods=['GET'])
def get_categories():
    """Lista categorias de contratos disponíveis"""
    categories = db.session.query(Contract.category).distinct().all()
    return jsonify([cat[0] for cat in categories])

@contract_bp.route('/popular', methods=['GET'])
def get_popular_contracts():
    """Lista contratos mais populares"""
    contracts = Contract.query.filter_by(is_active=True).order_by(
        Contract.popularity_score.desc()
    ).limit(10).all()
    
    return jsonify([contract.to_dict() for contract in contracts])

# Inicializar contratos ao importar o módulo
# init_contracts()  # Comentado para evitar erro de contexto


# Contratos adicionais para expandir a biblioteca

ADDITIONAL_CONTRACTS = [
    {
        'title': 'Contrato de Locação Comercial',
        'category': 'civil',
        'description': 'Contrato para locação de imóveis comerciais com cláusulas específicas para atividade empresarial.',
        'price': 19.90,
        'content': '''CONTRATO DE LOCAÇÃO COMERCIAL

LOCADOR: [NOME_LOCADOR], [QUALIFICACAO_LOCADOR]
LOCATÁRIO: [NOME_LOCATARIO], [QUALIFICACAO_LOCATARIO]

CLÁUSULA 1ª - DO OBJETO
O LOCADOR dá em locação ao LOCATÁRIO o imóvel comercial situado em [ENDERECO_IMOVEL], destinado ao exercício da atividade de [ATIVIDADE_COMERCIAL].

CLÁUSULA 2ª - DO PRAZO
O prazo de locação é de [PRAZO_LOCACAO], iniciando-se em [DATA_INICIO] e terminando em [DATA_FIM].

CLÁUSULA 3ª - DO VALOR E FORMA DE PAGAMENTO
O valor mensal da locação é de R$ [VALOR_ALUGUEL], reajustável anualmente pelo [INDICE_REAJUSTE].

CLÁUSULA 4ª - DO DEPÓSITO CAUÇÃO
O LOCATÁRIO depositará a título de caução o valor de R$ [VALOR_CAUCAO].

CLÁUSULA 5ª - DAS BENFEITORIAS
As benfeitorias necessárias serão de responsabilidade do LOCADOR, e as úteis e voluptuárias do LOCATÁRIO.

CLÁUSULA 6ª - DA RESCISÃO
O contrato poderá ser rescindido mediante aviso prévio de [PRAZO_AVISO] dias.'''
    },
    {
        'title': 'Contrato de Franquia',
        'category': 'comercial',
        'description': 'Acordo para exploração de marca e sistema de negócios.',
        'price': 19.90,
        'is_premium': True,
        'content': '''CONTRATO DE FRANQUIA

FRANQUEADOR: [NOME_FRANQUEADOR]
FRANQUEADO: [NOME_FRANQUEADO]

CLÁUSULA 1ª - DO OBJETO
O FRANQUEADOR concede ao FRANQUEADO o direito de explorar a marca [NOME_MARCA] na região de [TERRITORIO].

CLÁUSULA 2ª - DA TAXA DE FRANQUIA
O FRANQUEADO pagará taxa inicial de R$ [TAXA_INICIAL] e royalties mensais de [PERCENTUAL_ROYALTY]%.

CLÁUSULA 3ª - DAS OBRIGAÇÕES
O FRANQUEADO obriga-se a seguir o padrão operacional e de qualidade estabelecido.

CLÁUSULA 4ª - DO TERRITÓRIO
A exploração da franquia fica restrita ao território de [TERRITORIO_EXCLUSIVO].

CLÁUSULA 5ª - DO PRAZO
O contrato tem prazo de [PRAZO_FRANQUIA] anos, renovável por igual período.'''
    },
    {
        'title': 'Contrato de Desenvolvimento de Software',
        'category': 'tecnologia',
        'description': 'Desenvolvimento de sistemas e aplicações sob medida.',
        'price': 19.90,
        'is_premium': True,
        'content': '''CONTRATO DE DESENVOLVIMENTO DE SOFTWARE

CONTRATANTE: [NOME_CONTRATANTE]
DESENVOLVEDOR: [NOME_DESENVOLVEDOR]

CLÁUSULA 1ª - DO OBJETO
O DESENVOLVEDOR criará o software [NOME_SOFTWARE] conforme especificações técnicas anexas.

CLÁUSULA 2ª - DO PRAZO
O desenvolvimento será concluído em [PRAZO_DESENVOLVIMENTO] dias.

CLÁUSULA 3ª - DO VALOR
O valor total é de R$ [VALOR_TOTAL], pago em [FORMA_PAGAMENTO].

CLÁUSULA 4ª - DA PROPRIEDADE INTELECTUAL
Os direitos autorais do software pertencem ao [PROPRIETARIO_DIREITOS].

CLÁUSULA 5ª - DA GARANTIA
O DESENVOLVEDOR garante o funcionamento do software por [PRAZO_GARANTIA] meses.'''
    },
    {
        'title': 'Contrato de Compra e Venda de Imóvel',
        'category': 'imobiliario',
        'description': 'Transferência de propriedade imobiliária com todas as garantias.',
        'price': 19.90,
        'is_premium': True,
        'content': '''CONTRATO DE COMPRA E VENDA DE IMÓVEL

VENDEDOR: [NOME_VENDEDOR]
COMPRADOR: [NOME_COMPRADOR]

CLÁUSULA 1ª - DO OBJETO
O VENDEDOR vende ao COMPRADOR o imóvel situado em [ENDERECO_COMPLETO].

CLÁUSULA 2ª - DO PREÇO
O preço total é de R$ [VALOR_IMOVEL], pago da seguinte forma: [FORMA_PAGAMENTO].

CLÁUSULA 3ª - DA DOCUMENTAÇÃO
O imóvel está livre de ônus e possui toda documentação regular.

CLÁUSULA 4ª - DA TRADIÇÃO
A posse será transferida em [DATA_ENTREGA].

CLÁUSULA 5ª - DOS IMPOSTOS
Os impostos e taxas até a data da venda são de responsabilidade do VENDEDOR.'''
    },
    {
        'title': 'Contrato de Consultoria',
        'category': 'servicos',
        'description': 'Prestação de serviços especializados de consultoria.',
        'price': 19.90,
        'content': '''CONTRATO DE CONSULTORIA

CONTRATANTE: [NOME_CONTRATANTE]
CONSULTOR: [NOME_CONSULTOR]

CLÁUSULA 1ª - DO OBJETO
O CONSULTOR prestará serviços de consultoria em [AREA_CONSULTORIA].

CLÁUSULA 2ª - DO ESCOPO
Os serviços incluem: [DESCRICAO_SERVICOS].

CLÁUSULA 3ª - DO PRAZO
Os serviços serão prestados no período de [DATA_INICIO] a [DATA_FIM].

CLÁUSULA 4ª - DA REMUNERAÇÃO
O valor total é de R$ [VALOR_CONSULTORIA], pago em [FORMA_PAGAMENTO].

CLÁUSULA 5ª - DA CONFIDENCIALIDADE
O CONSULTOR compromete-se a manter sigilo sobre informações confidenciais.'''
    },
    {
        'title': 'Contrato Social de LTDA',
        'category': 'societario',
        'description': 'Constituição de sociedade limitada.',
        'price': 19.90,
        'is_premium': True,
        'content': '''CONTRATO SOCIAL DE SOCIEDADE LIMITADA

SÓCIOS: [NOMES_SOCIOS]

CLÁUSULA 1ª - DA CONSTITUIÇÃO
Fica constituída uma sociedade limitada sob a denominação [NOME_EMPRESA].

CLÁUSULA 2ª - DO OBJETO SOCIAL
A sociedade tem por objeto [OBJETO_SOCIAL].

CLÁUSULA 3ª - DO CAPITAL SOCIAL
O capital social é de R$ [CAPITAL_SOCIAL], dividido em [NUMERO_QUOTAS] quotas.

CLÁUSULA 4ª - DA ADMINISTRAÇÃO
A administração da sociedade caberá a [ADMINISTRADORES].

CLÁUSULA 5ª - DO EXERCÍCIO SOCIAL
O exercício social coincide com o ano civil.'''
    },
    {
        'title': 'Contrato de Comodato',
        'category': 'civil',
        'description': 'Empréstimo gratuito de bem móvel ou imóvel por tempo determinado.',
        'price': 19.90,
        'content': '''CONTRATO DE COMODATO

COMODANTE: [NOME_COMODANTE]
COMODATÁRIO: [NOME_COMODATARIO]

CLÁUSULA 1ª - DO OBJETO
O COMODANTE empresta gratuitamente ao COMODATÁRIO o bem [DESCRICAO_BEM].

CLÁUSULA 2ª - DO PRAZO
O prazo do comodato é de [PRAZO_COMODATO], findando automaticamente em [DATA_FIM].

CLÁUSULA 3ª - DAS OBRIGAÇÕES
O COMODATÁRIO obriga-se a conservar o bem e restituí-lo no estado em que o recebeu.

CLÁUSULA 4ª - DA RESPONSABILIDADE
O COMODATÁRIO responde pelos danos causados ao bem por culpa sua.

CLÁUSULA 5ª - DA RESTITUIÇÃO
O bem deverá ser restituído no prazo estabelecido, independente de notificação.'''
    },
    {
        'title': 'Contrato de Marketing Digital',
        'category': 'servicos',
        'description': 'Serviços de marketing e publicidade online.',
        'price': 19.90,
        'content': '''CONTRATO DE MARKETING DIGITAL

CONTRATANTE: [NOME_CONTRATANTE]
AGÊNCIA: [NOME_AGENCIA]

CLÁUSULA 1ª - DO OBJETO
A AGÊNCIA prestará serviços de marketing digital incluindo [SERVICOS_INCLUSOS].

CLÁUSULA 2ª - DAS METAS
As metas estabelecidas são: [METAS_MARKETING].

CLÁUSULA 3ª - DO INVESTIMENTO
O investimento mensal é de R$ [VALOR_MENSAL] para mídia paga e R$ [VALOR_SERVICOS] para serviços.

CLÁUSULA 4ª - DOS RELATÓRIOS
A AGÊNCIA fornecerá relatórios mensais de performance.

CLÁUSULA 5ª - DA PROPRIEDADE
O conteúdo criado pertence ao CONTRATANTE.'''
    }
]

def init_additional_contracts():
    """Inicializa contratos adicionais no banco de dados"""
    for contract_data in ADDITIONAL_CONTRACTS:
        existing = Contract.query.filter_by(title=contract_data['title']).first()
        if not existing:
            contract = Contract(**contract_data)
            db.session.add(contract)
    
    try:
        db.session.commit()
    except:
        db.session.rollback()

