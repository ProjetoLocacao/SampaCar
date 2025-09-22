# app.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/cadastro_clientes')
def cadastro_clientes():
    return render_template('cadastro_clientes.html')

@app.route('/cadastro_veiculos')
def cadastro_veiculos():
    return render_template('cadastro_veiculos.html')

@app.route('/painel_frota')
def painel_frota():
    return render_template('painel_frota.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

if __name__ == '__main__':
    app.run(debug=True)
