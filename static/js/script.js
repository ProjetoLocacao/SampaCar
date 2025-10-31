let clientes = [];

async function fetchVeiculos(filtros = {}) {
    try {
        let url = '/api/veiculos';
        if (filtros.marca || filtros.modelo) {
            const params = new URLSearchParams();
            if (filtros.marca) params.append('marca', filtros.marca);
            if (filtros.modelo) params.append('modelo', filtros.modelo);
            url += '?' + params.toString();
        }

        const resp = await fetch(url);
        if (!resp.ok) throw new Error('Erro ao buscar veículos');
        return await resp.json();
    } catch (error) {
        console.error('Erro ao buscar veículos:', error);
        return [];
    }
}

async function carregarVeiculos() {
    const veiculos = await fetchVeiculos();
    const lista = document.getElementById('veiculosList');
    if (!lista) return;

    lista.innerHTML = veiculos.map(v => `
        <div class="vehicle-card">
            ${v.foto ? `<img src="${v.foto}" alt="${v.marca} ${v.modelo}">` : ''}
            <h3>${v.marca} ${v.modelo}</h3>
            <p>Ano: ${v.ano}</p>
            <p>Condição: ${v.condicao || '-'}</p>
            <p>Placa: ${v.placa}</p>
            <p>Diária: R$ ${v.preco_diaria?.toFixed(2) || '0.00'}</p>
            <p class="status ${v.status === 'disponível' ? 'disponivel' : 'alugado'}">${v.status}</p>
            ${v.status === 'disponível' ? 
                `<button onclick="reservarVeiculo(${v.id})" class="btn-primary">Reservar</button>` : 
                '<button disabled>Indisponível</button>'}
            ${(() => {
                const currentUser = window.CURRENT_USER || { id: null, is_admin: false };
                if (currentUser.is_admin === true || currentUser.is_admin === 'true') {
                    return ` <button onclick="excluirVeiculo(${v.id})">Excluir</button>`;
                }
                if (v.owner_id && currentUser.id && v.owner_id === currentUser.id) {
                    return ` <button onclick="excluirVeiculo(${v.id})">Excluir</button>`;
                }
                return '';
            })()}
        </div>
    `).join('');
}

function atualizarGridVeiculos(veiculos) {
    const grid = document.getElementById('destaqueGrid');
    if (!grid) return;

    grid.innerHTML = veiculos.map(v => `
        <div class="card">
            ${v.foto ? `<img src="${v.foto}" alt="${v.marca} ${v.modelo}" class="card-img">` : ''}
            <div class="card-content">
                <h3>${v.marca} ${v.modelo}</h3>
                <p>Ano: ${v.ano}</p>
                <p>Diária: R$ ${v.preco_diaria?.toFixed(2) || '0.00'}</p>
                <span class="status ${v.status === 'disponível' ? 'disponivel' : 'alugado'}">${v.status}</span>
                ${v.status === 'disponível' ? 
                    `<button onclick="reservarVeiculo(${v.id})" class="btn-primary">Reservar</button>` : 
                    '<button disabled>Indisponível</button>'}
            </div>
        </div>
    `).join('');
}

async function loadDestaque(filterMarca, filterModelo) {
    try {
        const veiculos = await fetchVeiculos({ marca: filterMarca, modelo: filterModelo });
        atualizarGridVeiculos(veiculos.slice(0, 8));
    } catch (error) {
        console.error('Erro ao carregar destaques:', error);
    }
}

function formatarData(data) {
    if (!data) return '-';
    const d = new Date(data);
    return d.toLocaleDateString('pt-BR');
}

// Toast helper: cria toasts não intrusivos
function showToast(type = 'info', message = '') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.right = '20px';
        container.style.top = '20px';
        container.style.zIndex = 9999;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.style.minWidth = '200px';
    toast.style.marginTop = '8px';
    toast.style.padding = '10px 14px';
    toast.style.borderRadius = '6px';
    toast.style.color = '#fff';
    toast.style.boxShadow = '0 2px 6px rgba(0,0,0,0.2)';

    if (type === 'sucesso' || type === 'success') toast.style.background = '#28a745';
    else if (type === 'erro' || type === 'error') toast.style.background = '#dc3545';
    else toast.style.background = '#007bff';

    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => container.removeChild(toast), 500);
    }, 3500);
}

