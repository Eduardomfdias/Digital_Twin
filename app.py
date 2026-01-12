"""
Digital Twin - Guarda-Redes ABC Braga
Página Principal e Navegação
"""

import streamlit as st
from data_access import HandballDataAccess
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Digital Twin - ABC Braga",
    page_icon="🤾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado melhorado
st.markdown("""
<style>
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .hero-subtitle {
        font-size: 1.3rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    /* Dashboard Cards */
    .dashboard-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-left: 5px solid;
        height: 100%;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .card-timeout { border-left-color: #f76707; }
    .card-prejogo { border-left-color: #0ca678; }
    .card-treino { border-left-color: #1971c2; }
    
    .card-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #2c3e50;
    }
    .card-description {
        color: #6c757d;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    
    /* Métricas */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        color: white;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Tabela customizada */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Sidebar */
    .sidebar-gr {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #667eea;
    }
    
    /* Footer */
    .footer-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin-top: 3rem;
    }
    .footer-title {
        color: #667eea;
        font-weight: 700;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar DB
@st.cache_resource
def get_db():
    return HandballDataAccess()

db = get_db()

# HERO SECTION
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🤾 Digital Twin - ABC Braga</div>
    <div class="hero-subtitle">Sistema Inteligente de Apoio à Decisão para Guarda-Redes</div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown("### 🎯 ABC BRAGA")
    st.markdown("**Digital Twin System**")
    st.divider()
    
    st.markdown("### 🥅 Guarda-Redes")
    grs_df = db.get_all_goalkeepers()
    for _, gr in grs_df.iterrows():
        emoji = "⭐" if gr['posicao_principal'] == "Titular" else "🔶"
        st.markdown(f"""
        <div class="sidebar-gr">
            {emoji} <b>{gr['nome']}</b><br>
            <small>{gr['altura_cm']}cm | {gr['posicao_principal']}</small>
        </div>
        """, unsafe_allow_html=True)
    
    

# DASHBOARD CARDS
st.markdown("## 🎯 Dashboards Disponíveis")
st.markdown("")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/Timeout.py", label="⏱️ Abrir Dashboard", use_container_width=True)
    st.markdown("""
    <div class="dashboard-card card-timeout">
        <div class="card-icon">⏱️</div>
        <div class="card-title">Timeout em Jogo</div>
        <div class="card-description">
            Decisões táticas instantâneas durante o jogo. Análise de compatibilidade GR-Adversário em tempo real com recomendações imediatas (90 segundos).
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.page_link("pages/Pre_Jogo.py", label="📊 Abrir Dashboard", use_container_width=True)
    st.markdown("""
    <div class="dashboard-card card-prejogo">
        <div class="card-icon">📊</div>
        <div class="card-title">Análise Pré-Jogo</div>
        <div class="card-description">
            Preparação estratégica completa. Estudo de padrões ofensivos adversários, matriz de compatibilidade e plano tático detalhado.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.page_link("pages/Treino.py", label="📚 Abrir Dashboard", use_container_width=True)
    st.markdown("""
    <div class="dashboard-card card-treino">
        <div class="card-icon">📚</div>
        <div class="card-title">Planeamento de Treino</div>
        <div class="card-description">
            Desenvolvimento individual a longo prazo. Análise de gaps por zona, simulações de cenários e ROI de treino personalizado.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# MÉTRICAS PRINCIPAIS
st.markdown("## 📊 Estatísticas do Sistema")
st.markdown("")

col1, col2, col3, col4 = st.columns(4)

grs_df = db.get_all_goalkeepers()

with col1:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{len(grs_df)}</div>
        <div class="metric-label">Guarda-Redes</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    altura_media = grs_df['altura_cm'].mean()
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{altura_media:.0f}</div>
        <div class="metric-label">Altura Média (cm)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    query = "SELECT AVG(taxa_defesa_global) as media FROM epocas WHERE epoca = 2025"
    with db.get_connection() as conn:
        taxa_media = pd.read_sql_query(query, conn)['media'].values[0]
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{taxa_media:.1f}%</div>
        <div class="metric-label">Taxa Defesa Média</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    query = "SELECT COUNT(DISTINCT id) as total FROM jogos"
    with db.get_connection() as conn:
        total_jogos = pd.read_sql_query(query, conn)['total'].values[0]
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-value">{total_jogos}</div>
        <div class="metric-label">Jogos Analisados</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# PLANTEL CARDS
st.markdown("## 👥 Plantel de Guarda-Redes")
st.markdown("")

query = """
SELECT 
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

cols = st.columns(len(plantel_df))

for idx, (col, (_, gr)) in enumerate(zip(cols, plantel_df.iterrows())):
    with col:
        emoji = "⭐" if gr['posicao_principal'] == "Titular" else "🔶"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; text-align: center; color: white;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{emoji}</div>
            <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem;">{gr['nome']}</div>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;">
                <div style="font-size: 2rem; font-weight: 800;">{gr['altura_cm']} cm</div>
                <div style="font-size: 0.85rem; opacity: 0.9;">Altura</div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;">
                <div style="font-size: 2rem; font-weight: 800;">{gr['envergadura_cm']} cm</div>
                <div style="font-size: 0.85rem; opacity: 0.9;">Envergadura</div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;">
                <div style="font-size: 2rem; font-weight: 800;">{gr['taxa_defesa_global']:.1f}%</div>
                <div style="font-size: 0.85rem; opacity: 0.9;">Taxa Defesa</div>
            </div>
            <div style="font-size: 0.9rem; opacity: 0.85; margin-top: 1rem;">
                {gr['jogos_disputados']} jogos | {gr['posicao_principal']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div class="footer-section">
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 2rem;">
        <div>
            <div class="footer-title">🔧 Stack Tecnológico</div>
            <ul style="list-style: none; padding: 0;">
                <li>✓ Streamlit & Plotly</li>
                <li>✓ SQLite & Pandas</li>
                <li>✓ H2O.ai AutoML</li>
                <li>✓ Python 3.12</li>
            </ul>
        </div>
        <div>
            <div class="footer-title">📊 Base de Dados</div>
            <ul style="list-style: none; padding: 0;">
                <li>• 3 Guarda-Redes</li>
                <li>• 30 Jogos</li>
                <li>• 1.622 Lances</li>
                <li>• 360 Treinos</li>
            </ul>
        </div>
        <div>
            <div class="footer-title">👥 Equipa MEGSI</div>
            <ul style="list-style: none; padding: 0;">
                <li>Eduardo Dias</li>
                <li>Nuno Martinho</li>
                <li>Lucas Serralha</li>
                <li><b>UMinho 2025/26</b></li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("© 2025 ABC Braga Digital Twin System | Universidade do Minho")