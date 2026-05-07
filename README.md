# 🏙️🔍 Fiscaliza DF: Engenharia de Transparência Pública

[![Licença](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Tailwind](https://img.shields.io/badge/UI-Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

> **"Zeladoria urbana inteligente para um Distrito Federal mais transparente."**

O **Fiscaliza DF** é um ecossistema de software de alto impacto projetado para modernizar a interação entre o cidadão e a gestão pública do Distrito Federal. Através de uma interface minimalista e funcional, a plataforma permite o reporte geolocalizado de incidentes urbanos e oferece um painel administrativo robusto para auditoria e resolução de demandas.

---

## 1. 📋 Visão Geral do Projeto

O sistema foi concebido para resolver o gap de comunicação entre a população e os órgãos governamentais. Ele opera em três frentes principais:
*   **Captura de Dados:** Interface intuitiva para o cidadão relatar problemas com fotos e coordenadas precisas.
*   **Gestão Governamental:** Painel restrito para análise, resposta e atualização de status em tempo real.
*   **Transparência Ativa:** Dashboards públicos que mostram estatísticas reais de eficiência do governo.

---

## 2. 🚀 Funcionalidades Principais

### Portal do Cidadão
*   **Relato com Geolocalização:** Captura automática ou manual de Latitude/Longitude.
*   **Upload Inteligente:** Suporte a imagens de até 5MB com validação de segurança.
*   **Segurança Anti-Bot:** Implementação de desafio lógico dinâmico e *Honeypot* para evitar spam.
*   **Mapa Interativo:** Visualização de ocorrências em todo o território do DF.

### Painel Administrativo (Fiscaliza Admin)
*   **Gestão de Protocolos:** Fluxo completo de `Aberto`, `Em Análise` e `Resolvido`.
*   **Anotações e Chat Interno:** Registro histórico de interações entre gestor e cidadão dentro de cada chamado.
*   **Trilha de Auditoria:** Banco de dados que registra cada mudança de status para controle interno.
*   **Exportação de Inteligência:** Botão para exportação instantânea de dados em CSV para análise em BI.

---

## 3. 🛠️ Stack Tecnológica

O projeto utiliza o conceito de **Full-Stack Light**, priorizando velocidade de carregamento e facilidade de manutenção:

*   **Linguagem:** [Python 3](https://www.python.org/)
*   **Framework Web:** [Flask](https://flask.palletsprojects.com/) (Roteamento e lógica de servidor)
*   **Banco de Dados:** [SQLite](https://sqlite.org/) (Persistência de dados local)
*   **Estilização:** [Tailwind CSS](https://tailwindcss.com/) (Design responsivo e moderno)
*   **Manipulação de Dados:** [Pandas](https://pandas.pydata.org/) (Processamento de relatórios CSV)

---

## 4. 🗄️ Arquitetura do Banco de Dados

O banco de dados `database.db` é estruturado em três tabelas integradas:

*   **`reports`**: Entidade principal que armazena categoria, RA (Região Administrativa), descrição, fotos, coordenadas e dados do relator (Nome/CPF).
*   **`history`**: Tabela de log que armazena mudanças de status para transparência governamental.
*   **`comments`**: Sistema de chat vinculado a cada protocolo.

---

## 5. 💻 Instalação e Execução

Para rodar o **Fiscaliza DF** em seu ambiente local (Windows, Linux ou macOS), siga estas etapas:

### Pré-requisitos
*   Python 3.10 ou superior instalado.

### Passo a Passo

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-usuario/fiscaliza-df.git
    cd fiscaliza-df
    ```

2.  **Crie um ambiente virtual (Opcional, mas recomendado):**
    ```bash
    python -m venv venv
    # No Windows:
