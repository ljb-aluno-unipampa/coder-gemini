# Orquestrador Dinâmico de Infraestrutura de Rede e Segurança para Ambientes Containerizados

Este repositório contém o artefato de software desenvolvido para o projeto de Mestrado focado na automação, gerenciamento e segurança de redes locais virtuais baseadas em containers Docker. O sistema integra um servidor **Kea DHCP**, um firewall programável **nftables**, e uma **API RESTful (Flask)** protegida por autenticação para fornecer controle programático e visual (Interface Web) sobre a alocação de endereços e políticas de controle de acesso.

---

## 1. Arquitetura do Sistema

O ambiente é inteiramente orquestrado via Docker Compose, dividindo-se em duas zonas lógicas principais:

* **Gateway (`gateway`):** Atua como o nó central de borda (roteador). Executa o motor DHCP (Kea), o subsistema de filtragem de pacotes (`nftables`) e a API de gerenciamento (`Flask`). Possui duas interfaces: uma conectada à WAN (Internet do Host) e outra dedicada à LAN virtual.
* **Clientes (`client1`, `client2`):** Containers simulando estações de trabalho na rede local interna. Eles não possuem IPs estáticos definidos pelo Docker; dependem puramente de requisições broadcast (`DHCPDISCOVER`) destinadas ao Gateway para obter conectividade.

```txt
[ Máquina Host / WAN ]
             │
┌──────────────▼────────────────────────────────┐
│ NODULO GATEWAY (Ubuntu 24.04)                 │
│                                               │
│  ┌───────────┐   ┌────────────┐   ┌────────┐  │
│  │ Flask API │◄─►│ nftables   │◄─►│ Kea    │  │
│  │ (Port 5000│   │ (Firewall) │   │ DHCP4  │  │
│  └─────▲─────┘   └────────────┘   └───▲────┘  │
└────────┼──────────────────────────────┼───────┘
│ (Interface Web / API)        │ (LAN Virtual: eth0)
│                              ▼
┌────────┴──────────────────────────────────────┐
│ REDE LOCAL INTERNA (Subrede: 192.168.222.0/24)│
│                                               │
│   ┌───────────┐               ┌───────────┐   │
│   │  client1  │               │  client2  │   │
│   └───────────┘               └───────────┘   │
└───────────────────────────────────────────────┘
```

---

## 2. Pré-requisitos e Dependências

Para implantar e reproduzir os experimentos deste laboratório, os seguintes componentes devem estar previamente instalados no sistema operacional host:

* **Docker Linux Engine** (v20.10.0 ou superior)
* **Docker Compose V2** (v2.20.0 ou superior)
* **Cliente cURL** ou navegador web moderno para testes de interface.

---

## 3. Estrutura de Diretórios do Projeto

```text
.
├── docker-compose.yml          # Definição e interconexão dos serviços e redes Docker
├── .env                        # Variáveis de ambiente globais (Escopos, IPs e Senhas)
└── gateway/
    ├── Dockerfile              # Construção da imagem do Gateway (Ubuntu 24.04 + Kea + nftables)
    ├── start-gateway.sh        # Script automatizado de boot, limpeza de cache e permissões
    ├── gwapi_app/              # Código-fonte do Barramento API e Interface Web
        ├── auth.py             # Middleware de segurança (HTTP Basic Authentication)
        ├── firewall.py         # Abstração de controle e persistência de regras nftables
        ├── routes_base.py      # Renderizador da Interface Web SPA (Tailwind CSS)
        └── routes_dhcp.py      # Endpoints HTTP para manipulação de Leases e Reservas
    └── gwapi.py                # Inicializador e ponto de entrada do servidor Flask
└── client/
    ├── Dockerfile              # Construção da imagem dos clientes DHCP
    └── start-client.sh         # Script de solicitação de endereço via DHCP
```

## 4. Instruções de Instalação e Inicialização
Siga os passos abaixo para construir o ambiente isolado eliminando qualquer persistência indesejada de cache:


1. Clone o repositório institucional do projeto

```bash
git clone https://github.com/ljb-aluno-unipampa/coder-gemini.git
cd coder-gemini
```

2. Garanta a execução limpa derrubando resquícios de redes anteriores

```bash
docker compose down --remove-orphans
```

3. Construa a imagem do Gateway forçando o descarte de cache das camadas

```bash
docker compose build --no-cache gateway
```

4. Inicie o laboratório de redes em modo de segundo plano (background)

```bash
docker compose up -d
```

## 5. Protocolo de Validação dos Experimentos
5.1 Verificação de Boot dos Serviços Internos
Para inspecionar o comportamento e certificar-se de que os daemons do Kea DHCP e da API Flask inicializaram sem colisões de permissões de arquivo ou falhas de PID, execute:

```bash
docker logs gateway
```

O log deve atestar a descoberta automática das interfaces WAN/LAN e confirmar o binding do servidor HTTP Flask na porta de escuta pública.

5.2 Validação de Atribuição de Endereçamento Dinâmico (DHCP Leases)
Consulte o estado atual de concessão de IPs gerados pelos clientes na LAN realizando uma chamada autenticada à API via terminal do host:

```bash
curl -u admin:Mestrado2026! http://localhost:5000/api/dhcp/leases
```

Retorno Esperado (Formato JSON):

```json
[
  {
    "ip_address": "192.168.222.50",
    "hw_address": "02:42:c0:a8:de:03",
    "hostname": "client1",
    "valid_lifetime": "4000"
  }
]
```

## 6. Interface de Gerenciamento Web (Dashboard UI)
O ecossistema dispõe de um painel administrativo visual embarcado. Para acessá-lo, utilize um navegador na máquina host e navegue até o endereço:

URL de Acesso: http://localhost:5000

Funcionalidades Disponíveis no Painel:
Autenticação Integrada: Controle de sessão via credenciais administrativas centralizadas (admin / Mestrado2026!).

Monitor de Status Base: Indicador visual em tempo real da saúde operacional do daemon do Kea DHCP.

Tabela de Leases Ativas: Mapeamento instantâneo de quais containers estão conectados no barramento privado da rede.

Injetor de Reservas Estáticas: Formulário dedicado para cadastro de endereços IP fixos associados a endereços MAC específicos, permitindo a sincronização em tempo real das alterações ao motor do Kea sem a necessidade de reiniciar o container do gateway.
