from flask import Blueprint, render_template
from ..models import Veiculo, Perfil

main = Blueprint('main', __name__)

@main.route('/')
def home():
    veiculos = Veiculo.query.all() if hasattr(Veiculo, 'query') else []
    return render_template('home.html', veiculos=veiculos)

@main.route('/contato')
def contato():
    return render_template('contato.html')

@main.route('/sobre')
def sobre():
    return render_template('sobre.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')

@main.route('/perfil')
def perfil():
    p = Perfil.query.first() if hasattr(Perfil, 'query') else None
    return render_template('perfil.html', perfil=p)
