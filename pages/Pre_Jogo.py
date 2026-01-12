"""
Dashboard Pré-Jogo - Digital Twin ABC Braga
Preparação tática 24-48h antes do confronto
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data_access import HandballDataAccess
import sys
sys.path.append('..')

# H2O
try:
    from models.predictor_defesa import DefesaPredictor
    H2O_OK = True
except:
    H2O_OK = False

# =============================================================================
# CONFIG
# =============================================================================
st.set_page_config(page_title="Pré-Jogo - ABC Braga", page_icon="📊", layout="wide")

with open('styles/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache_resource
def get_db():
    return HandballDataAccess()

@st.cache_resource
def get_predictor():
    if H2O_OK:
        try:
            return DefesaPredictor(model_dir='models')
        except:
            return None
    return None

db = get_db()
predictor = get_predictor()

# =============================================================================
# HEATMAP BALIZA (Superior em cima, Inferior em baixo)
# =============================================================================
def heatmap_baliza(grid, titulo="", height=400, destacar_fracas=None, escala_max=100):
    """Heatmap com baliza realista e opção de destacar zonas fracas"""
    grid_plot = np.flipud(grid)
    
    fig = go.Figure()
    
    # Heatmap
    fig.add_trace(go.Heatmap(
        z=grid_plot, x=[0, 1, 2], y=[0, 1, 2],
        colorscale='RdYlGn', zmin=0, zmax=escala_max,
        text=np.round(grid_plot, 0), texttemplate='%{text}%',
        textfont=dict(size=20, color='black', family='Arial Black'),
        showscale=False, xgap=3, ygap=3
    ))
    
    # Postes laterais listrados
    for i in range(8):
        c = '#C41E3A' if i % 2 == 0 else 'white'
        fig.add_shape(type='rect', x0=-0.6, x1=-0.45, y0=-0.5+i*0.4, y1=-0.5+(i+1)*0.4, 
                      fillcolor=c, line=dict(width=0))
        fig.add_shape(type='rect', x0=2.45, x1=2.6, y0=-0.5+i*0.4, y1=-0.5+(i+1)*0.4, 
                      fillcolor=c, line=dict(width=0))
    
    # Trave superior listrada
    for i in range(8):
        c = '#C41E3A' if i % 2 == 0 else 'white'
        fig.add_shape(type='rect', x0=-0.6+i*0.42, x1=-0.6+(i+1)*0.42, y0=2.45, y1=2.6, 
                      fillcolor=c, line=dict(width=0))
    
    # Destacar zonas fracas com borda vermelha
    if destacar_fracas:
        for zona_idx in destacar_fracas:
            row = zona_idx // 3
            col = zona_idx % 3
            y_plot = 2 - row
            x_plot = col
            fig.add_shape(type='rect', 
                         x0=x_plot-0.48, x1=x_plot+0.48, 
                         y0=y_plot-0.48, y1=y_plot+0.48,
                         line=dict(color='#ff0000', width=4),
                         fillcolor='rgba(0,0,0,0)')
    
    # Labels
    fig.add_annotation(x=0, y=-0.75, text="Esq", showarrow=False, 
                      font=dict(size=10, color='#666'))
    fig.add_annotation(x=1, y=-0.75, text="Centro", showarrow=False, 
                      font=dict(size=10, color='#666'))
    fig.add_annotation(x=2, y=-0.75, text="Dir", showarrow=False, 
                      font=dict(size=10, color='#666'))
    fig.add_annotation(x=-0.85, y=2, text="Sup", showarrow=False, 
                      font=dict(size=10, color='#666'))
    fig.add_annotation(x=-0.85, y=1, text="Meio", showarrow=False, 
                      font=dict(size=10, color='#666'))
    fig.add_annotation(x=-0.85, y=0, text="Inf", showarrow=False, 
                      font=dict(size=10, color='#666'))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)),
        height=height,
        xaxis=dict(showgrid=False, showticklabels=False, range=[-1.1, 3.1], fixedrange=True),
        yaxis=dict(showgrid=False, showticklabels=False, scaleanchor='x', range=[-1, 3.1], fixedrange=True),
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def get_distribuicao_adversario(adv):
    """Retorna grid 3x3 com distribuição de remates do adversário"""
    alta = adv['remates_zona_alta_perc']
    media = adv['remates_zona_media_perc']
    baixa = adv['remates_zona_baixa_perc']
    
    # Distribuir cada faixa pelas 3 colunas (Esq, Centro, Dir)
    # grid[0]=Superior, grid[1]=Meio, grid[2]=Inferior
    grid = np.array([
        [alta * 0.28, alta * 0.44, alta * 0.28],      # Total = alta
        [media * 0.35, media * 0.30, media * 0.35],   # Total = media
        [baixa * 0.30, baixa * 0.40, baixa * 0.30]    # Total = baixa
    ])
    
    # Normalizar para somar 100%
    total = grid.sum()
    if total > 0:
        grid = (grid / total) * 100
    
    return grid


def calcular_probs_h2o(gr, predictor, dist, vel, minuto, dif):
    """Calcula prob defesa para 9 zonas, retorna grid 3x3"""
    probs = []
    for zona in range(1, 10):
        try:
            p = predictor.predict(
                zona=zona, distancia=dist, velocidade=vel,
                altura_gr=int(gr['altura_cm']),
                envergadura_gr=int(gr['envergadura_cm']),
                vel_lateral_gr=float(gr['velocidade_lateral_ms']),
                minuto=minuto, diferenca_golos=dif
            )
            probs.append(p)
        except:
            probs.append(50.0)
    
    # Zonas 1-3=Superior, 4-6=Meio, 7-9=Inferior
    grid = np.array(probs).reshape(3, 3)
    return grid


def calcular_media_ponderada(grid_defesa, grid_adversario):
    """Média ponderada: onde adversário ataca mais pesa mais"""
    pesos = grid_adversario / grid_adversario.sum()
    return np.sum(grid_defesa * pesos)

# =============================================================================
# VERIFICAR H2O
# =============================================================================
if not predictor:
    st.error("⚠️ Modelo H2O não disponível. Executa: `python train_modelo_defesa.py`")
    st.stop()

# =============================================================================
# SIDEBAR (primeiro!)
# =============================================================================
with st.sidebar:
    st.markdown("## ⚔️ Confronto")
    
    # Adversário
    query = "SELECT id, nome FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        advs = pd.read_sql_query(query, conn)
    
    adv_nome = st.selectbox("Adversário", advs['nome'].tolist())
    adv_id = int(advs[advs['nome'] == adv_nome]['id'].values[0])
    
    query = "SELECT * FROM adversarios WHERE id = ?"
    with db.get_connection() as conn:
        adv = pd.read_sql_query(query, conn, params=(adv_id,)).iloc[0]
    
    st.divider()
    st.markdown("## ⚙️ Condições")
    
    cond_minuto = st.slider("Minuto", 0, 60, 30)
    cond_dif = st.slider("Diferença Golos", -5, 5, 0)
    cond_dist = st.slider("Distância (m)", 6.0, 12.0, 9.0, 0.5)
    cond_vel = st.slider("Velocidade (km/h)", 70, 120, int(adv['velocidade_media_remate_kmh']))
    
    st.divider()
    st.caption(f"🤖 H2O.ai | AUC: 0.561")

# =============================================================================
# HEADER (depois da sidebar!)
# =============================================================================
st.markdown(f"""
<div style="background: linear-gradient(90deg, #1a1a2e, #16213e); 
            padding: 15px 25px; border-radius: 10px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 28px; font-weight: bold; color: white;">📊 PRÉ-JOGO</span>
            <span style="font-size: 18px; color: #ccc; margin-left: 20px;">Preparação tática</span>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 24px; font-weight: bold; color: white;">vs {adv_nome}</span>
            <div style="font-size: 12px; color: #888;">{adv['velocidade_media_remate_kmh']} km/h | {adv['estilo_ofensivo']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# CARREGAR DADOS (continua...)
# =============================================================================

# =============================================================================
# CARREGAR DADOS
# =============================================================================
# GRs
query = "SELECT * FROM guarda_redes"
with db.get_connection() as conn:
    grs = pd.read_sql_query(query, conn)

# Distribuição adversário
dist_adv = get_distribuicao_adversario(adv)

# Calcular ranking H2O
ranking = []
for _, gr in grs.iterrows():
    grid = calcular_probs_h2o(gr, predictor, cond_dist, cond_vel, cond_minuto, cond_dif)
    media = calcular_media_ponderada(grid, dist_adv)
    ranking.append({
        'id': gr['id'],
        'nome': gr['nome'],
        'altura': gr['altura_cm'],
        'enverg': gr['envergadura_cm'],
        'grid': grid,
        'media': media
    })

ranking = sorted(ranking, key=lambda x: x['media'], reverse=True)

# =============================================================================
# TABS
# =============================================================================
tab1, tab2, tab3 = st.tabs(["🎯 Adversário", "🥅 Qual GR?", "🔮 E Se...?"])

# =============================================================================
# TAB 1: ADVERSÁRIO
# =============================================================================
with tab1:
    st.markdown(f"## 🎯 Como ataca o **{adv_nome}**?")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📍 Distribuição de Remates")
        fig = heatmap_baliza(dist_adv, "", 400, escala_max=25)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Zona mais atacada
        idx = np.unravel_index(dist_adv.argmax(), dist_adv.shape)
        zonas = {(0,0): "Superior Esquerda", (0,1): "Superior Centro", (0,2): "Superior Direita",
                 (1,0): "Meio Esquerda", (1,1): "Meio Centro", (1,2): "Meio Direita",
                 (2,0): "Inferior Esquerda", (2,1): "Inferior Centro", (2,2): "Inferior Direita"}
        st.warning(f"⚠️ **Zona preferida**: {zonas[idx]} ({dist_adv[idx]:.1f}%)")
    
    with col2:
        st.markdown("### ⚡ Características & Alertas")
        
        # CARACTERÍSTICAS - Cards bonitos
        st.markdown("#### 📊 Perfil do Adversário")
        
        cols_metricas = st.columns(2)
        with cols_metricas[0]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                <div style="font-size: 12px; color: #fff; opacity: 0.9;">🚀 Velocidade</div>
                <div style="font-size: 28px; font-weight: bold; color: #fff;">{adv['velocidade_media_remate_kmh']}</div>
                <div style="font-size: 11px; color: #fff; opacity: 0.8;">km/h</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 15px; border-radius: 10px; text-align: center;">
                <div style="font-size: 12px; color: #fff; opacity: 0.9;">🎯 1ª Linha</div>
                <div style="font-size: 28px; font-weight: bold; color: #fff;">{adv['eficacia_primeira_linha_perc']}</div>
                <div style="font-size: 11px; color: #fff; opacity: 0.8;">% eficácia</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols_metricas[1]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                <div style="font-size: 12px; color: #fff; opacity: 0.9;">⚡ Transições</div>
                <div style="font-size: 28px; font-weight: bold; color: #fff;">{adv['transicoes_rapidas_jogo']}</div>
                <div style="font-size: 11px; color: #fff; opacity: 0.8;">por jogo</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 15px; border-radius: 10px; text-align: center;">
                <div style="font-size: 12px; color: #fff; opacity: 0.9;">🎯 2ª Linha</div>
                <div style="font-size: 28px; font-weight: bold; color: #fff;">{adv['eficacia_segunda_linha_perc']}</div>
                <div style="font-size: 11px; color: #fff; opacity: 0.8;">% eficácia</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # ALERTAS - Cards coloridos
        st.markdown("#### 🚨 Pontos de Atenção")
        
        alertas_ativos = []
        
        if adv['velocidade_media_remate_kmh'] > 100:
            alertas_ativos.append(("🔴", "Remates muito rápidos!", "#dc3545"))
        
        if adv['transicoes_rapidas_jogo'] > 20:
            alertas_ativos.append(("🔴", "Muitas transições rápidas!", "#dc3545"))
        
        if adv['eficacia_primeira_linha_perc'] > 65:
            alertas_ativos.append(("🟠", "Alta eficácia na 1ª linha", "#ffc107"))
        
        if alertas_ativos:
            for icon, msg, cor in alertas_ativos:
                st.markdown(f"""
                <div style="background: {cor}22; border-left: 5px solid {cor}; 
                            padding: 12px 15px; border-radius: 8px; margin-bottom: 8px;">
                    <span style="font-size: 18px; margin-right: 10px;">{icon}</span>
                    <span style="font-size: 14px; font-weight: bold; color: {cor};">{msg}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #28a74522; border-left: 5px solid #28a745; 
                        padding: 12px 15px; border-radius: 8px;">
                <span style="font-size: 18px; margin-right: 10px;">✅</span>
                <span style="font-size: 14px; font-weight: bold; color: #28a745;">Adversário equilibrado</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        st.caption(f"**Estilo ofensivo:** {adv['estilo_ofensivo']}")
    
# =============================================================================
# TAB 2: QUAL GR?
# =============================================================================
with tab2:
    st.markdown(f"## 🥅 Qual GR usar contra **{adv_nome}**?")
    st.caption(f"Condições: min {cond_minuto} | dif {cond_dif:+d} | {cond_dist}m | {cond_vel} km/h")
    
    # Semáforo - 3 cards
    cols = st.columns(3)
    
    for i, r in enumerate(ranking):
        with cols[i]:
            taxa = r['media']
            
            if taxa >= 55:
                cor, icon = "#28a745", "✅"
            elif taxa >= 45:
                cor, icon = "#ffc107", "➡️"
            else:
                cor, icon = "#dc3545", "⚠️"
            
            borda = "4px solid gold" if i == 0 else f"2px solid {cor}"
            
            st.markdown(f"""
            <div style="background:{cor}22; border:{borda}; border-radius:12px; 
                        padding:20px; text-align:center;">
                <div style="font-size:28px">{icon}</div>
                <div style="font-size:18px; font-weight:bold">{r['nome']}</div>
                <div style="font-size:36px; font-weight:bold; color:{cor}">{taxa:.1f}%</div>
                <div style="font-size:12px; color:#666">{r['altura']}cm | {r['enverg']}cm</div>
                {"<div style='color:gold; margin-top:8px'>⭐ RECOMENDADO</div>" if i==0 else ""}
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Insight
    diff = ranking[0]['media'] - ranking[1]['media']
    if diff > 5:
        st.success(f"✅ **{ranking[0]['nome']}** é claramente o melhor (+{diff:.1f}pp)")
    elif diff > 2:
        st.info(f"➡️ **{ranking[0]['nome']}** tem ligeira vantagem (+{diff:.1f}pp)")
    else:
        st.warning(f"⚠️ Diferença mínima ({diff:.1f}pp) - considerar outros fatores")
    
    st.divider()
    
    # Heatmaps
    st.markdown("### 🗺️ Probabilidade de Defesa por Zona")
    cols = st.columns(3)
    
    for i, r in enumerate(ranking):
        with cols[i]:
            st.markdown(f"**{r['nome']}** ({r['media']:.1f}%)")
            fig = heatmap_baliza(r['grid'], "", 280)
            st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# TAB 3: E SE...?
# =============================================================================
with tab3:
    st.markdown("## 🔮 E Se...?")
    st.info("💡 Ajusta os parâmetros e vê como muda a recomendação")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ Cenário")
        
        sim_min = st.slider("Minuto", 0, 60, 45, key="sim_min")
        sim_dif = st.slider("Diferença", -5, 5, -2, key="sim_dif")
        sim_dist = st.slider("Distância", 6.0, 12.0, 7.0, key="sim_dist")
        sim_vel = st.slider("Velocidade", 70, 120, 105, key="sim_vel")
        
        st.caption("📝 Cenário: Final de jogo, a perder, remates de perto e rápidos")
    
    with col2:
        st.markdown("### 📊 Novo Ranking")
        
        # Recalcular
        ranking_sim = []
        for _, gr in grs.iterrows():
            grid = calcular_probs_h2o(gr, predictor, sim_dist, sim_vel, sim_min, sim_dif)
            media = calcular_media_ponderada(grid, dist_adv)
            ranking_sim.append({'nome': gr['nome'], 'media': media, 'grid': grid})
        
        ranking_sim = sorted(ranking_sim, key=lambda x: x['media'], reverse=True)
        
        # Mostrar
        for i, r in enumerate(ranking_sim):
            if i == 0:
                st.success(f"🥇 **{r['nome']}**: {r['media']:.1f}%")
            elif i == 1:
                st.info(f"🥈 **{r['nome']}**: {r['media']:.1f}%")
            else:
                st.warning(f"🥉 **{r['nome']}**: {r['media']:.1f}%")
        
        st.divider()
        
        # Comparar com original
        if ranking[0]['nome'] != ranking_sim[0]['nome']:
            st.error(f"🔄 **MUDANÇA!** Neste cenário, **{ranking_sim[0]['nome']}** é melhor que {ranking[0]['nome']}")
        else:
            st.success(f"✅ **{ranking[0]['nome']}** continua a ser o melhor")
        
        st.divider()
        
        # Heatmap do melhor
        st.markdown(f"### 🗺️ {ranking_sim[0]['nome']} neste cenário")
        fig = heatmap_baliza(ranking_sim[0]['grid'], "", 350)
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("📊 Pré-Jogo | Digital Twin ABC Braga | H2O.ai AutoML")