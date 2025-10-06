/**
Ponto de entrada da aplicação React do Projeto Apollo.
Inicializa o App e aplica o CSS global e ícones de bandeiras.
Padrão seguido: Airbnb React Style Guide.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';

// Estilos globais e dependências externas
import './App.css';
import 'flag-icons/css/flag-icons.min.css';

// Componente principal da aplicação
import App from './App';

// Cria a raiz React e renderiza o aplicativo
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
