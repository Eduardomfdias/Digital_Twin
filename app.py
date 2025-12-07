"""
Digital Twin - Guarda-Redes ABC Braga
Página Principal e Navegação
"""

import streamlit as st
from data_access import HandballDataAccess

# Configuração da página
st.set_page_config(
    page_title="Digital Twin - ABC Braga",
    page_icon="🤾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar CSS customizado
with open('styles/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Inicializar acesso a dados
@st.cache_resource
def get_db():
    return HandballDataAccess()

db = get_db()

# Header principal
st.markdown('<div class="main-header">🤾 Digital Twin - Guarda-Redes de Andebol</div>', unsafe_allow_html=True)
st.markdown("**ABC Braga | Sistema de Apoio à Decisão Tática**")
st.divider()

# Sidebar - Info do projeto
with st.sidebar:
    st.markdown("## 🎯 ABC BRAGA")
    st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    st.markdown("### 📍 Navegação")
    st.markdown("""
    Use o menu acima para aceder aos dashboards:
    - ⏱️ **Timeout em Jogo**
    - 📊 **Análise Pré-Jogo**
    - 📚 **Planeamento de Treino**
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Info dos GRs disponíveis
    st.markdown("### 🥅 Guarda-Redes")
    grs_df = db.get_all_goalkeepers()
    for _, gr in grs_df.iterrows():
        emoji = "⭐" if gr['posicao_principal'] == "Titular" else "🔹"
        st.markdown(f"{emoji} **{gr['nome']}** ({gr['altura_cm']}cm)")

# Conteúdo principal - Dashboard de Boas-Vindas
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### ⏱️ Timeout em Jogo")
    st.info("""
    **Decisões rápidas durante o jogo**
    - Compatibilidade GR vs Adversário
    - Heatmap de vulnerabilidades
    - Recomendações imediatas (90s)
    """)
    st.page_link("pages/Timeout.py", label="Abrir Dashboard", icon="⏱️")

with col2:
    st.markdown("### 📊 Análise Pré-Jogo")
    st.info("""
    **Preparação antes do confronto**
    - Padrões ofensivos do adversário
    - Matriz de compatibilidade
    - Plano tático detalhado
    """)
    st.page_link("pages/Pre_Jogo.py", label="Abrir Dashboard", icon="📊")

with col3:
    st.markdown("### 📚 Planeamento de Treino")
    st.info("""
    **Desenvolvimento a longo prazo**
    - Análise de gap por zona
    - Simulações de cenários
    - ROI de treino personalizado
    """)
    st.page_link("pages/Treino.py", label="Abrir Dashboard", icon="📚")

st.divider()

# Estatísticas gerais
st.markdown("## 📊 Visão Geral do Plantel")

col1, col2, col3, col4 = st.columns(4)

# Carregar estatísticas
grs_df = db.get_all_goalkeepers()

with col1:
    st.metric("Guarda-Redes", len(grs_df))

with col2:
    altura_media = grs_df['altura_cm'].mean()
    st.metric("Altura Média", f"{altura_media:.0f} cm")

with col3:
    # Query épocas para taxa média
    import pandas as pd
    query = "SELECT AVG(taxa_defesa_global) as media FROM epocas WHERE epoca = 2025"
    with db.get_connection() as conn:
        taxa_media = pd.read_sql_query(query, conn)['media'].values[0]
    st.metric("Taxa Defesa Média", f"{taxa_media:.1f}%")

with col4:
    # Total de jogos
    query = "SELECT COUNT(DISTINCT id) as total FROM jogos"
    with db.get_connection() as conn:
        total_jogos = pd.read_sql_query(query, conn)['total'].values[0]
    st.metric("Jogos Analisados", total_jogos)

# Tabela dos GRs
st.markdown("### 👥 Plantel Detalhado")

# Adicionar dados de época 2025
query = """
SELECT 
    gr.id,
    gr.nome,
    gr.altura_cm,
    gr.envergadura_cm,
    gr.posicao_principal,
    e.taxa_defesa_global,
    e.jogos_disputados
FROM guarda_redes gr
LEFT JOIN epocas e ON gr.id = e.guarda_redes_id AND e.epoca = 2025
"""

with db.get_connection() as conn:
    plantel_df = pd.read_sql_query(query, conn)

plantel_df = plantel_df.rename(columns={
    'nome': 'Nome',
    'altura_cm': 'Altura (cm)',
    'envergadura_cm': 'Envergadura (cm)',
    'posicao_principal': 'Posição',
    'taxa_defesa_global': 'Taxa Defesa (%)',
    'jogos_disputados': 'Jogos'
})

st.dataframe(
    plantel_df[['Nome', 'Altura (cm)', 'Envergadura (cm)', 'Posição', 'Taxa Defesa (%)', 'Jogos']],
    use_container_width=True,
    hide_index=True
)

# Footer
st.divider()

col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.markdown("#### 🔧 Tecnologias")
    st.markdown("""
    - **Streamlit**: Interface
    - **SQLite**: Base de dados
    - **Plotly**: Visualizações
    - **Pandas**: Análise de dados
    """)

with col_footer2:
    st.markdown("#### 📊 Base de Dados")
    st.markdown("""
    - 3 Guarda-Redes
    - 30 Jogos
    - 1.622 Lances
    - 360 Treinos
    """)

with col_footer3:
    st.markdown("#### 👥 Equipa MEGSI")
    st.markdown("""
    - Eduardo Dias
    - Nuno Martinho
    - Lucas Serralha
    
    **2025/26**
    """)

st.caption("© 2025 ABC Braga Digital Twin System | Universidade do Minho")