"""
Dashboard de Timeout em Jogo
Decisões rápidas durante os 60-90 segundos de timeout
"""

import streamlit as st
import pandas as pd
import numpy as np
# Imports existentes...
from data_access import HandballDataAccess
import sys
sys.path.append('..')

# NOVO: Import do predictor H2O
try:
    from models.predictor_defesa import DefesaPredictor
    H2O_AVAILABLE = True
except ImportError:
    H2O_AVAILABLE = False
    print("⚠️ H2O.ai não disponível")
    
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
with open('styles/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Inicializar BD
@st.cache_resource
def get_db():
    return HandballDataAccess()

db = get_db()

# NOVO: Inicializar predictor H2O
@st.cache_resource
def get_predictor():
    """Carrega modelo H2O.ai (cached)"""
    if not H2O_AVAILABLE:
        return None
    try:
        predictor = DefesaPredictor(model_dir='models')
        return predictor
    except Exception as e:
        st.warning(f"⚠️ Modelo H2O não disponível: {e}")
        return None

predictor = get_predictor()

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
        taxa_df = pd.read_sql_query(query, conn, params=(gr_id,))

    # Verificar se há dados
    if len(taxa_df) == 0:
        taxa = 0.0  # Default se não houver dados
    else:
        taxa = taxa_df['taxa_defesa_global'].values[0]
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
    if len(compat_df) == 0:
        st.warning("⚠️ Sem dados de compatibilidade para este adversário.")
    else:
        melhor_gr = compat_df.iloc[0]
        
        if melhor_gr['nome'] == goalkeeper_nome:
            st.success(f"✅ **{goalkeeper_nome}** é a melhor opção vs {adversario_nome} ({melhor_gr['taxa_defesa_perc']:.1f}% eficácia)")
        else:
            atual_taxa = compat_df[compat_df['nome']==goalkeeper_nome]['taxa_defesa_perc'].values
            if len(atual_taxa) > 0:
                st.warning(f"⚠️ **SUGESTÃO DE SUBSTITUIÇÃO**: {melhor_gr['nome']} tem melhor compatibilidade ({melhor_gr['taxa_defesa_perc']:.1f}% vs {atual_taxa[0]:.1f}%)")
            else:
                st.warning(f"⚠️ **SUGESTÃO**: {melhor_gr['nome']} tem melhor compatibilidade ({melhor_gr['taxa_defesa_perc']:.1f}%)")
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

# =============================================================================
# NOVO: SIMULADOR DE LANCE COM H2O.AI
# =============================================================================

st.divider()
st.markdown("## 🤖 Simulador Preditivo (H2O.ai)")

if predictor:
    st.info("💡 **Modelo treinado com 1.622 lances históricos** - Usa Machine Learning para prever probabilidades em tempo real")
        
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    
    with col_sim1:
        st.markdown("**⚙️ Características do Lance**")
        sim_zona = st.selectbox(
            "Zona da Baliza",
            options=list(range(1, 10)),
            format_func=lambda x: {
                1: "1 - Superior Esquerda", 2: "2 - Superior Centro", 3: "3 - Superior Direita",
                4: "4 - Média Esquerda", 5: "5 - Média Centro", 6: "6 - Média Direita",
                7: "7 - Inferior Esquerda", 8: "8 - Inferior Centro", 9: "9 - Inferior Direita"
            }[x],
            index=4,
            key="sim_zona"
        )
        sim_dist = st.slider("Distância (m)", 6.0, 12.0, 9.0, 0.5, key="sim_dist")
    
    with col_sim2:
        st.markdown("**🎯 Contexto do Remate**")
        sim_vel = st.slider("Velocidade (km/h)", 70, 120, 95, 5, key="sim_vel")
        sim_min = st.slider("Minuto", 0, 60, game_time, key="sim_min")
    
    with col_sim3:
        st.markdown("**🥅 Guarda-Redes**")
        # Usar dados do GR já carregados no início
        gr_completo = grs_df[grs_df['nome'] == goalkeeper_nome]
        
        if len(gr_completo) == 0:
            st.error("❌ Erro ao carregar GR!")
            st.stop()
        
        # Buscar TODAS as colunas do GR
        query_gr = "SELECT * FROM guarda_redes WHERE nome = ?"
        with db.get_connection() as conn:
            gr_info_df = pd.read_sql_query(query_gr, conn, params=(goalkeeper_nome,))
            if len(gr_info_df) == 0:
                # Fallback: usar valores padrão
                st.warning("⚠️ Usando valores padrão do GR")
                gr_info = pd.Series({
                    'altura_cm': 185,
                    'envergadura_cm': 190,
                    'velocidade_lateral_ms': 4.2
                })
            else:
                gr_info = gr_info_df.iloc[0]
        
        st.metric("GR Selecionado", goalkeeper_nome)
        st.metric("Altura", f"{gr_info['altura_cm']} cm")
        st.metric("Diferença Golos", f"{score_home - score_away:+d}")
    
    # Botão de predição
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        if st.button("🔮 PREVER PROBABILIDADE DE DEFESA", type="primary", use_container_width=True):
            with st.spinner("🤖 Calculando com H2O.ai..."):
                try:
                    prob = predictor.predict(
                        zona=sim_zona,
                        distancia=sim_dist,
                        velocidade=sim_vel,
                        altura_gr=int(gr_info['altura_cm']),
                        envergadura_gr=int(gr_info['envergadura_cm']),
                        vel_lateral_gr=float(gr_info['velocidade_lateral_ms']),
                        minuto=sim_min,
                        diferenca_golos=score_home - score_away
                    )
                    
                    # Mostrar resultado com cores
                    st.markdown("### 📊 RESULTADO DA PREDIÇÃO")
                    
                    col_res1, col_res2, col_res3 = st.columns(3)
                    
                    with col_res1:
                        st.metric(
                            "Probabilidade DEFESA",
                            f"{prob:.1f}%",
                            delta=f"{prob - 50:.1f}pp vs média" if prob > 50 else f"{prob - 50:.1f}pp vs média"
                        )
                    
                    with col_res2:
                        st.metric(
                            "Probabilidade GOLO",
                            f"{100 - prob:.1f}%",
                            delta=None
                        )
                    
                    with col_res3:
                        # Recomendação
                        if prob > 65:
                            st.success("✅ ALTA confiança")
                            recomendacao = "Manter posicionamento"
                        elif prob > 50:
                            st.info("➡️ MÉDIA confiança")
                            recomendacao = "Atenção redobrada"
                        else:
                            st.error("⚠️ RISCO elevado")
                            recomendacao = "Considerar ajuste"
                        
                        st.markdown(f"**{recomendacao}**")
                    
                    # Barra de probabilidade visual
                    import plotly.graph_objects as go
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=prob,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Probabilidade de Defesa"},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 40], 'color': "lightcoral"},
                                {'range': [40, 60], 'color': "lightyellow"},
                                {'range': [60, 100], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 50
                            }
                        }
                    ))
                    
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Info do modelo
                    st.caption(f"🤖 Modelo: GBM | AUC: 0.562 | Treinado com {predictor.metadata.get('n_train', 'N/A')} lances")
                    
                except Exception as e:
                    st.error(f"❌ Erro na predição: {e}")
    
    with col_btn2:
        if st.button("🔄 Reset", use_container_width=True):
            st.rerun()
    
    # BONUS: Heatmap de probabilidades por zona
    with st.expander("🗺️ Ver Heatmap de Probabilidades (todas as zonas)"):
        with st.spinner("Calculando probabilidades para todas as zonas..."):
            try:
                import numpy as np
                
                probs_zonas = []
                for z in range(1, 10):
                    prob_z = predictor.predict(
                        zona=z,
                        distancia=sim_dist,
                        velocidade=sim_vel,
                        altura_gr=int(gr_info['altura_cm']),
                        envergadura_gr=int(gr_info['envergadura_cm']),
                        vel_lateral_gr=float(gr_info['velocidade_lateral_ms']),
                        minuto=sim_min,
                        diferenca_golos=score_home - score_away
                    )
                    probs_zonas.append(prob_z)
                
                # Reshape para 3x3
                probs_grid = np.array(probs_zonas).reshape(3, 3)
                
                # Criar heatmap
                fig_heat = go.Figure(data=go.Heatmap(
                    z=probs_grid,
                    x=['Esquerda', 'Centro', 'Direita'],
                    y=['Superior', 'Meio', 'Inferior'],
                    colorscale='RdYlGn',
                    text=np.round(probs_grid, 1),
                    texttemplate='%{text}%',
                    textfont={"size": 16, "color": "white"},
                    zmin=0,
                    zmax=100,
                    colorbar=dict(title="Prob. (%)")
                ))
                
                fig_heat.update_layout(
                    title=f"Probabilidade de Defesa por Zona - {goalkeeper_nome}<br><sub>Contexto: {sim_dist}m, {sim_vel}km/h, min {sim_min}</sub>",
                    height=450,
                    yaxis=dict(autorange='reversed')
                )
                
                st.plotly_chart(fig_heat, use_container_width=True)
                
                # Análise automática
                zona_melhor = probs_zonas.index(max(probs_zonas)) + 1
                zona_pior = probs_zonas.index(min(probs_zonas)) + 1
                
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.success(f"✅ **Zona Mais Forte**: Zona {zona_melhor} ({max(probs_zonas):.1f}%)")
                with col_a2:
                    st.error(f"⚠️ **Zona Mais Vulnerável**: Zona {zona_pior} ({min(probs_zonas):.1f}%)")
                
            except Exception as e:
                st.error(f"Erro ao gerar heatmap: {e}")

else:
    st.warning("""
    ⚠️ **Modelo H2O.ai não disponível**
    
    Para ativar predições em tempo real:
    1. Execute: `python train_modelo_defesa.py`
    2. Reinicie o dashboard
    
    O modelo permite prever probabilidades de defesa baseadas em Machine Learning!
    """)

st.caption("⏱️ Interface otimizada para decisões em 60-90 segundos")
