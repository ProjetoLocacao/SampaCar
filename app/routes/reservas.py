from flask import Blueprint, render_template, request, current_app, session, jsonify
from ..extensions import db
from ..models import Reserva

reservas = Blueprint('reservas', __name__, template_folder='../../templates')

@reservas.route('/minhas', methods=['GET'], endpoint='minhas')
def minhas_reservas():
    login_required = getattr(current_app, 'login_required', None)
    if callable(login_required):
        @login_required
        def inner():
            uid = session.get('usuario_id')
            try:
                minhas = Reserva.query.filter_by(usuario_id=uid).all() if uid else []
            except Exception:
                minhas = []
            return render_template('minhas_reservas.html', reservas=minhas)
        return inner()
    # fallback
    uid = session.get('usuario_id')
    minhas = Reserva.query.filter_by(usuario_id=uid).all() if uid else []
    return render_template('minhas_reservas.html', reservas=minhas)

@reservas.route('/')
def lista_reservas():
    reservas_list = Reserva.query.all() if hasattr(Reserva, 'query') else []
    return render_template('minhas_reservas.html', reservas=reservas_list)

@reservas.route('/api', methods=['GET','POST'])
def api_reservas():
    if request.method == 'GET':
        res = Reserva.query.all() if hasattr(Reserva, 'query') else []
        return jsonify([{
            'id': r.id,
            'cliente': r.cliente,
            'data_reserva': r.data_reserva,
            'data_devolucao': r.data_devolucao,
            'dias': r.dias,
            'status': r.status,
            'usuario_id': r.usuario_id,
            'veiculo_id': r.veiculo_id
        } for r in res])
    else:
        data = request.get_json(silent=True) or request.form
        r = Reserva(
            cliente=data.get('cliente'),
            data_reserva=data.get('data_reserva'),
            data_devolucao=data.get('data_devolucao'),
            dias=int(data.get('dias') or 0),
            status=data.get('status') or 'pendente',
            usuario_id=data.get('usuario_id'),
            veiculo_id=data.get('veiculo_id')
        )
        db.session.add(r)
        db.session.commit()
        return jsonify({'id': r.id}), 201