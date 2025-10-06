\# Dashboard e IPS de Tráfego de Servidor em Tempo Real



\## Descrição do Projeto

Este projeto implementa um \*\*Dashboard de Tráfego de Servidor em Tempo Real\*\* com funcionalidades de \*\*Sistema de Prevenção de Intrusões (IPS)\*\*. Ele monitora o tráfego de rede de um servidor específico, detecta atividades suspeitas e bloqueia IPs maliciosos, enquanto visualiza os dados de tráfego e alertas de segurança em uma interface web interativa.



O sistema é dividido em duas partes principais:



\### Backend (Python com FastAPI)

\- Captura e analisa pacotes de rede em tempo real usando `scapy`.

\- Agrega dados de tráfego em janelas de 5 segundos, incluindo volume de entrada/saída, IPs de clientes e distribuição por protocolo.

\- Implementa um motor IPS para detectar:

&nbsp;   - \*\*Scans de portas\*\* (TCP Null Scan, TCP FIN Scan, Port Scan).

&nbsp;   - \*\*Ataques baseados em assinatura\*\* (SQL Injection, Path Traversal, XSS).

\- Bloqueia IPs detectados como maliciosos usando `iptables` por um período configurável.

\- Fornece dados de tráfego e alertas de segurança em tempo real via \*\*WebSockets\*\* para o frontend.



\### Frontend (React.js com ECharts)

\- Conecta-se ao backend via WebSocket para receber atualizações em tempo real.

\- Exibe gráficos interativos de tráfego de rede, mostrando:

&nbsp;   - Tráfego de entrada e saída por cliente.

&nbsp;   - Distribuição de tráfego por protocolo para clientes selecionados.

\- Apresenta um \*\*Log de Segurança\*\* em tempo real com os alertas detectados pelo IPS, incluindo timestamp, IP, razão e ação tomada (BLOQUEADO).

\- Interface responsiva e intuitiva para monitoramento contínuo.



---



\## Funcionalidades Principais



| Funcionalidade           | Descrição                                                                                                   |

| :----------------------- | :---------------------------------------------------------------------------------------------------------- |

| \*\*Monitoramento de Tráfego\*\* | Visualização em tempo real do volume de dados de entrada e saída, por cliente e por protocolo.              |

| \*\*Detecção de Intrusões\*\* | Identificação de scans de portas e ataques comuns (SQL Injection, XSS, Path Traversal) via assinaturas.     |

| \*\*Bloqueio Automático de IP\*\* | Bloqueio dinâmico de IPs maliciosos usando `iptables` para mitigar ameaças.                                |

| \*\*Alertas em Tempo Real\*\* | Notificações instantâneas de segurança exibidas no dashboard.                                               |

| \*\*Interface Interativa\*\* | Dashboard web construído com React.js e ECharts para visualização de dados e alertas.                       |



---



\## Pré-requisitos



\### Backend

\- Python 3.10 ou superior

\- Permissões de administrador/root para captura de pacotes (necessário para `scapy` e `iptables`)

\- Variável de ambiente `SERVER\_IP` configurada com o IP do servidor a ser monitorado.



\### Frontend

\- Node.js (versão recomendada: 18.x ou superior)

\- npm ou yarn



---



\## Instalação e Execução



\### 1. Clonar o Repositório

```bash

git clone <URL\_DO\_REPOSITORIO>

cd <NOME\_DO\_REPOSITORIO>

```



\### 2. Configuração do Backend



\#### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do diretório `backend` com o seguinte conteúdo:

```

SERVER\_IP="<SEU\_IP\_DO\_SERVIDOR>"

```

Substitua `<SEU\_IP\_DO\_SERVIDO>` pelo endereço IP da interface de rede que você deseja monitorar.



\#### Instalação das Dependências

```bash

cd backend

pip install -r requirements.txt

```

(Assumindo que você criará um `requirements.txt` com as dependências: `fastapi`, `uvicorn`, `python-dotenv`, `scapy`, `asyncio`, `pandas`, `collections`)



\#### Execução

Para iniciar o backend, é necessário executá-lo com permissões de root devido à captura de pacotes e manipulação de `iptables`.

```bash

sudo python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

```

Ou, se preferir usar `gunicorn` para produção:

```bash

sudo gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000

```



\### 3. Configuração do Frontend



\#### Instalação das Dependências

```bash

cd frontend

npm install

\# ou yarn install

```



\#### Execução

```bash

npm start

\# ou yarn start

```

O frontend será iniciado em `http://localhost:3000`.



---



\## Estrutura do Projeto



```

. (raiz do projeto)

├── backend/

│   ├── app/

│   │   ├── \_\_init\_\_.py

│   │   ├── app.py             # Aplicação FastAPI principal, WebSockets, inicialização do sniffer

│   │   ├── sniffer.py         # Lógica de captura e processamento de pacotes com Scapy

│   │   ├── ips\_engine.py      # Motor de detecção de intrusões (scans, assinaturas)

│   │   ├── response\_actions.py # Funções para bloquear IPs e gerenciar alertas

│   │   └── aggregator.py      # Agregação de dados de tráfego em janelas de tempo

│   ├── .env                 # Variáveis de ambiente (SERVER\_IP)

│   └── requirements.txt     # Dependências Python

├── frontend/

│   ├── public/

│   │   └── index.html         # Arquivo HTML principal

│   ├── src/

│   │   ├── App.js             # Componente principal do React, lógica do WebSocket, gráficos ECharts

│   │   ├── App.css            # Estilos CSS para o dashboard

│   │   └── index.js           # Ponto de entrada do React

│   ├── package.json         # Dependências e scripts do Frontend

│   └── README.md            # (Este arquivo)

└── README\_novo.md           # O novo README gerado

```



---



\## Tecnologias Utilizadas



\- \*\*Backend\*\*: Python, FastAPI, Scapy, Uvicorn, python-dotenv

\- \*\*Frontend\*\*: React.js, ECharts, WebSockets

\- \*\*Segurança\*\*: iptables



---



\## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests para melhorias, correção de bugs ou novas funcionalidades.





