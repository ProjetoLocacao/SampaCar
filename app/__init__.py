from flask import Flask, jsonify, request, session, g, redirect, url_for, flash, render_template, abort
from .models import Veiculo, Reserva
from .extensions import db
from functools import wraps

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config['SECRET_KEY'] = 'chave-secreta-do-locacar'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///locacar_final.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # carregar blueprints de forma tolerante a nomes diferentes nos arquivos
    def _load_blueprint(mod_name):
        try:
            mod = __import__(f"app.routes.{mod_name}", fromlist=[mod_name])
        except Exception:
            return None
        for attr in (mod_name, f"{mod_name}_bp", f"{mod_name}bp", "bp", "blueprint"):
            if hasattr(mod, attr):
                return getattr(mod, attr)
        return None

    auth_bp = _load_blueprint('auth')
    main_bp = _load_blueprint('main')
    veiculos_bp = _load_blueprint('veiculos')
    reservas_bp = _load_blueprint('reservas')

    if auth_bp:
        app.register_blueprint(auth_bp)
    if main_bp:
        app.register_blueprint(main_bp)
    if veiculos_bp:
        app.register_blueprint(veiculos_bp, url_prefix='/veiculos')
    if reservas_bp:
        app.register_blueprint(reservas_bp, url_prefix='/reservas')

    # disponibiliza `current_user` e `is_admin` nas templates
    @app.context_processor
    def inject_user():
        user = None
        if session.get('usuario_id'):
            user = {
                'id': session.get('usuario_id'),
                'nome': session.get('usuario_nome'),
                'tipo': session.get('usuario_tipo')
            }
        return {'current_user': user, 'is_admin': (user and user.get('tipo') == 'admin')}

    # decorator para require login
    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('usuario_id'):
                flash('Você precisa fazer login para acessar essa página.', 'warning')
                return redirect(url_for('auth.login') if 'auth' in app.blueprints else url_for('login'))
            return f(*args, **kwargs)
        return decorated

    # decorator para require admin
    def admin_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('usuario_id'):
                flash('Login requerido.', 'warning')
                return redirect(url_for('auth.login') if 'auth' in app.blueprints else url_for('login'))
            if session.get('usuario_tipo') != 'admin':
                # se não for admin, mostrar 403 simples
                return render_template('403.html'), 403 if '403.html' in app.jinja_env.list_templates() else abort(403)
            return f(*args, **kwargs)
        return decorated

    # anexa os decorators para uso nos blueprints importados (opções)
    app.login_required = login_required
    app.admin_required = admin_required

    # --- ROTAS JSON COMPATÍVEIS COM O FRONTEND (sem criar api.py) ---
    @app.route('/api/veiculos', methods=['GET', 'POST'])
    def api_veiculos():
        if request.method == 'GET':
            veiculos = Veiculo.query.all()
            return jsonify([{
                'id': v.id,
                'marca': v.marca,
                'modelo': v.modelo,
                'placa': v.placa,
                'ano': v.ano,
                'status': v.status,
                'preco_diaria': getattr(v, 'preco_diaria', None),
                'foto': getattr(v, 'foto', None),
                'condicao': getattr(v, 'condicao', None),
                'owner_id': getattr(v, 'owner_id', None)
            } for v in veiculos])
        data = request.get_json(silent=True) or request.form
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

    @app.route('/api/veiculos/<int:vid>/reservar', methods=['POST'])
    def api_reservar(vid):
        if not session.get('usuario_id'):
            return jsonify({'error': 'autenticação necessária'}), 401
        v = Veiculo.query.get_or_404(vid)
        data = request.get_json(silent=True) or request.form
        r = Reserva(
            cliente = session.get('usuario_nome') or '',
            data_reserva = data.get('data_reserva'),
            data_devolucao = data.get('data_devolucao'),
            dias = int(data.get('dias') or 0),
            status = data.get('status') or 'ativa',
            usuario_id = session.get('usuario_id'),
            veiculo_id = vid
        )
        v.status = 'alugado'
        db.session.add(r)
        db.session.commit()
        return jsonify({'id': r.id}), 201

    @app.route('/api/reservas', methods=['GET', 'POST'])
    def api_reservas():
        if request.method == 'GET':
            reservas = Reserva.query.all()
            out = []
            for r in reservas:
                veic = getattr(r, 'veiculo', None)
                out.append({
                    'reserva': {
                        'id': r.id,
                        'cliente': r.cliente,
                        'data_reserva': r.data_reserva,
                        'data_devolucao': r.data_devolucao,
                        'dias': r.dias,
                        'status': r.status,
                        'usuario_id': r.usuario_id,
                        'veiculo_id': r.veiculo_id
                    },
                    'veiculo': {
                        'id': veic.id if veic else None,
                        'marca': getattr(veic, 'marca', None),
                        'modelo': getattr(veic, 'modelo', None),
                        'placa': getattr(veic, 'placa', None),
                        'ano': getattr(veic, 'ano', None),
                        'status': getattr(veic, 'status', None),
                        'foto': getattr(veic, 'foto', None)
                    }
                })
            return jsonify(out)
        data = request.get_json(silent=True) or request.form
        r = Reserva(
            cliente = data.get('cliente') or session.get('usuario_nome', ''),
            data_reserva = data.get('data_reserva'),
            data_devolucao = data.get('data_devolucao'),
            dias = int(data.get('dias') or 0),
            status = data.get('status') or 'pendente',
            usuario_id = int(data.get('usuario_id') or session.get('usuario_id')),
            veiculo_id = int(data.get('veiculo_id') or 0)
        )
        db.session.add(r); db.session.commit()
        return jsonify({'id': r.id}), 201

    @app.route('/api/reservas/<int:rid>/devolver', methods=['POST'])
    def api_devolver(rid):
        r = Reserva.query.get_or_404(rid)
        data = request.get_json(silent=True) or request.form
        r.data_devolucao = data.get('data_devolucao')
        r.status = 'finalizada'
        if getattr(r, 'veiculo', None):
            r.veiculo.status = 'disponível'
        db.session.commit()
        return jsonify({'id': r.id})

    # --- fim rotas JSON ---
    # create tables and seed if needed
    with app.app_context():
        db.create_all()
        try:
            from .utils import seed_db
            seed_db()
        except Exception:
            pass

    return app