async function loadReservas() {
    const reservasArea = document.getElementById('reservasArea');
    if (!reservasArea) return;

    try {
        console.log('Iniciando carregamento de reservas...');
        const response = await fetch('/api/reservas', { credentials: 'same-origin' });
        console.log('Resposta recebida:', response.status);
        
        const data = await response.json();
        console.log('Dados recebidos:', data);

        if (!data || data.length === 0) {
            reservasArea.innerHTML = '<tr><td colspan="7" class="text-center">Você não tem reservas.</td></tr>';
            return;
        }

        let htmlContent = '';
        
        for (const item of data) {
            if (!item || !item.reserva || !item.veiculo) {
                console.log('Item inválido:', item);
                continue;
            }

            const reserva = item.reserva;
            const veiculo = item.veiculo;
            
            const statusClass = reserva.status === 'finalizada' ? 'finalizada' : 'ativa';
            const statusText = reserva.status === 'finalizada' ? 'Finalizada' : 'Em andamento';

            htmlContent += `
                <tr>
                    <td>${veiculo.marca} ${veiculo.modelo} (${veiculo.placa || '-'})</td>
                    <td>${formatarData(reserva.data_reserva)}</td>
                    <td>${reserva.status === 'finalizada' ? formatarData(reserva.data_devolucao) : '-'}</td>
                    <td>${reserva.dias} dia(s)</td>
                    <td>${veiculo.condicao || '-'}</td>
                    <td>
                        <span class="status-badge ${statusClass}">
                            ${statusText}
                        </span>
                    </td>
                    <td>
                        ${reserva.status !== 'finalizada' ? 
                            `<button onclick="iniciarDevolucao(${reserva.id})" class="btn-primary">Devolver</button>` : 
                            `<div class="info-devolucao">Devolvido</div>`
                        }
                    </td>
                </tr>
            `;
        }

        if (htmlContent === '') {
            reservasArea.innerHTML = '<tr><td colspan="7" class="text-center">Nenhuma reserva encontrada.</td></tr>';
        } else {
            reservasArea.innerHTML = htmlContent;
        }
        
        console.log('Reservas carregadas com sucesso!');
    } catch (error) {
        console.error('Erro detalhado ao carregar reservas:', error);
        reservasArea.innerHTML = '<tr><td colspan="7" class="text-center">Erro ao carregar reservas. Tente novamente mais tarde.</td></tr>';
    }
}

