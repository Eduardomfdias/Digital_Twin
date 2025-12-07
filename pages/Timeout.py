"""
Dashboard de Timeout em Jogo
Decisões rápidas durante os 60-90 segundos de timeout
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from data_access import HandballDataAccess
import sys
sys.path.append('..')
from utils.visualizations import (
    criar_heatmap_baliza,
    criar_grafico_compatibilidade_barras,
    criar_grafico_vulnerabilidades
)

# Configuração da página
st.set_page_config(
    page_title="Timeout em Jogo - ABC Braga",
    page_icon="⏱️",
    layout="wide"
)

# Carregar CSS
with open('../styles/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Inicializar BD
@st.cache_resource
def get_db():
    return HandballDataAccess()

db = get_db()

# Header
st.markdown('<div class="main-header">⏱️ Interface de Timeout (90 segundos)</div>', unsafe_allow_html=True)
st.markdown("**Decisão tática imediata durante o jogo**")
st.divider()

# Sidebar - Contexto do jogo
with st.sidebar:
    st.markdown("## ⚡ Contexto do Jogo")
    
    # Seleção de adversário
    query = "SELECT id, nome FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        adversarios_df = pd.read_sql_query(query, conn)
    
    adversario_nome = st.selectbox(
        "Adversário",
        adversarios_df['nome'].tolist(),
        index=0  # FC Porto por defeito
    )
    adversario_id = adversarios_df[adversarios_df['nome'] == adversario_nome]['id'].values[0]
    
    st.divider()
    
    st.markdown("### 📊 Situação de Jogo")
    game_time = st.slider("Minuto do Jogo", 0, 60, 42)
    
    col1, col2 = st.columns(2)
    with col1:
        score_home = st.number_input("ABC Braga", 0, 50, 24)
    with col2:
        score_away = st.number_input(adversario_nome, 0, 50, 24)
    
    st.divider()
    
    # GR atualmente em campo
    st.markdown("### 🥅 GR em Campo")
    grs_df = db.get_all_goalkeepers()
    goalkeeper_nome = st.selectbox(
        "Atleta",
        grs_df['nome'].tolist(),
        index=0  # Humberto por defeito
    )
    gr_id = grs_df[grs_df['nome'] == goalkeeper_nome]['id'].values[0]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("⏰ Tempo Restante", f"{game_time} min", f"{60-game_time} min")

with col2:
    diferenca = score_home - score_away
    st.metric("🎯 Resultado", f"{score_home} - {score_away}", f"{diferenca:+d}")

with col3:
    # Taxa defesa do GR (época atual)
    query = """
    SELECT taxa_defesa_global 
    FROM epocas 
    WHERE guarda_redes_id = ? AND epoca = 2025
    """
    with db.get_connection() as conn:
        taxa = pd.read_sql_query(query, conn, params=(gr_id,))['taxa_defesa_global'].values[0]
    st.metric("🥅 Eficácia GR", f"{taxa:.1f}%", "+2%")

with col4:
    # Simulação de countdown
    remaining = max(0, 90 - (datetime.now().second % 90))
    st.metric("⏳ Timeout", f"{remaining}s", "Restantes")

st.divider()

# Conteúdo principal
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### 🎯 Análise de Compatibilidade")
    
    # Carregar compatibilidade de TODOS os GRs vs este adversário
    compat_df = db.get_compatibility_matrix(adversario_id)
    
    # Criar gráfico de compatibilidade
    fig_compat = criar_grafico_compatibilidade_barras(compat_df)
    st.plotly_chart(fig_compat, use_container_width=True)
    
    # Recomendação baseada em dados reais
    melhor_gr = compat_df.iloc[0]
    
    if melhor_gr['nome'] == goalkeeper_nome:
        st.success(f"✅ **{goalkeeper_nome}** é a melhor opção vs {adversario_nome} ({melhor_gr['taxa_defesa_perc']:.1f}% eficácia)")
    else:
        st.warning(f"⚠️ **SUGESTÃO DE SUBSTITUIÇÃO**: {melhor_gr['nome']} tem melhor compatibilidade ({melhor_gr['taxa_defesa_perc']:.1f}% vs {compat_df[compat_df['nome']==goalkeeper_nome]['taxa_defesa_perc'].values[0]:.1f}%)")
    
    st.divider()
    
    # Heatmap de performance por zona do GR atual
    st.markdown(f"### 🗺️ Performance por Zona - {goalkeeper_nome}")
    
    zones_df = db.get_zone_performance(gr_id=gr_id, adversario_id=adversario_id)
    
    if len(zones_df) > 0:
        fig_heatmap = criar_heatmap_baliza(zones_df)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Identificar zona mais fraca
        zona_mais_fraca = zones_df.loc[zones_df['taxa_defesa'].idxmin()]
        st.error(f"⚠️ **ZONA VULNERÁVEL**: {zona_mais_fraca['zona_baliza_nome']} ({zona_mais_fraca['taxa_defesa']:.0f}% defesa)")
    else:
        st.info(f"Sem dados históricos de {goalkeeper_nome} vs {adversario_nome}")

with col_right:
    st.markdown("### 📊 Estatísticas do Jogo")
    
    # Estatísticas simuladas do jogo atual
    # (Numa implementação real, viriam de tracking em tempo real)
    st.metric("Defesas / Remates", "6/10", "+1")
    st.metric("Taxa Defesa (Jogo)", "60%", "+5%")
    st.metric("Zonas Comprometidas", "2", "Sup. Dir, Méd. Esq")
    
    st.divider()
    
    st.markdown("### 💪 Estado Físico")
    fatigue = min(100, game_time * 1.5)
    st.progress(fatigue/100)
    st.caption(f"Fadiga estimada: {fatigue:.0f}%")
    
    st.divider()
    
    st.markdown("### 🎯 Decisão")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("✅ Manter", use_container_width=True, type="primary"):
            st.success("Decisão registada!")
    
    with col_btn2:
        if st.button("🔄 Substituir", use_container_width=True):
            st.info("Ver alternativas abaixo ⬇️")
    
    st.divider()
    
    # Tabela de alternativas
    st.markdown("### 🔄 Alternativas")
    
    # Mostrar outros GRs com compatibilidade
    alternativas = compat_df[compat_df['nome'] != goalkeeper_nome].copy()
    alternativas = alternativas[['nome', 'taxa_defesa_perc']].rename(columns={
        'nome': 'GR',
        'taxa_defesa_perc': 'Taxa (%)'
    })
    
    st.dataframe(
        alternativas,
        use_container_width=True,
        hide_index=True
    )

# Rodapé com recomendações táticas
st.divider()
st.markdown("### 💡 Recomendações Táticas")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **Posicionamento**
    - Descair 30cm à direita
    - Distância: 1.2m da linha
    """)

with col2:
    st.warning("""
    **Atenção**
    - Lateral esquerdo adversário
    - Remates zona superior
    """)

with col3:
    st.success("""
    **Pontos Fortes**
    - Zonas inferiores
    - Tempo de reação
    """)

st.caption("⏱️ Interface otimizada para decisões em 60-90 segundos")
