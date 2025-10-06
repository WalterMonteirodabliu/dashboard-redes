/**
 Interface principal do Projeto Apollo — Painel de Comando.
 Exibe o throughput de rede em tempo real e o diário de bordo (alertas de segurança).
 Comunicação com o backend é feita via WebSocket.
 */

import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import './App.css';

/**
 TrafficChart
 Exibe o gráfico de throughput em tempo real (Kbps).
 */
const TrafficChart = ({ history }) => {
  const option = {
    backgroundColor: 'transparent',
    title: {
      text: 'Telemetria de Rede (Throughput)',
      textStyle: { color: '#e94560' }
    },
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['Throughput (Kbps)'],
      textStyle: { color: '#fff' }
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: history.timestamps,
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value} Kbps', color: '#fff' }
    },
    series: [
      {
        name: 'Throughput (Kbps)',
        type: 'line',
        data: history.data,
        smooth: true,
        areaStyle: { color: '#e94560' },
        lineStyle: { color: '#e94560' }
      }
    ]
  };

  return (
    <ReactECharts option={option} style={{ height: '500px', width: '100%' }} />
  );
};

/**
 AlertLog
 Exibe o diário de bordo de segurança, com alertas emitidos pelo IPS.
 */
const AlertLog = ({ alerts }) => (
  <div className="alerts-log">
    <h2>Diário de Bordo da Missão</h2>
    <ul>
      {alerts.map((alert, index) => (
        <li
          key={index}
          className={`alert-item alert-${alert.severity?.toLowerCase()}`}
        >
          <div className="alert-header">
            <span className="alert-ip">
              {/* Ícone da bandeira do país de origem */}
              <span
                className={`fi fi-${alert.geo?.country_code?.toLowerCase()}`}
              ></span>
              {alert.ip}
            </span>
            {/* Horário formatado da ocorrência */}
            <span className="alert-time">
              {new Date(alert.timestamp * 1000).toLocaleTimeString()}
            </span>
          </div>
          <span className="alert-hostname">{alert.geo?.hostname}</span>
          <span className="alert-reason">{alert.reason}</span>
          <span className="alert-action">{alert.action}</span>
        </li>
      ))}
    </ul>
  </div>
);

/**
 Componente principal da aplicação. Gerencia a comunicação WebSocket,
 o estado dos dados de throughput e os alertas de segurança.
 */
function App() {
  /** Histórico do throughput (timestamps + valores em Kbps) */
  const [throughputHistory, setThroughputHistory] = useState({
    timestamps: [],
    data: []
  });

  /** Lista de alertas de segurança emitidos pelo backend */
  const [alerts, setAlerts] = useState([]);

  /** Indica se há conexão ativa com o backend */
  const [isConnected, setIsConnected] = useState(false);

  /** Referência persistente para o WebSocket */
  const ws = useRef(null);

  /**
   * Efeito responsável por abrir e manter a conexão com o backend via WebSocket.
   * Reconecta automaticamente em caso de falha.
   */
  useEffect(() => {
    function connect() {
      ws.current = new WebSocket('ws://localhost:8000/ws/data');

      ws.current.onopen = () => setIsConnected(true);

      ws.current.onclose = () => {
        setIsConnected(false);
        // Tenta reconectar após 5 segundos
        setTimeout(connect, 5000);
      };

      ws.current.onmessage = (event) => {
        const message = JSON.parse(event.data);

        // Atualiza dados de throughput
        if (message.type === 'throughput_data') {
          const timestamp = Object.keys(message.payload)[0];
          const data = message.payload[timestamp];

          setThroughputHistory((prev) => {
            const kbps = ((data.bytes_total || 0) * 8) / 1024;
            const time = new Date(parseInt(timestamp) * 1000).toLocaleTimeString();

            return {
              timestamps: [...prev.timestamps, time].slice(-60),
              data: [...prev.data, kbps.toFixed(2)].slice(-60)
            };
          });
        }

        // Adiciona novos alertas de segurança
        else if (message.type === 'security_alert') {
          setAlerts((prev) => [message.payload, ...prev.slice(0, 49)]);
        }
      };
    }

    connect();

    // Fecha o WebSocket ao desmontar o componente
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  return (
    <div className="App">
      {/* Cabeçalho principal do painel */}
      <header className="App-header">
        <h1>Projeto Apollo - Painel de Comando</h1>
        <div className="status">
          Link com o Centro de Controle:{' '}
          <span style={{ color: isConnected ? '#52c41a' : '#e94560' }}>
            {isConnected ? 'Ativo' : 'Inativo'}
          </span>
        </div>
      </header>

      {/* Conteúdo principal */}
      <main className="main-content">
        <div className="chart-container">
          <TrafficChart history={throughputHistory} />
        </div>
        <AlertLog alerts={alerts} />
      </main>
    </div>
  );
}

export default App;
