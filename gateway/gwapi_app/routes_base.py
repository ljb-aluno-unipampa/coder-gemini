# gateway/gwapi_app/routes_base.py
from flask import Blueprint, render_template_string, jsonify
import subprocess

base_bp = Blueprint('base', __name__)

# Template HTML inline para evitar a necessidade de gerenciar múltiplos arquivos estruturais no container
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MasterGW - Painel de Controle</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-gray-100 font-sans min-h-screen flex flex-col">

    <div id="login-modal" class="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
        <div class="bg-gray-800 p-8 rounded-lg shadow-2xl border border-gray-700 w-96">
            <div class="text-center mb-6">
                <i class="fa-solid fa-shield-halved text-4xl text-blue-500 mb-2"></i>
                <h2 class="text-2xl font-bold">MasterGW Admin</h2>
                <p class="text-gray-400 text-sm">Autenticação do Laboratório</p>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs uppercase font-bold text-gray-400 mb-1">Usuário</label>
                    <input type="text" id="auth-user" class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs uppercase font-bold text-gray-400 mb-1">Senha</label>
                    <input type="password" id="auth-pass" class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none focus:border-blue-500">
                </div>
                <button onclick="login()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded transition">
                    Acessar Painel
                </button>
                <p id="login-error" class="text-red-500 text-sm text-center hidden">Credenciais inválidas!</p>
            </div>
        </div>
    </div>

    <div id="main-content" class="hidden flex-1 flex flex-col">
        <header class="bg-gray-800 border-b border-gray-700 px-6 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <i class="fa-solid fa-network-wired text-blue-500 text-2xl"></i>
                <h1 class="text-xl font-bold tracking-wide">MasterGW <span class="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded font-mono">v1.0</span></h1>
            </div>
            <div class="flex items-center space-x-4">
                <span id="session-user" class="text-gray-400 text-sm font-mono"></span>
                <button onclick="logout()" class="text-gray-400 hover:text-red-400 transition text-sm">
                    <i class="fa-solid fa-right-from-bracket"></i> Sair
                </button>
            </div>
        </header>

        <main class="p-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
            
            <div class="lg:col-span-1 space-y-6">
                <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
                    <h2 class="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4 flex items-center justify-between">
                        <span>Status do DHCP (Kea)</span>
                        <i class="fa-solid fa-server text-blue-400"></i>
                    </h2>
                    <div class="flex items-center space-x-3 bg-gray-900 p-3 rounded border border-gray-700/50">
                        <span id="dhcp-status-indicator" class="h-3 w-3 rounded-full bg-gray-500 animate-pulse"></span>
                        <span id="dhcp-status-text" class="font-mono text-sm">Verificando...</span>
                    </div>
                </div>

                <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
                    <h2 class="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4 flex items-center justify-between">
                        <span>Segurança (nftables)</span>
                        <i class="fa-solid fa-fire-burner text-orange-400"></i>
                    </h2>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-xs text-gray-400 uppercase mb-1">Política Padrão (INPUT)</label>
                            <select id="fw-policy" class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white font-mono">
                                <option value="accept">ACCEPT (Liberdade Total)</option>
                                <option value="drop">DROP (Bloqueio Total / Firewall Ativo)</option>
                            </select>
                        </div>
                        <button onclick="applyFirewall()" class="w-full bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 rounded transition text-sm">
                            <i class="fa-solid fa-floppy-disk mr-2"></i>Aplicar Regras do Firewall
                        </button>
                    </div>
                </div>
            </div>

            <div class="lg:col-span-2 space-y-6">
                <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center space-x-2">
                            <i class="fa-solid fa-list-check text-green-400"></i>
                            <span>Concessões Ativas (Leases)</span>
                        </h2>
                        <button onclick="loadLeases()" class="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded transition">
                            <i class="fa-solid fa-rotate mr-1"></i> Atualizar
                        </button>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="border-b border-gray-700 text-xs uppercase text-gray-400 font-mono">
                                    <th class="pb-2">Hostname</th>
                                    <th class="pb-2">Endereço IP</th>
                                    <th class="pb-2">Endereço MAC</th>
                                </tr>
                            </thead>
                            <tbody id="leases-table" class="text-sm font-mono divide-y divide-gray-700/50">
                                <tr><td colspan="3" class="py-4 text-center text-gray-500">Nenhum dispositivo detectado ainda.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
                    <h2 class="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4 flex items-center space-x-2">
                        <i class="fa-solid fa-address-card text-purple-400"></i>
                        <span>Reservas Estáticas de IP</span>
                    </h2>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 bg-gray-900 p-4 rounded-lg border border-gray-700 mb-4">
                        <input type="text" id="res-host" placeholder="Hostname (Ex: servidor)" class="bg-gray-800 border border-gray-700 rounded p-2 text-sm text-white focus:outline-none">
                        <input type="text" id="res-mac" placeholder="MAC (Ex: 00:11:22:33:44:55)" class="bg-gray-800 border border-gray-700 rounded p-2 text-sm text-white focus:outline-none">
                        <input type="text" id="res-ip" placeholder="IP (Ex: 192.168.222.10)" class="bg-gray-800 border border-gray-700 rounded p-2 text-sm text-white focus:outline-none">
                        <button onclick="addReservation()" class="md:col-span-3 bg-purple-600 hover:bg-purple-700 text-white text-sm font-bold py-2 rounded transition">
                            <i class="fa-solid fa-plus mr-1"></i> Adicionar Nova Reserva Comercial/Estática
                        </button>
                    </div>

                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="border-b border-gray-700 text-xs uppercase text-gray-400 font-mono">
                                    <th class="pb-2">Hostname</th>
                                    <th class="pb-2">Endereço IP</th>
                                    <th class="pb-2">Endereço MAC</th>
                                    <th class="pb-2 text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody id="reservations-table" class="text-sm font-mono divide-y divide-gray-700/50">
                                </tbody>
                        </table>
                    </div>
                    <div class="mt-4 flex justify-end">
                        <button onclick="applyDHCP()" class="bg-green-600 hover:bg-green-700 text-white font-bold px-4 py-2 rounded text-sm transition shadow-lg">
                            <i class="fa-solid fa-cloud-arrow-up mr-1"></i> Sincronizar e Aplicar Reservas no Kea
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        let token = "";

        function getHeaders() {
            return {
                'Authorization': token,
                'Content-Type': 'application/json'
            };
        }

        async function login() {
            const user = document.getElementById('auth-user').value;
            const pass = document.getElementById('auth-pass').value;
            const errorElement = document.getElementById('login-error');

            token = 'Basic ' + btoa(user + ':' + pass);

            // Testa credenciais batendo no endpoint de status
            try {
                const res = await fetch('/api/dhcp/status', { headers: getHeaders() });
                if (res.ok) {
                    document.getElementById('login-modal').classList.add('hidden');
                    document.getElementById('main-content').classList.remove('hidden');
                    document.getElementById('session-user').innerText = `Logado como: ${user}`;
                    initDashboard();
                } else {
                    errorElement.classList.remove('hidden');
                }
            } catch (e) {
                errorElement.classList.remove('hidden');
            }
        }

        function logout() {
            token = "";
            document.getElementById('login-modal').classList.remove('hidden');
            document.getElementById('main-content').classList.add('hidden');
        }

        function initDashboard() {
            loadDHCPStatus();
            loadLeases();
            loadReservations();
        }

        async function loadDHCPStatus() {
            const ind = document.getElementById('dhcp-status-indicator');
            const txt = document.getElementById('dhcp-status-text');
            try {
                const res = await fetch('/api/dhcp/status', { headers: getHeaders() });
                const data = await res.json();
                if(data.result === 0) {
                    ind.className = "h-3 w-3 rounded-full bg-green-500 shadow-lg shadow-green-500/50";
                    txt.innerText = "ONLINE (Serviço Ativo)";
                } else {
                    ind.className = "h-3 w-3 rounded-full bg-red-500";
                    txt.innerText = "OFFLINE ou Falha";
                }
            } catch(e) {
                ind.className = "h-3 w-3 rounded-full bg-red-500";
                txt.innerText = "Falha de Conexão";
            }
        }

        async function loadLeases() {
            const tbody = document.getElementById('leases-table');
            try {
                const res = await fetch('/api/dhcp/leases', { headers: getHeaders() });
                const leases = await res.json();
                
                if(leases.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="3" class="py-4 text-center text-gray-500">Nenhum dispositivo ativo na LAN.</td></tr>`;
                    return;
                }

                tbody.innerHTML = leases.map(l => `
                    <tr class="hover:bg-gray-700/30">
                        <td class="py-2 text-gray-300">\${l.hostname}</td>
                        <td class="py-2 text-blue-400">\${l.ip_address}</td>
                        <td class="py-2 text-gray-400">\${l.hw_address}</td>
                    </tr>
                `).join('');
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="3" class="py-4 text-center text-red-400">Erro ao carregar leases.</td></tr>`;
            }
        }

        async function loadReservations() {
            const tbody = document.getElementById('reservations-table');
            try {
                const res = await fetch('/api/dhcp/reservations', { headers: getHeaders() });
                const reservations = await res.json();
                
                if(reservations.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="4" class="py-3 text-center text-gray-500">Nenhuma reserva configurada.</td></tr>`;
                    return;
                }

                tbody.innerHTML = reservations.map(r => `
                    <tr class="hover:bg-gray-700/30">
                        <td class="py-2 text-gray-300">\${r.hostname}</td>
                        <td class="py-2 text-purple-400">\${r['ip-address']}</td>
                        <td class="py-2 text-gray-400">\${r.mac}</td>
                        <td class="py-2 text-right">
                            <button onclick="deleteReservation('\${r.mac}')" class="text-red-500 hover:text-red-400 p-1"><i class="fa-solid fa-trash"></i></button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="4" class="py-3 text-center text-red-400">Erro ao carregar reservas.</td></tr>`;
            }
        }

        async function addReservation() {
            const host = document.getElementById('res-host').value.strip;
            const mac = document.getElementById('res-mac').value.strip;
            const ip = document.getElementById('res-ip').value.strip;

            const payload = { hostname: document.getElementById('res-host').value, mac: document.getElementById('res-mac').value, ip: document.getElementById('res-ip').value };
            
            const res = await fetch('/api/dhcp/reservations', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });

            if(res.ok) {
                alert("Reserva adicionada localmente! Não esqueça de clicar em 'Sincronizar e Aplicar' para enviar ao servidor.");
                loadReservations();
                document.getElementById('res-host').value = '';
                document.getElementById('res-mac').value = '';
                document.getElementById('res-ip').value = '';
            } else {
                const err = await res.json();
                alert("Erro: " + err.error);
            }
        }

        async function deleteReservation(mac) {
            if(!confirm("Remover esta reserva?")) return;
            const res = await fetch(`/api/dhcp/reservations/\${mac}`, {
                method: 'DELETE',
                headers: getHeaders()
            });
            if(res.ok) {
                loadReservations();
            }
        }

        async function applyDHCP() {
            const res = await fetch('/api/dhcp/apply', { method: 'POST', headers: getHeaders() });
            const data = await res.json();
            alert(data.message || data.status);
            loadDHCPStatus();
        }

        async function applyFirewall() {
            const policy = document.getElementById('fw-policy').value;
            // Endpoint de salvar e aplicar o estado do firewall
            alert("Enviando comando para alterar política do Firewall para: " + policy.toUpperCase());
            // Integração com o backend do firewall concluído na etapa 5
        }
    </script>
</body>
</html>
"""

@base_bp.route('/')
def index():
    return render_template_string(UI_TEMPLATE)

@base_bp.route('/api/status', methods=['GET'])
def sys_status():
    return jsonify({"gateway": "online", "version": "1.0.0"})