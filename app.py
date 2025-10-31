from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import json
from pathlib import Path
import os
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'chave-secreta-do-locacar'  # Chave fixa para desenvolvimento

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
DATA_FILE = Path('data.json')

def read_data():
    if not DATA_FILE.exists():
        data = {
            "veiculos": [
                {
                    "id": 1,
                    "marca": "Fiat",
                    "modelo": "Uno",
                    "ano": 2020,
                    "status": "disponível",
                    "placa": "ABC1234"
                },
                {
                    "id": 2,
                    "marca": "Chevrolet",
                    "modelo": "Onix",
                    "ano": 2021,
                    "status": "disponível",
                    "placa": "XYZ5678"
                }
            ],
            "reservas": [],
            "perfil": {},
            "clientes": []
        }
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return data
    data = json.loads(DATA_FILE.read_text(encoding='utf-8'))

    # Migração automática: converter formato antigo de reservas (veiculo_index) para o formato atual
    reservas = data.get('reservas', [])
    precisa_migrar = any(isinstance(r, dict) and 'veiculo_index' in r for r in reservas)
    if precisa_migrar:
        print('Migrando formato antigo de reservas para novo formato...')
        novas_reservas = []
        usuarios = data.get('usuarios', [])
        default_usuario_id = usuarios[0]['id'] if usuarios else None
        veiculos = data.get('veiculos', [])
        next_id = 1
        for item in reservas:
            if not isinstance(item, dict):
                continue
            idx = item.get('veiculo_index')
            if idx is None:
                continue
            # tenta mapear pelo índice para o id do veículo
            veiculo_id = None
            if isinstance(idx, int) and 0 <= idx < len(veiculos):
                ve = veiculos[idx]
                veiculo_id = ve.get('id') or (idx + 1)
            # montar reserva padrão
            reserva = {
                'id': next_id,
                'veiculo_id': veiculo_id,
                'usuario_id': default_usuario_id,
                'cliente': data.get('perfil', {}).get('nome', 'Cliente'),
                'data_reserva': item.get('data_reserva') or '',
                'dias': item.get('dias', 1),
                'status': 'ativa'
            }
            novas_reservas.append(reserva)
            # marcar veículo como alugado se mapeado
            if veiculo_id is not None:
                for v in veiculos:
                    if v.get('id') == veiculo_id:
                        v['status'] = 'alugado'
                        break
            next_id += 1

        data['reservas'] = novas_reservas
        data['veiculos'] = veiculos
        write_data(data)
        print('Migração concluída, data.json atualizada.')

    return data

def write_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        data = read_data()
        usuario = next((u for u in data.get('usuarios', []) 
                       if u['email'] == email and u['senha'] == senha), None)
        
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_tipo'] = usuario.get('tipo', 'usuario')
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email ou senha inválidos!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        data = read_data()
        novo_usuario = {
            'id': len(data.get('usuarios', [])) + 1,
            'nome': request.form.get('nome'),
            'email': request.form.get('email'),
            'senha': request.form.get('senha'),
            'telefone': request.form.get('telefone'),
            'tipo': 'usuario'
        }
        
        # Verificar se email já existe
        if any(u['email'] == novo_usuario['email'] for u in data.get('usuarios', [])):
            flash('Email já cadastrado!', 'error')
            return redirect(url_for('cadastro'))
        
        if 'usuarios' not in data:
            data['usuarios'] = []
        data['usuarios'].append(novo_usuario)
        write_data(data)
        
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('cadastro.html')

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/cadastro_clientes')
def cadastro_clientes():
    return render_template('cadastro_clientes.html')

@app.route('/cadastro_veiculos')
def cadastro_veiculos():
    return render_template('cadastro_veiculos.html')

@app.route('/painel_frota')
@login_required
def painel_frota():
    data = read_data()
    usuario = next((u for u in data.get('usuarios', []) if u['id'] == session['usuario_id']), None)
    is_admin = usuario and usuario.get('tipo') == 'admin'
    # restringe acesso ao painel da frota apenas para administradores
    if not is_admin:
        flash('Acesso negado: painel disponível apenas para administradores.', 'error')
        return redirect(url_for('home'))

    return render_template('painel_frota.html', is_admin=is_admin)

