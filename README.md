# Contrax: Sistema Inteligente de Gestão de Contratos (CLM)

## 📌 Visão Geral
### Tecnologias
![Python](https://img.shields.io/badge/Python_3.10+-black?style=flat-square&logo=python&logoColor=FFE873)
![Streamlit](https://img.shields.io/badge/Streamlit-black?style=flat-square&logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-black?style=flat-square&logo=supabase&logoColor=white)
![AI Powered](https://img.shields.io/badge/AI_Powered-black?style=flat-square&logo=googlegemini&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-black?style=flat-square&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-black?style=flat-square&logo=plotly&logoColor=white)

**Contrax** é uma plataforma de *Contract Lifecycle Management* (CLM) desenvolvida para centralizar e automatizar a gestão financeira de contratos corporativos.

O projeto foi criado para resolver dores reais da empresa goiana **Hcompany (Grupo H Egídio)**, substituindo planilhas descentralizadas, lentas e suscetíveis a erros humanos por uma aplicação robusta que gerencia ciclo de vida, pagamentos recorrentes e renovações. O grande diferencial é a utilização de **Inteligência Artificial (Google Gemini)** para leitura automática de faturas e preenchimento de lançamentos financeiros.

## Problema identificado:

* Lançamento manual de dezenas de parcelas mensais
* Dificuldade em rastrear status de pagamentos
* Relatórios consolidados custosos de gerar
* Risco de perda de prazos e renovações contratuais
* Falta de visibilidade gerencial sobre despesas

# Solução Técnica

## Arquitetura
O sistema foi construído seguindo princípios de separação de responsabilidades:

* **Arquitetura Modular:** O projeto não é apenas um script; possui separação clara de responsabilidades (`core`, `services`, `pages`, `utils`) facilitando a manutenção.
* **Automação com IA:** Módulo integrado que lê PDFs de notas fiscais e extrai valores e números de documentos automaticamente.
* **Segurança:** Gestão de ambientes (Homologação/Produção) e credenciais via `st.secrets`.
* **Dashboard Interativo:** Visualização de dados financeiros em tempo real com filtros dinâmicos.

## 🛠️ Stack Tecnológica

O projeto foi construído inteiramente em **Python**, utilizando o poder do **Streamlit** para renderização de interface e gestão de estado (*Session State*).

| Componente | Tecnologia | Descrição |
| :--- | :--- | :--- |
| **Core & UI** | **Streamlit** | Framework fullstack para interfaces de dados interativas. |
| **Banco de Dados** | **Supabase (PostgreSQL)** | Persistência de dados, utilizando a biblioteca `supabase-py`. |
| **Manipulação de Dados** | **Pandas** | Tratamento de DataFrames para relatórios e dashboards. |
| **Inteligência Artificial** | **Google Gemini API** | Extração de dados não estruturados (OCR) de faturas em PDF. |
| **Visualização** | **Plotly** | Gráficos interativos para análise de despesas e faturamento. |
| **Exportação** | **OpenPyXL** | Geração de relatórios anuais em formato Excel (.xlsx). |

# ✨ Funcionalidades

## 1. Gestão Completa de Contratos

* Cadastro de novos contratos com geração automática de parcelas
* Edição de informações contratuais
* Ativação/desativação de contratos
* Sistema de renovação inteligente para contratos vencidos
* Controle de vigência e alertas de término

## 2. Lançamento Inteligente de Parcelas

**Diferencial competitivo:** Integração com IA

Fluxo automatizado de lançamento:
1. O Usuário seleciona o Contrato a ser lançado (manualmente para validação)
2. Usuário faz upload da nota fiscal (PDF)
3. O Sistema envia o documento para Google Gemini API
4. A IA extrai automaticamente:
   - Valor da nota
   - Número do documento
5. Campos do formulário são preenchidos automaticamente
6. Usuário apenas confirma o lançamento

Isso reduziu o tempo médio de lançamento de ~3 minutos para ~15 segundos por parcela.

## 📂 Estrutura do Projeto

```text
src/
├── core/                              # Configurações e conexões
│   ├── database_connections.py          # Client Supabase com cache
│   └── app.py                           # Entry point principal
├── _pages/                            # Camada de apresentação
│   ├── parcelas.py                      # Interface de lançamentos
│   ├── contratos.py                     # CRUD de contratos
│   └── dashboard.py                     # Analytics e relatórios
├── services/                          # Lógica de negócio
│   ├── parcelas_service.py              # Operações de lançamento
│   ├── contratos_service.py             # Gestão de contratos
│   └── dashboard_service.py             # Processamento de métricas
└── utils/                             # Ferramentas auxiliares
    ├── gemini_extractor.py              # IA para OCR de faturas
    ├── formatters.py                    # Formatação de dados
    └── plots.py                         # Visualizações Plotly
```

#  Aprendizados Técnicos
Este projeto me permitiu desenvolver competências em:

* **Arquitetura de aplicações:** Estruturação modular, separação de camadas.
* **Integração com APIs externas:** Supabase REST API, Google Gemini.
* **Processamento de dados:** Transformações complexas com Pandas.
* **UX para usuários não-técnicos:** Interface intuitiva com feedback visual.
* **Deploy e manutenção:** Gestão de ambientes, versionamento de schema.

##  Tecnologias Documentadas
- [Streamlit Documentation](https://docs.streamlit.io)
- [Supabase Python Client](https://supabase.com/docs/reference/python)
- [Google Gemini API](https://ai.google.dev/docs)
- [Pandas User Guide](https://pandas.pydata.org/docs/user_guide/)
- [Plotly Python](https://plotly.com/python/)

## Nota
*  Imagens do projeto estão contidas no diretório "screenshots"!
