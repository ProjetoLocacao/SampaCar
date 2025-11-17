from .models import Usuario, Veiculo, Perfil
from .extensions import db
from werkzeug.security import generate_password_hash

def seed_db():
    if hasattr(Usuario, 'query') and Usuario.query.first():
        return
    admin = Usuario(nome='Admin', email='admin@locacar.com', senha=generate_password_hash('admin123'), telefone='', tipo='admin')
    user1 = Usuario(nome='aa', email='aa@example.com', senha=generate_password_hash('patata45@'), telefone='11945112538', tipo='usuario')
    db.session.add_all([admin, user1])
    v1 = Veiculo(marca='Fiat', modelo='Uno', placa='ABC1234', ano=2020, status='disponível')
    v2 = Veiculo(marca='Toyota', modelo='Corolla', placa='XYZ9876', ano=2019, status='disponível')
    v3 = Veiculo(marca='Hyundai', modelo='HB20', placa='HB20000', ano=2021, status='manutenção')
    db.session.add_all([v1,v2,v3])
    perfil = Perfil(nome='Locacar', email='contato@locacar.com', endereco='Rua Exemplo, 123', telefone='11999999999', descricao='Locadora de veículos exemplar.')
    db.session.add(perfil)
    db.session.commit()