@app.route('/minhas_reservas')
def minhas_reservas():
    return render_template('minhas_reservas.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    data = read_data()
    if request.method == 'POST':
        # Se a requisição for JSON (API)
        if request.is_json:
            perfil_data = request.json
            data['perfil'] = perfil_data
            write_data(data)
            return jsonify({"message": "Perfil atualizado com sucesso", "perfil": perfil_data})
        
        # Se for submissão do formulário
        perfil_data = {
            'nome': request.form.get('nome'),
            'email': request.form.get('email'),
            'telefone': request.form.get('telefone'),
            'endereco': request.form.get('endereco')
        }
        data['perfil'] = perfil_data
        write_data(data)
        return redirect(url_for('perfil'))
    
    # Se for GET, renderiza o template
    return render_template('perfil.html', perfil=data.get('perfil', {}))

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        # Aqui você pode adicionar lógica para processar o formulário
        # Por exemplo, enviar email, salvar no banco de dados, etc.
        nome = request.form.get('nome')
        email = request.form.get('email')
        mensagem = request.form.get('mensagem')
        # Por enquanto, apenas retornamos à página
        return redirect(url_for('contato'))
    return render_template('contato.html')

# --- API endpoints ---
@app.route('/api/veiculos', methods=['GET'])
def api_get_veiculos():
    data = read_data()
    marca = request.args.get('marca')
    modelo = request.args.get('modelo')
    
    veiculos = data["veiculos"]
    if marca:
        veiculos = [v for v in veiculos if marca.lower() in v['marca'].lower()]
    if modelo:
        veiculos = [v for v in veiculos if modelo.lower() in v['modelo'].lower()]
    
    return jsonify(veiculos)

@app.route('/api/veiculos/<int:veiculo_id>', methods=['GET'])
def api_get_veiculo(veiculo_id):
    data = read_data()
    veiculo = next((v for v in data["veiculos"] if v["id"] == veiculo_id), None)
    if not veiculo:
        return jsonify({"error": "Veículo não encontrado"}), 404
    return jsonify(veiculo)

@app.route('/api/veiculos', methods=['POST'])
@login_required
def api_add_veiculo():
    data = read_data()
    novo = request.json or {}
    
    # Validação básica
    required_fields = ["marca", "modelo", "ano", "placa"]
    if not all(k in novo for k in required_fields):
        return jsonify({"error": "Campos obrigatórios faltando"}), 400
    
    # Gerar ID único
    ids = [v.get('id', 0) for v in data["veiculos"]]
    novo_id = max(ids + [0]) + 1
    
    # registra o proprietário do veículo (quem está logado)
    novo.update({
        "id": novo_id,
        "status": "disponível",
        "owner_id": session.get('usuario_id')
    })
    
    data["veiculos"].append(novo)
    write_data(data)
    return jsonify(novo), 201

@app.route('/api/veiculos/<int:veiculo_id>', methods=['PUT'])
@login_required
def api_update_veiculo(veiculo_id):
    if not session.get('usuario_tipo') == 'admin':
        return jsonify({"error": "Acesso não autorizado"}), 403
        
    data = read_data()
    veiculo = next((v for v in data["veiculos"] if v["id"] == veiculo_id), None)
    if not veiculo:
        return jsonify({"error": "Veículo não encontrado"}), 404
    
    # Atualizar status
    novo_status = request.json.get('status')
    if novo_status and novo_status in ['disponível', 'alugado', 'manutenção']:
        veiculo['status'] = novo_status
        write_data(data)
        return jsonify(veiculo)
    return jsonify({"error": "Status inválido"}), 400

@app.route('/api/veiculos/<int:veiculo_id>', methods=['DELETE'])
@login_required
def api_delete_veiculo(veiculo_id):
    data = read_data()
    veiculo = next((v for v in data["veiculos"] if v["id"] == veiculo_id), None)
    if not veiculo:
        return jsonify({"error": "Veículo não encontrado"}), 404

    usuario_id = session.get('usuario_id')
    usuario_tipo = session.get('usuario_tipo')

    # só admin ou o dono do veículo pode excluir
    if usuario_tipo != 'admin' and veiculo.get('owner_id') != usuario_id:
        return jsonify({"error": "Acesso não autorizado"}), 403

    data["veiculos"] = [v for v in data["veiculos"] if v["id"] != veiculo_id]
    write_data(data)
    return jsonify({"message": "Veículo excluído com sucesso"})

@app.route('/api/veiculos/<int:veiculo_id>/reservar', methods=['POST'])
def reservar_veiculo(veiculo_id):
    data = read_data()
    
    # Encontrar veículo pelo ID
    veiculo = next((v for v in data["veiculos"] if v.get('id') == veiculo_id), None)
    if not veiculo:
        return jsonify({"error": "Veículo não encontrado"}), 404
        
    if veiculo['status'] == 'alugado':
        return jsonify({"error": "Veículo já está alugado"}), 400
        
    # Criar reserva
    reserva = {
        "id": len(data.get('reservas', [])) + 1,
        "veiculo_id": veiculo_id,
        "usuario_id": session.get('usuario_id'),
        "cliente": data.get('perfil', {}).get('nome', 'Cliente'),
        "data_reserva": request.json.get('data_reserva', ''),
        "dias": request.json.get('dias', 1),
        "status": "ativa"
    }
    
    veiculo['status'] = 'alugado'
    data['reservas'].append(reserva)
    write_data(data)
    
    return jsonify({
        "message": "Reserva realizada com sucesso",
        "reserva": reserva,
        "veiculo": veiculo
    })


@app.route('/api/veiculos/<int:veiculo_id>/devolver', methods=['POST'])
@login_required
def devolver_por_veiculo(veiculo_id):
    try:
        print(f"Solicitação de devolução por veículo: {veiculo_id} por usuário {session.get('usuario_id')}")
        if not request.is_json:
            # ainda aceitaremos caso não seja JSON (compatibilidade com chamadas simples)
            data_req = request.get_json(silent=True) or {}
        else:
            data_req = request.json

        data = read_data()
        # encontrar reserva ativa para o veículo
        reserva = next((r for r in data.get('reservas', []) if r.get('veiculo_id') == veiculo_id and r.get('status') != 'finalizada'), None)
        if not reserva:
            return jsonify({"error": "Reserva ativa não encontrada para este veículo"}), 404

        # autorização: dono da reserva ou admin
        if reserva.get('usuario_id') != session.get('usuario_id') and session.get('usuario_tipo') != 'admin':
            return jsonify({"error": "Não autorizado"}), 403

        # encontrar veículo
        veiculo = next((v for v in data.get('veiculos', []) if v.get('id') == veiculo_id), None)
        if not veiculo:
            return jsonify({"error": "Veículo não encontrado"}), 404

        # finalizar
        veiculo['status'] = 'disponível'
        reserva['status'] = 'finalizada'
        reserva['data_devolucao'] = data_req.get('data_devolucao', '')
        write_data(data)
        return jsonify({"message": "Veículo devolvido com sucesso", "reserva": reserva, "veiculo": veiculo})
    except Exception as e:
        print('Erro em devolver_por_veiculo:', str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/reservas/<int:reserva_id>/devolver', methods=['POST'])
@login_required
def devolver_veiculo(reserva_id):
    try:
        print(f"Tentando devolver veículo. ID da reserva: {reserva_id}")
        print(f"Usuário atual: {session.get('usuario_id')}, Tipo: {session.get('usuario_tipo')}")
        
        if not request.is_json:
            print("Erro: Requisição não é JSON")
            return jsonify({"error": "Requisição deve ser JSON"}), 400
            
        data = read_data()
        print(f"Dados carregados. Reservas encontradas: {len(data.get('reservas', []))}")
        
        # Encontrar a reserva
        reserva = next((r for r in data['reservas'] if r.get('id') == reserva_id), None)
        if not reserva:
            print(f"Erro: Reserva {reserva_id} não encontrada")
            return jsonify({"error": "Reserva não encontrada"}), 404
            
        print(f"Reserva encontrada: {reserva}")
        
        # Verificar se o usuário é o dono da reserva ou admin
        if reserva.get('usuario_id') != session.get('usuario_id') and session.get('usuario_tipo') != 'admin':
            print("Erro: Usuário não autorizado")
            return jsonify({"error": "Não autorizado"}), 403
            
        # Verificar se a reserva já foi finalizada
        if reserva.get('status') == 'finalizada':
            print("Erro: Reserva já finalizada")
            return jsonify({"error": "Esta reserva já foi finalizada"}), 400
            
        # Encontrar o veículo
        veiculo = next((v for v in data['veiculos'] if v.get('id') == reserva.get('veiculo_id')), None)
        if not veiculo:
            print(f"Erro: Veículo {reserva.get('veiculo_id')} não encontrado")
            return jsonify({"error": "Veículo não encontrado"}), 404
            
        print(f"Veículo encontrado: {veiculo}")
        
        # Atualizar status e datas
        veiculo['status'] = 'disponível'
        
        # Atualizar reserva
        data_devolucao = request.json.get('data_devolucao', '')
        reserva.update({
            'status': 'finalizada',
            'data_devolucao': data_devolucao,
            'historico': {
                'data_aluguel': reserva.get('data_reserva', ''),
                'data_devolucao': data_devolucao,
                'dias_alugados': reserva.get('dias', 0),
                'condicao_veiculo': veiculo.get('condicao', '')
            }
        })
        
        write_data(data)
        print("Dados atualizados com sucesso")
        
        return jsonify({
            "message": "Veículo devolvido com sucesso",
            "reserva": reserva,
            "veiculo": veiculo
        })
        
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return jsonify({"error": f"Erro ao devolver veículo: {str(e)}"}), 500

@app.route('/api/reservas', methods=['GET'])
@login_required
def api_get_reservas():
    try:
        data = read_data()
        reservas = []
        usuario_id = session.get('usuario_id')
        usuario_tipo = session.get('usuario_tipo')

        for reserva in data.get("reservas", []):
            # Se não for admin, retornar apenas as reservas do usuário
            if usuario_tipo != 'admin' and reserva.get("usuario_id") != usuario_id:
                continue

            veiculo_id = reserva.get("veiculo_id")
            veiculo = next((v for v in data["veiculos"] if v.get('id') == veiculo_id), None)

            if veiculo:
                reservas.append({
                    "reserva": reserva,
                    "veiculo": veiculo,
                    "valor_total": veiculo.get('preco_diaria', 0) * reserva.get('dias', 1)
                })

        return jsonify(reservas)
    except Exception as e:
        print(f"Erro ao buscar reservas: {str(e)}")
        return jsonify({"error": "Erro ao buscar reservas"}), 500

@app.route('/api/perfil', methods=['GET','POST'])
def api_perfil():
    data = read_data()
    if request.method == 'GET':
        return jsonify(data.get("perfil", {}))
    else:
        perfil = request.json or {}
        # store perfil
        data["perfil"] = perfil
        write_data(data)
        return jsonify(perfil)

if __name__ == '__main__':
    app.run(debug=True)