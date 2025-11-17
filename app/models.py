from .extensions import db

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    senha = db.Column(db.String(200))
    telefone = db.Column(db.String(50))
    tipo = db.Column(db.String(50))

    reservas = db.relationship('Reserva', backref='usuario', lazy=True)

class Veiculo(db.Model):
    __tablename__ = 'veiculo'
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(120))
    modelo = db.Column(db.String(120))
    placa = db.Column(db.String(30))
    ano = db.Column(db.Integer)
    status = db.Column(db.String(50))

    # ADICIONADOS:
    preco_diaria = db.Column(db.Float, nullable=True)
    foto = db.Column(db.String(255), nullable=True)      # URL ou caminho relativo em /static/uploads/
    condicao = db.Column(db.String(100), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    # relacionamento opcional com Usuario (se existir classe Usuario)
    owner = db.relationship('Usuario', backref=db.backref('veiculos', lazy=True))

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(120))
    data_reserva = db.Column(db.String(30))
    data_devolucao = db.Column(db.String(30))
    dias = db.Column(db.Integer)
    status = db.Column(db.String(50))

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculo.id'), nullable=True)

class Perfil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120))
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(255))
    telefone = db.Column(db.String(50))
    descricao = db.Column(db.Text)
