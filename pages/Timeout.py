"""
Dashboard de Timeout em Jogo - VERSÃO DINÂMICA
Simulação em tempo real para decisões táticas
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.append('..')

from data_access import HandballDataAccess
from utils.visualizations import (
    criar_heatmap_baliza,
    criar_grafico_compatibilidade_barras
)

# Import do predictor H2O
try:
    from models.predictor_defesa import DefesaPredictor
    H2O_AVAILABLE = True
except ImportError:
    H2O_AVAILABLE = False

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================
st.set_page_config(
    page_title="Timeout em Jogo - ABC Braga",
    page_icon="⏱️",
    layout="wide"
)

with open('styles/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache_resource
def get_db():
    return HandballDataAccess()

@st.cache_resource
def get_predictor():
    if not H2O_AVAILABLE:
        return None
    try:
        return DefesaPredictor(model_dir='models')
    except Exception as e:
        st.warning(f"⚠️ Modelo não disponível: {e}")
        return None

db = get_db()
predictor = get_predictor()

# =============================================================================
# HEADER
# =============================================================================
st.markdown('<div class="main-header">⏱️ Timeout Tático (90 segundos)</div>', unsafe_allow_html=True)
st.markdown("**Simulador Dinâmico com IA**")
st.divider()

# =============================================================================
# SIDEBAR - CONTEXTO
# =============================================================================
with st.sidebar:
    st.markdown("## ⚡ Contexto do Jogo")
    
    query = "SELECT id, nome FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        adversarios_df = pd.read_sql_query(query, conn)
    
    adversario_nome = st.selectbox("Adversário", adversarios_df['nome'].tolist(), index=0)
    adversario_id = adversarios_df[adversarios_df['nome'] == adversario_nome]['id'].values[0]
    
    st.divider()
    
    st.markdown("### 🥅 GR em Campo")
    grs_df = db.get_all_goalkeepers()
    goalkeeper_nome = st.selectbox("Atleta", grs_df['nome'].tolist(), index=0)
    gr_id = grs_df[grs_df['nome'] == goalkeeper_nome]['id'].values[0]
    
    st.divider()
    
    st.markdown("### 📊 Situação")
    game_time = st.slider("Minuto do Jogo", 0, 60, 42)
    
    col1, col2 = st.columns(2)
    with col1:
        score_home = st.number_input("ABC", 0, 50, 24)
    with col2:
        score_away = st.number_input(adversario_nome[:10], 0, 50, 24)
    
    diferenca = score_home - score_away

# Buscar info do GR
query_gr = "SELECT * FROM guarda_redes WHERE nome = ?"
with db.get_connection() as conn:
    gr_info_df = pd.read_sql_query(query_gr, conn, params=(goalkeeper_nome,))
    gr_info = gr_info_df.iloc[0] if len(gr_info_df) > 0 else None

if gr_info is None or len(gr_info_df) == 0:
    st.error("Erro ao carregar GR")
    st.stop()

# =============================================================================
# MÉTRICAS
# =============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("⏰ Tempo", f"{game_time} min", f"{60-game_time} min rest.")

with col2:
    st.metric("🎯 Resultado", f"{score_home} - {score_away}", f"{diferenca:+d}")

with col3:
    query = "SELECT taxa_defesa_global FROM epocas WHERE guarda_redes_id = ? AND epoca = 2025"
    with db.get_connection() as conn:
        taxa_df = pd.read_sql_query(query, conn, params=(gr_id,))
    taxa = taxa_df['taxa_defesa_global'].values[0] if len(taxa_df) > 0 else 0.0
    st.metric("🥅 Eficácia Época", f"{taxa:.1f}%")

with col4:
    remaining = max(0, 90 - (datetime.now().second % 90))
    st.metric("⏳ Timeout", f"{remaining}s")

st.divider()

# =============================================================================
# COMPATIBILIDADE
# =============================================================================
# =============================================================================
# COMPATIBILIDADE (calculada em tempo real)
# =============================================================================
st.markdown("## 🎯 Performance vs Adversário")

# Calcular compatibilidade a partir dos jogos REAIS
query_compat = """
SELECT 
    gr.nome,
    COUNT(DISTINCT j.id) as jogos,
    COUNT(l.id) as remates,
    SUM(CASE WHEN l.resultado = 'Defesa' THEN 1 ELSE 0 END) as defesas,
    ROUND(AVG(CASE WHEN l.resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa_defesa_perc
FROM guarda_redes gr
JOIN jogos j ON gr.id = j.guarda_redes_id
JOIN lances l ON j.id = l.jogo_id
WHERE j.adversario_id = ?
GROUP BY gr.id, gr.nome
ORDER BY taxa_defesa_perc DESC
"""

with db.get_connection() as conn:
    compat_real = pd.read_sql_query(query_compat, conn, params=(adversario_id,))

if len(compat_real) > 0:
    col_c1, col_c2 = st.columns([2, 1])
    
    with col_c1:
        fig = criar_grafico_compatibilidade_barras(compat_real)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_c2:
        melhor = compat_real.iloc[0]
        if melhor['nome'] == goalkeeper_nome:
            st.success(f"✅ **{goalkeeper_nome}** é a melhor opção")
            st.metric("Taxa vs {adversario_nome}", f"{melhor['taxa_defesa_perc']:.1f}%")
            st.caption(f"{int(melhor['jogos'])} jogos | {int(melhor['remates'])} remates")
        else:
            atual = compat_real[compat_real['nome']==goalkeeper_nome]
            if len(atual) > 0:
                delta = melhor['taxa_defesa_perc'] - atual['taxa_defesa_perc'].values[0]
                st.warning(f"⚠️ **SUGESTÃO:** {melhor['nome']}")
                st.metric("Ganho Potencial", f"+{delta:.1f}pp")
else:
    st.info("Sem jogos históricos vs este adversário")

# =============================================================================
# SIMULADOR DINÂMICO
# =============================================================================
if not predictor:
    st.error("⚠️ Simulador indisponível. Execute: python train_modelo_defesa_v2.py")
    st.stop()

st.markdown("## 🔮 Simulador: **E SE...?**")
st.info("💡 Ajusta parâmetros e vê o impacto na probabilidade de defesa")

tab1, tab2, tab3 = st.tabs(["🎯 Lance Individual", "🗺️ Heatmap Zonas", "⚖️ Comparador"])

# =============================================================================
# TAB 1: LANCE INDIVIDUAL
# =============================================================================
with tab1:
    st.markdown("### Simula um lance específico")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎯 Remate**")
        sim_zona = st.selectbox(
            "Zona da Baliza",
            list(range(1, 10)),
            format_func=lambda x: {
                1: "1-Sup.Esq", 2: "2-Sup.Centro", 3: "3-Sup.Dir",
                4: "4-Méd.Esq", 5: "5-Méd.Centro", 6: "6-Méd.Dir",
                7: "7-Inf.Esq", 8: "8-Inf.Centro", 9: "9-Inf.Dir"
            }[x],
            index=4
        )
        sim_dist = st.slider("Distância (m)", 6.0, 12.0, 9.0, 0.5)
        sim_vel = st.slider("Velocidade (km/h)", 70, 120, 95, 5)
    
    with col2:
        st.markdown("**⚙️ Ajustes Táticos**")
        ajuste_pos = st.slider(
            "Posicionamento (cm)",
            -30, 30, 0, 5,
            help="- = atrás, + = avançado"
        )
        ajuste_vel = st.slider(
            "Velocidade lateral (%)",
            -20, 20, 0, 5,
            help="Motivação/fadiga"
        )
        st.caption(f"📍 Ajuste: {ajuste_pos:+d}cm")
        st.caption(f"⚡ Vel: {ajuste_vel:+d}%")
    
    with col3:
        st.markdown("**📊 RESULTADO**")
        
        try:
            dist_adj = max(6.0, min(12.0, sim_dist - ajuste_pos/100))
            vel_lateral_adj = gr_info['velocidade_lateral_ms'] * (1 + ajuste_vel/100)
            
            prob = predictor.predict(
                zona=sim_zona,
                distancia=dist_adj,
                velocidade=sim_vel,
                altura_gr=int(gr_info['altura_cm']),
                envergadura_gr=int(gr_info['envergadura_cm']),
                vel_lateral_gr=float(vel_lateral_adj),
                minuto=game_time,
                diferenca_golos=diferenca
            )
            
            st.metric("Prob. DEFESA", f"{prob:.1f}%")
            
            if prob > 60:
                st.success("✅ ALTA confiança")
            elif prob > 45:
                st.info("➡️ MÉDIA confiança")
            else:
                st.error("⚠️ RISCO elevado")
            
            # Gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob,
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 40], 'color': "lightcoral"},
                        {'range': [40, 60], 'color': "lightyellow"},
                        {'range': [60, 100], 'color': "lightgreen"}
                    ]
                }
            ))
            fig.update_layout(height=200, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro: {e}")

# =============================================================================
# TAB 2: HEATMAP DINÂMICO
# =============================================================================
with tab2:
    st.markdown("### Mapa de probabilidades - TODAS as zonas")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**⚙️ Parâmetros**")
        heat_dist = st.slider("Distância", 6.0, 12.0, 9.0, 0.5, key="h_dist")
        heat_vel = st.slider("Velocidade", 70, 120, 95, 5, key="h_vel")
        st.divider()
        st.markdown(f"**GR:** {goalkeeper_nome}")
        st.caption(f"{gr_info['altura_cm']}cm | {gr_info['envergadura_cm']}cm enverg.")
    
    with col2:
        try:
            probs = []
            for z in range(1, 10):
                p = predictor.predict(
                    zona=z, distancia=heat_dist, velocidade=heat_vel,
                    altura_gr=int(gr_info['altura_cm']),
                    envergadura_gr=int(gr_info['envergadura_cm']),
                    vel_lateral_gr=float(gr_info['velocidade_lateral_ms']),
                    minuto=game_time, diferenca_golos=diferenca
                )
                probs.append(p)
            
            grid = np.array(probs).reshape(3, 3)
            
            fig = go.Figure(data=go.Heatmap(
                z=grid,
                x=['Esquerda', 'Centro', 'Direita'],
                y=['Superior', 'Meio', 'Inferior'],
                colorscale='RdYlGn',
                text=np.round(grid, 1),
                texttemplate='%{text}%',
                textfont={"size": 18, "color": "white", "family": "Arial Black"},
                zmin=0, zmax=100,
                colorbar=dict(title="Prob. (%)")
            ))
            
            fig.update_layout(
                title=f"{goalkeeper_nome} | {heat_dist}m | {heat_vel}km/h",
                height=500,
                yaxis=dict(autorange='reversed')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            melhor_idx = probs.index(max(probs))
            pior_idx = probs.index(min(probs))
            
            col1, col2 = st.columns(2)
            col1.success(f"✅ Zona {melhor_idx+1}: {max(probs):.1f}%")
            col2.error(f"⚠️ Zona {pior_idx+1}: {min(probs):.1f}%")
            
        except Exception as e:
            st.error(f"Erro: {e}")

# =============================================================================
# TAB 3: COMPARADOR
# =============================================================================
with tab3:
    st.markdown("### Compara 2 cenários")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔵 Cenário A")
        za = st.selectbox("Zona", range(1,10), index=4, key="za", format_func=lambda x: f"Z{x}")
        da = st.slider("Dist.", 6.0, 12.0, 9.0, key="da")
        va = st.slider("Vel.", 70, 120, 95, 5, key="va")
        
        try:
            pa = predictor.predict(
                za, da, va, int(gr_info['altura_cm']),
                int(gr_info['envergadura_cm']),
                float(gr_info['velocidade_lateral_ms']),
                game_time, diferenca
            )
            st.metric("Probabilidade", f"{pa:.1f}%")
        except:
            pa = 0
    
    with col2:
        st.markdown("#### 🔴 Cenário B")
        zb = st.selectbox("Zona", range(1,10), index=8, key="zb", format_func=lambda x: f"Z{x}")
        db_val = st.slider("Dist.", 6.0, 12.0, 7.0, key="db")
        vb = st.slider("Vel.", 70, 120, 110, 5, key="vb")
        
        try:
            pb = predictor.predict(
                zb, db_val, vb, int(gr_info['altura_cm']),
                int(gr_info['envergadura_cm']),
                float(gr_info['velocidade_lateral_ms']),
                game_time, diferenca
            )
            st.metric("Probabilidade", f"{pb:.1f}%")
        except:
            pb = 0
    
    if pa > 0 and pb > 0:
        st.divider()
        delta = pa - pb
        
        if abs(delta) < 5:
            st.info(f"➡️ Equivalentes (Δ={delta:.1f}pp)")
        elif delta > 0:
            st.success(f"✅ A é melhor (+{delta:.1f}pp)")
        else:
            st.warning(f"⚠️ B é melhor (+{abs(delta):.1f}pp)")
        
        fig = go.Figure([
            go.Bar(name='A', x=['Prob'], y=[pa], marker_color='lightblue'),
            go.Bar(name='B', x=['Prob'], y=[pb], marker_color='lightcoral')
        ])
        fig.update_layout(height=300, yaxis=dict(range=[0,100]))
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("⏱️ Timeout otimizado para 60-90s | 🤖 H2O.ai AutoML")