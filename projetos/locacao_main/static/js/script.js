let clientes = [];
let veiculos = [
    {marca: "Fiat", modelo: "Uno", ano: 2020, status: "disponível"},
    {marca: "Chevrolet", modelo: "Onix", ano: 2021, status: "alugado"}
];

// Cadastro de clientes
if(document.getElementById('formCliente')) {
    document.getElementById('formCliente').onsubmit = function(e) {
        e.preventDefault();
        const nome = this.nome.value;
        const email = this.email.value;
        const telefone = this.telefone.value;
        clientes.push({nome, email, telefone});
        mostrarClientes();
        this.reset();
    };
    function mostrarClientes() {
        let html = "<ul>";
        clientes.forEach(c => {
            html += `<li>${c.nome} - ${c.email} - ${c.telefone}</li>`;
        });
        html += "</ul>";
        document.getElementById('clientesList').innerHTML = html;
    }
}

// Cadastro de veículos
if(document.getElementById('formVeiculo')) {
    document.getElementById('formVeiculo').onsubmit = function(e) {
        e.preventDefault();
        const marca = this.marca.value;
        const modelo = this.modelo.value;
        const ano = this.ano.value;
        veiculos.push({marca, modelo, ano, status: "disponível"});
        mostrarVeiculos();
        this.reset();
    };
    function mostrarVeiculos() {
        let html = "<ul>";
        veiculos.forEach(v => {
            html += `<li>${v.marca} ${v.modelo} ${v.ano} - ${v.status}</li>`;
        });
        html += "</ul>";
        document.getElementById('veiculosList').innerHTML = html;
    }
}

// Painel da frota
if(document.getElementById('tabelaFrota')) {
    function renderFrota() {
        let tbody = "";
        veiculos.forEach((v, i) => {
            tbody += `<tr>
                <td>${v.marca}</td>
                <td>${v.modelo}</td>
                <td>${v.ano}</td>
                <td>${v.status}</td>
                <td>
                    <button onclick="alugarVeiculo(${i})" ${v.status === "alugado" ? "disabled" : ""}>Alugar</button>
                    <button onclick="devolverVeiculo(${i})" ${v.status === "disponível" ? "disabled" : ""}>Devolver</button>
                </td>
            </tr>`;
        });
        document.querySelector("#tabelaFrota tbody").innerHTML = tbody;
    }
    window.alugarVeiculo = function(i) {
        veiculos[i].status = "alugado";
        renderFrota();
    }
    window.devolverVeiculo = function(i) {
        veiculos[i].status = "disponível";
        renderFrota();
    }
    renderFrota();
}