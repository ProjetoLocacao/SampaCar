from flask import Blueprint, render_template, current_app
from ..models import Veiculo

veiculos = Blueprint('veiculos', __name__, template_folder='../../templates')

@veiculos.route('/', methods=['GET'])
def listar_veiculos():
    try:
        veiculos_list = Veiculo.query.all()
    except Exception:
        veiculos_list = []
    return render_template('veiculos.html', veiculos=veiculos_list)

@veiculos.route('/painel_frota', methods=['GET'])
def painel_frota():
    # usa o decorator admin definido em app.create_app (current_app.admin_required)
    admin_required = getattr(current_app, 'admin_required', None)
    if callable(admin_required):
        @admin_required
        def inner():
            try:
                veiculos_list = Veiculo.query.all()
            except Exception:
                veiculos_list = []
            return render_template('painel_frota.html', veiculos=veiculos_list)
        return inner()
    # fallback: negar acesso se não houver o decorator
    return render_template('403.html'), 403