async function reservarVeiculo(veiculoId) {
    try {
        const dias = prompt('Por quantos dias você deseja alugar?', '1');
        if (!dias) return;

    const response = await fetch(`/api/veiculos/${veiculoId}/reservar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                dias: parseInt(dias),
                data_reserva: new Date().toISOString().split('T')[0]
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            showToast('sucesso', 'Veículo reservado com sucesso!');
            setTimeout(() => window.location.reload(), 800);
        } else {
            showToast('erro', data.error || 'Erro ao reservar veículo');
        }
    } catch (error) {
        console.error('Erro ao reservar:', error);
        showToast('erro', 'Erro ao processar reserva');
    }
}

async function cadastrarVeiculo(formData) {
    try {
        const response = await fetch('/api/veiculos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(Object.fromEntries(formData)),
                credentials: 'same-origin'
        });

        const data = await response.json();
        
        if (response.ok) {
            showToast('sucesso', 'Veículo cadastrado com sucesso!');
            document.getElementById('formVeiculo').reset();
            await carregarVeiculos();
            renderMeusVeiculos();
        } else {
            showToast('erro', data.error || 'Erro ao cadastrar veículo');
        }
    } catch (error) {
        console.error('Erro ao cadastrar:', error);
        showToast('erro', 'Erro ao processar cadastro');
    }
}

function mostrarMensagem(texto, tipo) {
    // Mantive compatibilidade com a função antiga para partes do código que ainda a chamam
    showToast(tipo === 'erro' ? 'erro' : 'sucesso', texto);
}

async function salvarPerfil(form) {
    try {
        const formData = new FormData(form);
        const perfilData = {
            nome: formData.get('nome'),
            email: formData.get('email'),
            telefone: formData.get('telefone'),
            endereco: formData.get('endereco')
        };

        const response = await fetch('/api/perfil', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(perfilData)
        });

        if (response.ok) {
            showToast('sucesso', 'Perfil salvo com sucesso!');
        } else {
            showToast('erro', 'Erro ao salvar perfil');
        }
    } catch (error) {
        console.error('Erro ao salvar perfil:', error);
        showToast('erro', 'Erro ao salvar perfil');
    }
}

document.addEventListener('DOMContentLoaded', async() => {
    // Configurar busca na página inicial
    const btnSearch = document.getElementById('btnSearch');
    const btnClear = document.getElementById('btnClear');
    const searchMarca = document.getElementById('searchMarca');
    const searchModelo = document.getElementById('searchModelo');

    if (btnSearch && btnClear) {
        // Carregar veículos iniciais
        await loadDestaque();

        // Configurar busca
        btnSearch.addEventListener('click', async () => {
            const marca = searchMarca.value.trim();
            const modelo = searchModelo.value.trim();
            await loadDestaque(marca, modelo);
        });

        // Configurar limpar
        btnClear.addEventListener('click', async () => {
            searchMarca.value = '';
            searchModelo.value = '';
            await loadDestaque();
        });

        // Buscar ao pressionar Enter
        searchMarca.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') await loadDestaque(searchMarca.value.trim(), searchModelo.value.trim());
        });
        searchModelo.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') await loadDestaque(searchMarca.value.trim(), searchModelo.value.trim());
        });
    }

    // Carregar reservas se estiver na página de reservas
    await loadReservas();
    await carregarVeiculos();
    
    // Setup do formulário de perfil
    const formPerfil = document.getElementById('formPerfil');
    if (formPerfil) {
        formPerfil.addEventListener('submit', async (e) => {
            e.preventDefault();
            await salvarPerfil(formPerfil);
        });
    }

    // Setup de clientes
    const formCliente = document.getElementById('formCliente');
    const tabelaClientes = document.getElementById('tabelaClientes');

            if (formCliente) {
                formCliente.onsubmit = function(e) {
                    e.preventDefault();
                    const nome = this.nome.value;
                    const email = this.email.value;
                    const telefone = this.telefone.value;
                    clientes.push({ nome, email, telefone });
                    mostrarClientes();
                    this.reset();
                }
            }

            function mostrarClientes() {
                if (!tabelaClientes) return;
                let tbody = '';
                clientes.forEach(c => {
                    tbody += `<tr><td>${c.nome}</td><td>${c.email}</td><td>${c.telefone}</td></tr>`;
                });
                const tbodyElement = tabelaClientes.querySelector('tbody');
                if (tbodyElement) {
                    tbodyElement.innerHTML = tbody;
                }
            }

            // Cadastro de veículos
            if (document.getElementById('formVeiculo')) {
                document.getElementById('formVeiculo').onsubmit = async function(e) {
                    e.preventDefault();
                    const marca = this.marca.value;
                    const modelo = this.modelo.value;
                    const ano = parseInt(this.ano.value);
                    const placa = this.placa ? this.placa.value : '';
                    const preco_diaria = this.preco_diaria ? parseFloat(this.preco_diaria.value) : 0;
                    const foto = this.foto ? this.foto.value : '';
                    const condicao = this.condicao ? this.condicao.value : 'usado';

                    const resp = await fetch('/api/veiculos', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ marca, modelo, ano, placa, preco_diaria, foto, condicao }),
                        credentials: 'same-origin'
                    });
                    if (resp.ok) {
                        showToast('sucesso', 'Veículo cadastrado com sucesso');
                        this.reset();
                        renderFrota();
                        await carregarVeiculos();
                        renderMeusVeiculos();
                    } else {
                        const err = await resp.json().catch(()=>({error:'Erro'}));
                        showToast('erro', err.error || 'Erro ao cadastrar');
                    }
                }
            }

            // Painel frota render atualizado: usa v.id e botão de devolução que procura reserva ativa
            async function renderFrota() {
                const veiculos = await fetchVeiculos();
                // buscar reservas para mapear por veiculo_id
                let reservasMap = {};
                try {
                    const resp = await fetch('/api/reservas', { credentials: 'same-origin' });
                    if (resp.ok) {
                        const reservas = await resp.json();
                        reservas.forEach(r => {
                            if (r && r.reserva && r.reserva.veiculo_id) {
                                reservasMap[r.reserva.veiculo_id] = r.reserva;
                            }
                        });
                    }
                } catch (e) {
                    console.warn('Não foi possível carregar reservas para painel da frota', e);
                }

                const tbody = veiculos.map((v) => {
                    const reserva = reservasMap[v.id];
                    const dataReserva = reserva && reserva.data_reserva ? reserva.data_reserva : '-';
                    const dias = reserva && reserva.dias ? reserva.dias : '-';
                    const acoes = v.status === 'disponível'
                        ? `<button onclick="reservarVeiculo(${v.id})">Reservar</button>`
                        : `<button onclick="devolverPorVeiculoId(${v.id})">Devolver</button>`;

                            // ações de admin/do dono
                            const currentUser = window.CURRENT_USER || { id: null, is_admin: false };
                            let ownerAcoes = '';
                            if (currentUser.is_admin === true || currentUser.is_admin === 'true') {
                                ownerAcoes = ` <button onclick="gerenciarVeiculo(${v.id})">Gerenciar</button> <button onclick="excluirVeiculo(${v.id})">Excluir</button>`;
                            } else if (v.owner_id && currentUser.id && v.owner_id === currentUser.id) {
                                ownerAcoes = ` <button onclick="excluirVeiculo(${v.id})">Excluir</button>`;
                            }

                            return `
            <tr>
                <td>${v.marca}</td>
                <td>${v.modelo}</td>
                <td>${v.ano}</td>
                <td>${dataReserva}</td>
                <td>${dias}</td>
                <td>${v.placa || '-'}</td>
                <td>${v.status}</td>
                <td>
                    ${acoes} ${ownerAcoes}
                </td>
            </tr>
        `}).join('');

                const table = document.querySelector("#tabelaFrota");
                if (table) table.querySelector("tbody").innerHTML = tbody;
            }

            // Devolver veículo por vehicle id: encontra reserva ativa e chama endpoint de devolução por reserva
            window.devolverPorVeiculoId = async function(veiculoId) {
                try {
                    console.log('Procurando reserva ativa para veiculo', veiculoId);
                    const resp = await fetch('/api/reservas', { credentials: 'same-origin' });
                    if (!resp.ok) throw new Error('Erro ao buscar reservas');
                    const reservas = await resp.json();

                    const reservaObj = reservas.find(r => r.reserva && r.reserva.veiculo_id === veiculoId && (r.reserva.status === 'ativa' || !r.reserva.status));
                    if (!reservaObj) {
                        showToast('info', 'Nenhuma reserva ativa encontrada para este veículo.');
                        return;
                    }

                    const reservaId = reservaObj.reserva.id;
                    const confirmar = confirm('Confirma devolução do veículo?');
                    if (!confirmar) return;

                    const dataDevolucao = new Date().toISOString().split('T')[0];
                    const devolverResp = await fetch(`/api/reservas/${reservaId}/devolver`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'same-origin',
                        body: JSON.stringify({ data_devolucao: dataDevolucao })
                    });

                    const result = await devolverResp.json();
                    if (!devolverResp.ok) {
                        showToast('erro', result.error || 'Erro ao devolver veículo');
                        console.error('Erro na devolução', result);
                        return;
                    }

                    showToast('sucesso', 'Veículo devolvido com sucesso!');
                    renderFrota();
                    renderMeusVeiculos();
                } catch (error) {
                    console.error('Erro ao devolver por veículo:', error);
                    showToast('erro', 'Erro ao devolver veículo. Veja o console para mais detalhes.');
                }
            }

            renderFrota();
            
            // Gerenciar veículo (alterar status)
            window.gerenciarVeiculo = async function(veiculoId) {
                try {
                    const novoStatus = prompt('Novo status (disponível, alugado, manutenção):');
                    if (!novoStatus) return;
                    const resp = await fetch(`/api/veiculos/${veiculoId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: novoStatus })
                    });
                    const data = await resp.json();
                    if (!resp.ok) {
                        showToast('erro', data.error || 'Erro ao atualizar veículo');
                        return;
                    }
                    showToast('sucesso', 'Veículo atualizado com sucesso');
                    renderFrota();
                } catch (e) {
                    console.error('Erro ao gerenciar veículo', e);
                    showToast('erro', 'Erro ao atualizar veículo');
                }
            }

            // Excluir veículo
            window.excluirVeiculo = async function(veiculoId) {
                try {
                    if (!confirm('Tem certeza que deseja excluir este veículo?')) return;
                    const resp = await fetch(`/api/veiculos/${veiculoId}`, { method: 'DELETE', credentials: 'same-origin' });
                    const data = await resp.json();
                    if (!resp.ok) {
                        showToast('erro', data.error || 'Erro ao excluir veículo');
                        return;
                    }
                    showToast('sucesso', 'Veículo excluído com sucesso');
                    renderFrota();
                    renderMeusVeiculos();
                } catch (e) {
                    console.error('Erro ao excluir veículo', e);
                    showToast('erro', 'Erro ao excluir veículo');
                }
            }

            // Render 'Meus Veículos' — filtra por owner_id e popula container
            async function renderMeusVeiculos() {
                const container = document.getElementById('meusVeiculosList');
                if (!container) return;

                const veiculos = await fetchVeiculos();
                const currentUser = window.CURRENT_USER || { id: null, is_admin: false };

                const meus = veiculos.filter(v => (currentUser.is_admin === true || currentUser.is_admin === 'true') ? true : (v.owner_id && currentUser.id && v.owner_id === currentUser.id));

                container.innerHTML = meus.length === 0 ? '<p>Nenhum veículo cadastrado por você.</p>' : meus.map(v => `
                    <div class="vehicle-card small">
                        ${v.foto ? `<img src="${v.foto}" alt="${v.marca} ${v.modelo}">` : ''}
                        <h4>${v.marca} ${v.modelo}</h4>
                        <p>Ano: ${v.ano} • Placa: ${v.placa || '-'}</p>
                        <p>Status: <strong>${v.status}</strong></p>
                        <div class="actions">
                            ${v.status === 'disponível' ? `<button onclick="reservarVeiculo(${v.id})">Reservar</button>` : `<button onclick="devolverPorVeiculoId(${v.id})">Devolver</button>`}
                            ${(currentUser.is_admin === true || currentUser.is_admin === 'true') || (v.owner_id && currentUser.id && v.owner_id === currentUser.id) ? ` <button onclick="excluirVeiculo(${v.id})">Excluir</button>` : ''}
                        </div>
                    </div>
                `).join('');
            }

            // Inicializar botões de 'Meus Veículos' se existirem
            const btnShowAll = document.getElementById('btnShowAll');
            const btnShowMine = document.getElementById('btnShowMine');
            if (btnShowAll) btnShowAll.addEventListener('click', async () => { await carregarVeiculos(); document.getElementById('meusVeiculosSection')?.classList.remove('visible'); });
            if (btnShowMine) btnShowMine.addEventListener('click', async () => { await renderMeusVeiculos(); document.getElementById('meusVeiculosSection')?.classList.add('visible'); });

            // chamar pela primeira vez
            renderMeusVeiculos();
});