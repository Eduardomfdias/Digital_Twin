"""
Dashboard de Planeamento de Treino
Análise de gap e otimização de treino personalizado
"""

import streamlit as st
import pandas as pd
import numpy as np
from data_access import HandballDataAccess
import sys
sys.path.append('..')
from utils.visualizations import (
    criar_grafico_gap,
    criar_grafico_evolucao,
    criar_tabela_cenarios_roi
)

# Configuração
st.set_page_config(
    page_title="Planeamento de Treino - ABC Braga",
    page_icon="📚",
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
st.markdown('<div class="main-header">📚 Planeamento de Treino Personalizado</div>', unsafe_allow_html=True)
st.markdown("**Análise de gap e otimização de desenvolvimento**")
st.divider()

# Sidebar - Seleção do GR
with st.sidebar:
    st.markdown("## 🥅 Guarda-Redes")
    
    grs_df = db.get_all_goalkeepers()
    
    goalkeeper_nome = st.selectbox(
        "Atleta",
        grs_df['nome'].tolist(),
        index=0
    )
    gr_id = grs_df[grs_df['nome'] == goalkeeper_nome]['id'].values[0]
    
    # Info do GR
    gr_info = grs_df[grs_df['id'] == gr_id].iloc[0]
    
    st.divider()
    
    st.markdown("### 📊 Perfil")
    st.metric("Altura", f"{gr_info['altura_cm']} cm")
    st.metric("Posição", gr_info['posicao_principal'])
    
    # Taxa defesa atual
    query = "SELECT taxa_defesa_global FROM epocas WHERE guarda_redes_id = ? AND epoca = 2025"
    with db.get_connection() as conn:
        taxa_atual = pd.read_sql_query(query, conn, params=(gr_id,))['taxa_defesa_global'].values[0]
    
    st.metric("Taxa Defesa (2025)", f"{taxa_atual:.1f}%")

# Layout principal
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## 📊 Análise de Gap por Zona")
    
    # Carregar dados de época para ter taxas por zona
    query = """
    SELECT 
        taxa_defesa_zona1, taxa_defesa_zona2, taxa_defesa_zona3,
        taxa_defesa_zona4, taxa_defesa_zona5, taxa_defesa_zona6,
        taxa_defesa_zona7, taxa_defesa_zona8, taxa_defesa_zona9
    FROM epocas
    WHERE guarda_redes_id = ? AND epoca = 2025
    """
    with db.get_connection() as conn:
        zonas_data = pd.read_sql_query(query, conn, params=(gr_id,))
    
    if len(zonas_data) > 0:
        # Preparar dados
        zonas_nomes = [
            'Superior Esquerda', 'Superior Centro', 'Superior Direita',
            'Média Esquerda', 'Média Centro', 'Média Direita',
            'Inferior Esquerda', 'Inferior Centro', 'Inferior Direita'
        ]
        
        atual = zonas_data.iloc[0].values.tolist()
        objetivo = [65, 70, 65, 75, 80, 75, 80, 85, 80]  # Valores alvo
        
        gap_df = pd.DataFrame({
            'zona': zonas_nomes,
            'atual': atual,
            'objetivo': objetivo,
            'gap': [obj - at for obj, at in zip(objetivo, atual)]
        })
        
        # Criar gráfico de gap
        fig_gap = criar_grafico_gap(gap_df, goalkeeper_nome)
        st.plotly_chart(fig_gap, use_container_width=True)
        
        st.divider()
        
        # Tabela de priorização
        st.markdown("### 🎯 Priorização de Áreas de Treino")
        
        gap_analysis = gap_df.copy()
        gap_analysis['Prioridade'] = gap_analysis['gap'].apply(
            lambda x: '🔴 Alta' if x > 15 else ('🟡 Média' if x > 8 else '🟢 Baixa')
        )
        gap_analysis['Tempo Treino (%)'] = gap_analysis['gap'].apply(
            lambda x: max(5, min(25, x * 1.2))
        ).round(0).astype(int)
        
        gap_analysis = gap_analysis.sort_values('gap', ascending=False)
        
        tabela_gap = gap_analysis[['zona', 'gap', 'Prioridade', 'Tempo Treino (%)']].rename(columns={
            'zona': 'Zona',
            'gap': 'Gap (%)'
        })
        
        st.dataframe(
            tabela_gap.style.background_gradient(subset=['Gap (%)'], cmap='RdYlGn_r'),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("Sem dados de época para este GR")

with col2:
    st.markdown("## 📅 Plano de Treino")
    
    st.metric("Horas Totais/Semana", "20h")
    st.metric("Sessões/Semana", "8")
    
    st.divider()
    
    st.markdown("### 🗓️ Distribuição")
    
    import plotly.express as px
    
    treino_dist = pd.DataFrame({
        'Componente': ['Técnico-Tático', 'Físico', 'Psicológico', 'Recuperação'],
        'Horas': [10, 6, 2, 2]
    })
    
    fig_pie = px.pie(
        treino_dist, 
        values='Horas', 
        names='Componente',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=250, showlegend=False)
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    st.markdown("### 🎯 Focos Prioritários")
    
    if len(zonas_data) > 0:
        top_3_gaps = gap_analysis.head(3)
        for i, (_, row) in enumerate(top_3_gaps.iterrows(), 1):
            st.warning(f"{i}. {row['zona']} ({row['gap']:.1f}% gap)")
    
    st.divider()
    
    st.markdown("### 📈 Evolução Esperada")
    st.info("**4 semanas**: +5-8% zonas prioritárias")
    st.info("**12 semanas**: +12-15% eficácia global")

# Evolução temporal
st.divider()
st.markdown("## 📈 Evolução Temporal")

evolucao_df = db.get_evolution(gr_id=gr_id, last_n_months=6)

if len(evolucao_df) > 0:
    fig_evolucao = criar_grafico_evolucao(evolucao_df)
    st.plotly_chart(fig_evolucao, use_container_width=True)
    
    # Análise de tendência
    tendencia_recente = evolucao_df.iloc[0]['tendencia']
    
    if tendencia_recente == 'Crescente':
        st.success(f"✅ **Tendência positiva**: {goalkeeper_nome} está em evolução!")
    elif tendencia_recente == 'Decrescente':
        st.error(f"⚠️ **Atenção**: Possível estagnação ou fadiga detectada")
    else:
        st.info(f"➡️ **Performance estável** nos últimos meses")
else:
    st.info("Sem dados de evolução temporal")

# Simulações de cenários (ROI)
st.divider()
st.markdown("## 💡 Cenários de Melhoria (ROI)")

cenarios_df = db.get_training_scenarios(gr_id=gr_id, top_n=5)

if len(cenarios_df) > 0:
    st.markdown("**Top 5 cenários por Retorno de Investimento:**")
    
    # Tabela interativa
    tabela_cenarios = cenarios_df.copy()
    tabela_cenarios['ROI'] = tabela_cenarios['roi_estimado'].round(1)
    tabela_cenarios['Ganho (%)'] = tabela_cenarios['ganho_esperado'].round(1)
    tabela_cenarios['Tempo (sem)'] = tabela_cenarios['tempo_resultados_semanas']
    
    display_cenarios = tabela_cenarios[[
        'cenario', 
        'Ganho (%)', 
        'ROI', 
        'Tempo (sem)',
        'prioridade'
    ]].rename(columns={
        'cenario': 'Cenário',
        'prioridade': 'Prioridade'
    })
    
    st.dataframe(
        display_cenarios.style.background_gradient(subset=['ROI'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True
    )
    
    # Destacar melhor cenário
    melhor = cenarios_df.iloc[0]
    
    st.success(f"""
    **💎 Cenário Recomendado**: {melhor['cenario']}
    - Ganho esperado: +{melhor['ganho_esperado']:.1f}%
    - ROI: {melhor['roi_estimado']:.1f}
    - Tempo até resultados: {melhor['tempo_resultados_semanas']:.0f} semanas
    """)
else:
    st.info("Sem simulações de cenários disponíveis")

# Histórico de treinos
st.divider()
st.markdown("## 📋 Histórico de Treinos Recente")

query = """
SELECT 
    data,
    tipo_treino,
    foco_principal,
    duracao_minutos,
    taxa_sucesso_perc,
    sensacao_fisica,
    confianca
FROM treinos
WHERE guarda_redes_id = ?
ORDER BY data DESC
LIMIT 10
"""

with db.get_connection() as conn:
    treinos_recentes = pd.read_sql_query(query, conn, params=(gr_id,))

if len(treinos_recentes) > 0:
    treinos_display = treinos_recentes.rename(columns={
        'data': 'Data',
        'tipo_treino': 'Tipo',
        'foco_principal': 'Foco',
        'duracao_minutos': 'Duração (min)',
        'taxa_sucesso_perc': 'Sucesso (%)',
        'sensacao_fisica': 'Física (1-10)',
        'confianca': 'Confiança (1-10)'
    })
    
    st.dataframe(
        treinos_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Métricas agregadas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        media_sucesso = treinos_recentes['taxa_sucesso_perc'].mean()
        st.metric("Taxa Sucesso Média", f"{media_sucesso:.1f}%")
    
    with col2:
        media_fisica = treinos_recentes['sensacao_fisica'].mean()
        st.metric("Sensação Física Média", f"{media_fisica:.1f}/10")
    
    with col3:
        media_conf = treinos_recentes['confianca'].mean()
        st.metric("Confiança Média", f"{media_conf:.1f}/10")
else:
    st.info("Sem histórico de treinos")

st.caption("📚 Planeamento baseado em dados e simulações preditivas")
