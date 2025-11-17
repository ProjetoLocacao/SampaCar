from flask import Blueprint, jsonify, request, session
from ..models import Veiculo, Reserva
from ..extensions import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/veiculos', methods=['GET','POST'])
def veiculos_list_create():
    if request.method == 'GET':
        veiculos = Veiculo.query.all()
        return jsonify([{
            'id': v.id, 'marca': v.marca, 'modelo': v.modelo,
            'placa': v.placa, 'ano': v.ano, 'status': v.status,
            'preco_diaria': getattr(v, 'preco_diaria', None),
            'foto': getattr(v, 'foto', None),
            'condicao': getattr(v, 'condicao', None),
            'owner_id': getattr(v, 'owner_id', None)
        } for v in veiculos])
    data = request.json or request.form
    v = Veiculo(
        marca=data.get('marca'),
        modelo=data.get('modelo'),
        placa=data.get('placa'),
        ano=int(data.get('ano') or 0),
        status=data.get('status') or 'disponível',
        preco_diaria=float(data.get('preco_diaria')) if data.get('preco_diaria') else None,
        foto=data.get('foto'),
        condicao=data.get('condicao'),
        owner_id=int(data.get('owner_id')) if data.get('owner_id') else None
    )
    db.session.add(v); db.session.commit()
    return jsonify({'id': v.id}), 201

@api_bp.route('/veiculos/<int:vid>', methods=['GET','PUT','DELETE'])
def veiculo_single(vid):
    v = Veiculo.query.get_or_404(vid)
    if request.method == 'GET':
        return jsonify({
            'id': v.id, 'marca': v.marca, 'modelo': v.modelo,
            'placa': v.placa, 'ano': v.ano, 'status': v.status,
            'preco_diaria': getattr(v, 'preco_diaria', None),
            'foto': getattr(v, 'foto', None),
            'condicao': getattr(v, 'condicao', None),
            'owner_id': getattr(v, 'owner_id', None)
        })
    if request.method == 'PUT':
        data = request.json or request.form
        v.marca = data.get('marca', v.marca)
        v.modelo = data.get('modelo', v.modelo)
        v.placa = data.get('placa', v.placa)
        v.ano = int(data.get('ano') or v.ano)
        v.status = data.get('status', v.status)
        v.preco_diaria = float(data.get('preco_diaria')) if data.get('preco_diaria') else v.preco_diaria
        v.foto = data.get('foto', v.foto)
        v.condicao = data.get('condicao', v.condicao)
        v.owner_id = int(data.get('owner_id')) if data.get('owner_id') else v.owner_id
        db.session.commit()
        return jsonify({'id': v.id})
    if request.method == 'DELETE':
        db.session.delete(v); db.session.commit()
        return jsonify({'result':'deleted'})

@api_bp.route('/veiculos/<int:vid>/reservar', methods=['POST'])
def reservar_veiculo(vid):
    if not session.get('usuario_id'):
        return jsonify({'error':'autenticação necessária'}), 401
    v = Veiculo.query.get_or_404(vid)
    data = request.json or request.form
    r = Reserva(cliente=session.get('usuario_nome') or '',
                data_reserva=data.get('data_reserva'),
                dias=int(data.get('dias') or 0),
                status='ativa', usuario_id=session['usuario_id'],
                veiculo_id=vid)
    v.status = 'alugado'
    db.session.add(r); db.session.commit()
    return jsonify({'id': r.id}), 201

@api_bp.route('/reservas', methods=['GET'])
def reservas_list():
    reservas = Reserva.query.all()
    out = []
    for r in reservas:
        veic = getattr(r, 'veiculo', None)
        out.append({'reserva': {
            'id': r.id, 'cliente': r.cliente, 'data_reserva': r.data_reserva,
            'dias': r.dias, 'status': r.status, 'veiculo_id': r.veiculo_id
        }, 'veiculo': {
            'id': veic.id if veic else None, 'marca': getattr(veic,'marca',None),
            'modelo': getattr(veic,'modelo',None), 'placa': getattr(veic,'placa',None)
        }})
    return jsonify(out)

@api_bp.route('/reservas/<int:rid>/devolver', methods=['POST'])
def devolver_reserva(rid):
    r = Reserva.query.get_or_404(rid)
    data = request.json or request.form
    r.data_devolucao = data.get('data_devolucao')
    r.status = 'finalizada'
    if getattr(r, 'veiculo', None):
        r.veiculo.status = 'disponível'
    db.session.commit()
    return jsonify({'id': r.id})