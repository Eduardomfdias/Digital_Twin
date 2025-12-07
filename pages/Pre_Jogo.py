"""
Dashboard de Análise Pré-Jogo
Preparação detalhada 24-48h antes do confronto
"""

import streamlit as st
import pandas as pd
import numpy as np
from data_access import HandballDataAccess
import sys
sys.path.append('..')
from utils.visualizations import (
    criar_heatmap_baliza,
    criar_grafico_compatibilidade_barras,
    criar_radar_adversario
)

# Configuração
st.set_page_config(
    page_title="Análise Pré-Jogo - ABC Braga",
    page_icon="📊",
    layout="wide"
)

# CSS
with open('../styles/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# BD
@st.cache_resource
def get_db():
    return HandballDataAccess()

db = get_db()

# Header
st.markdown('<div class="main-header">📊 Análise Pré-Jogo e Briefing Tático</div>', unsafe_allow_html=True)
st.markdown("**Preparação detalhada do confronto (24-48h antes)**")
st.divider()

# Sidebar - Seleção
with st.sidebar:
    st.markdown("## ⚔️ Próximo Confronto")
    
    # Adversário
    query = "SELECT id, nome, ranking_liga FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        adversarios_df = pd.read_sql_query(query, conn)
    
    adversario_nome = st.selectbox(
        "Adversário",
        adversarios_df['nome'].tolist(),
        index=0
    )
    adversario_id = adversarios_df[adversarios_df['nome'] == adversario_nome]['id'].values[0]
    
    # Info do adversário
    query = "SELECT * FROM adversarios WHERE id = ?"
    with db.get_connection() as conn:
        adv_info = pd.read_sql_query(query, conn, params=(adversario_id,)).iloc[0]
    
    st.divider()
    
    st.markdown("### 📌 Informações")
    st.metric("Ranking Liga", f"{adv_info['ranking_liga']}º")
    st.metric("Média Golos/Jogo", f"{adv_info['media_golos_jogo']:.1f}")
    st.metric("Estilo Ofensivo", adv_info['estilo_ofensivo'])

# Tabs principais
tab1, tab2, tab3 = st.tabs(["🎯 Padrões Adversário", "🥅 Compatibilidade GR", "📋 Plano Tático"])

# TAB 1: Padrões do Adversário
with tab1:
    st.markdown("## 🎯 Análise do Adversário")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Distribuição de Remates")
        
        # Criar heatmap com padrões do adversário
        zones_dist = np.array([
            [adv_info['remates_zona_alta_perc'] * 0.3, 
             adv_info['remates_zona_alta_perc'] * 0.4, 
             adv_info['remates_zona_alta_perc'] * 0.3],
            [adv_info['remates_zona_media_perc'] * 0.35, 
             adv_info['remates_zona_media_perc'] * 0.3, 
             adv_info['remates_zona_media_perc'] * 0.35],
            [adv_info['remates_zona_baixa_perc'] * 0.3, 
             adv_info['remates_zona_baixa_perc'] * 0.4, 
             adv_info['remates_zona_baixa_perc'] * 0.3]
        ])
        
        import plotly.graph_objects as go
        
        fig_adv = go.Figure(data=go.Heatmap(
            z=zones_dist,
            x=['Esquerda', 'Centro', 'Direita'],
            y=['Superior', 'Meio', 'Inferior'],
            colorscale='Reds',
            text=np.round(zones_dist, 1),
            texttemplate='%{text}%',
            textfont={"size": 16},
            colorbar=dict(title="Prob. (%)"),
        ))
        
        fig_adv.update_layout(
            title=f"Distribuição de Remates - {adversario_nome}",
            height=400,
            yaxis=dict(autorange='reversed')
        )
        
        st.plotly_chart(fig_adv, use_container_width=True)
        
        # Padrões identificados
        st.markdown("#### 📌 Padrões Identificados")
        
        zona_preferida = "Alta" if adv_info['remates_zona_alta_perc'] > adv_info['remates_zona_media_perc'] else "Média"
        st.info(f"🔸 **Preferência**: Zona {zona_preferida} ({max(adv_info['remates_zona_alta_perc'], adv_info['remates_zona_media_perc'])}%)")
        st.info(f"🔸 **Velocidade Média**: {adv_info['velocidade_media_remate_kmh']} km/h")
        st.info(f"🔸 **Tipo Ataque**: {adv_info['tipo_ataque_predominante']}")
    
    with col2:
        st.markdown("### ⚡ Características Ofensivas")
        
        # Métricas chave
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.metric("Transições/Jogo", adv_info['transicoes_rapidas_jogo'])
            st.metric("Eficácia 1ª Linha", f"{adv_info['eficacia_primeira_linha_perc']}%")
        
        with col_m2:
            st.metric("Golos/Jogo", f"{adv_info['media_golos_jogo']:.1f}")
            st.metric("Eficácia 2ª Linha", f"{adv_info['eficacia_segunda_linha_perc']}%")
        
        st.divider()
        
        st.markdown("### 🎯 Ameaças Principais")
        
        # Identificar ameaças baseadas nos dados
        ameacas = []
        
        if adv_info['velocidade_media_remate_kmh'] > 100:
            ameacas.append(("🔴 ALTA", "Remates de alta velocidade", f"{adv_info['velocidade_media_remate_kmh']} km/h"))
        
        if adv_info['transicoes_rapidas_jogo'] > 20:
            ameacas.append(("🟠 MÉDIA", "Transições rápidas frequentes", f"{adv_info['transicoes_rapidas_jogo']}/jogo"))
        
        if adv_info['eficacia_primeira_linha_perc'] > 65:
            ameacas.append(("🟠 MÉDIA", "Eficácia elevada 1ª linha", f"{adv_info['eficacia_primeira_linha_perc']}%"))
        
        for nivel, desc, valor in ameacas:
            st.warning(f"{nivel} **{desc}**: {valor}")

# TAB 2: Compatibilidade GR
with tab2:
    st.markdown("## 🎯 Matriz de Compatibilidade GR vs Adversário")
    
    # Carregar compatibilidade
    compat_df = db.get_compatibility_matrix(adversario_id)
    
    # Gráfico de barras
    fig_compat = criar_grafico_compatibilidade_barras(compat_df)
    st.plotly_chart(fig_compat, use_container_width=True)
    
    st.divider()
    
    # Tabela detalhada
    st.markdown("### 📊 Análise Detalhada")
    
    # Preparar dados para exibição
    tabela_compat = compat_df.copy()
    tabela_compat['Prob. Titular'] = (tabela_compat['prob_ser_titular'] * 100).round(0).astype(int).astype(str) + '%'
    
    tabela_display = tabela_compat[[
        'nome', 
        'taxa_defesa_perc', 
        'Prob. Titular',
        'zona_fraca_1',
        'zona_fraca_2'
    ]].rename(columns={
        'nome': 'Guarda-Redes',
        'taxa_defesa_perc': 'Taxa Defesa (%)',
        'zona_fraca_1': 'Zona Fraca 1',
        'zona_fraca_2': 'Zona Fraca 2'
    })
    
    st.dataframe(
        tabela_display.style.background_gradient(subset=['Taxa Defesa (%)'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True
    )
    
    # Recomendação
    melhor = compat_df.iloc[0]
    st.success(f"✅ **RECOMENDAÇÃO**: {melhor['nome']} ({melhor['taxa_defesa_perc']:.1f}% eficácia vs {adversario_nome})")
    
    # Heatmaps lado a lado dos GRs
    st.divider()
    st.markdown("### 🗺️ Performance por Zona - Comparação")
    
    cols = st.columns(3)
    
    for idx, (_, gr) in enumerate(compat_df.iterrows()):
        with cols[idx]:
            st.markdown(f"**{gr['nome']}**")
            
            # Buscar performance por zona
            query = """
            SELECT zona_baliza_id, zona_baliza_nome, 
                   ROUND(AVG(CASE WHEN resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa_defesa
            FROM lances l
            JOIN jogos j ON l.jogo_id = j.id
            WHERE j.guarda_redes_id = ?
            GROUP BY zona_baliza_id, zona_baliza_nome
            ORDER BY zona_baliza_id
            """
            
            with db.get_connection() as conn:
                gr_id = db.get_all_goalkeepers()[db.get_all_goalkeepers()['nome'] == gr['nome']]['id'].values[0]
                zones_gr = pd.read_sql_query(query, conn, params=(gr_id,))
            
            if len(zones_gr) > 0:
                fig_mini = criar_heatmap_baliza(zones_gr, height=250)
                st.plotly_chart(fig_mini, use_container_width=True)
            else:
                st.info("Sem dados")

# TAB 3: Plano Tático
with tab3:
    st.markdown("## 📋 Plano Tático Detalhado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Estratégia de Posicionamento")
        
        with st.expander("🔸 Situações de 1ª Linha (6-9m)", expanded=True):
            st.markdown(f"""
            - **Posicionamento**: {'Direita' if adv_info['remates_zona_media_perc'] > 35 else 'Centro'}
            - **Distância**: 1.2m da linha de golo
            - **Foco**: Antecipar zona {'média-direita' if adv_info['tipo_ataque_predominante'] == 'Circulação' else 'central'}
            - **Ajuste**: Atenção a transições rápidas ({adv_info['transicoes_rapidas_jogo']}/jogo)
            """)
        
        with st.expander("🔸 Situações de 2ª Linha (9-12m)"):
            st.markdown(f"""
            - **Posicionamento**: Centralizado
            - **Distância**: 0.8m da linha de golo
            - **Foco**: Cobertura zonas superiores ({adv_info['remates_zona_alta_perc']}% remates)
            - **Ajuste**: Preparação para remates {adv_info['velocidade_media_remate_kmh']} km/h
            """)
        
        with st.expander("🔸 Situações de 7 Metros"):
            st.markdown("""
            - **Posicionamento**: Agressivo (+2m avanço)
            - **Foco**: Redução de ângulos
            - **Risco**: Remates colocados
            """)
    
    with col2:
        st.markdown("### ⚙️ Ajustes Dinâmicos")
        
        # Timeline de ajustes
        ajustes = pd.DataFrame({
            'Período': ['0-15 min', '15-30 min', '30-45 min', '45-60 min'],
            'Ajuste Recomendado': [
                'Posicionamento padrão, observar',
                'Ajustar baseado em padrões observados',
                'Manter vigilância transições',
                'Posicionamento agressivo (pressão final)'
            ],
            'Prioridade': ['Média', 'Alta', 'Alta', 'Crítica']
        })
        
        st.dataframe(ajustes, use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.markdown("### 🔄 Critérios de Substituição")
        st.error(f"""
        **Considerar substituição se**:
        - Taxa de defesa < 45% após 20 min
        - 3+ golos em zonas vulneráveis do GR
        - Sinais de fadiga técnica
        - Adversário explora zona fraca sistematicamente
        """)

st.caption("📊 Briefing para preparação 24-48h antes do jogo")
