from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from ..models import Usuario
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        user = Usuario.query.filter_by(email=email).first() if hasattr(Usuario, 'query') else None
        if user and check_password_hash(user.senha, senha):
            session['usuario_id'] = user.id
            session['usuario_tipo'] = getattr(user, 'tipo', None)
            session['usuario_nome'] = getattr(user, 'nome', '')   # ADICIONADO: nome na sessão
            return redirect(url_for('main.home'))
        flash('Credenciais inválidas')
    return render_template('login.html')

@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    # limpa sessão
    session.clear()
    flash('Você saiu da conta.', 'info')
    # redireciona para rota de login — tenta 'auth.login' se blueprint auth existir
    if 'auth' in current_app.blueprints:
        return redirect(url_for('auth.login'))
    return redirect('/login')

@auth.route('/cadastro', methods=['GET','POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        telefone = request.form.get('telefone')
        tipo = request.form.get('tipo') or 'usuario'
        if hasattr(Usuario, 'query') and Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado')
            return redirect(url_for('auth.cadastro'))
        hashed = generate_password_hash(senha) if senha else ''
        user = Usuario(nome=nome, email=email, senha=hashed, telefone=telefone, tipo=tipo)
        db.session.add(user)
        db.session.commit()
        flash('Registro criado com sucesso')
        return redirect(url_for('auth.login'))
    return render_template('cadastro.html')