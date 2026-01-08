"""
Dashboard Timeout - Digital Twin ABC Braga
Decisão rápida em 60-90 segundos
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
st.set_page_config(page_title="Timeout - ABC Braga", page_icon="⏱️", layout="wide")

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
# HEATMAP BALIZA
# =============================================================================
def heatmap_baliza(grid, titulo="", height=350):
    """Heatmap com baliza realista - grid[0]=Superior, grid[1]=Meio, grid[2]=Inferior"""
    grid_plot = np.flipud(grid)
    
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=grid_plot, x=[0, 1, 2], y=[0, 1, 2],
        colorscale='RdYlGn', zmin=0, zmax=100,
        text=np.round(grid_plot, 0), texttemplate='%{text}%',
        textfont=dict(size=20, color='black', family='Arial Black'),
        showscale=False, xgap=3, ygap=3
    ))
    
    # Postes listrados
    for i in range(8):
        c = '#C41E3A' if i % 2 == 0 else 'white'
        fig.add_shape(type='rect', x0=-0.6, x1=-0.45, y0=-0.5+i*0.4, y1=-0.5+(i+1)*0.4, fillcolor=c, line=dict(width=0))
        fig.add_shape(type='rect', x0=2.45, x1=2.6, y0=-0.5+i*0.4, y1=-0.5+(i+1)*0.4, fillcolor=c, line=dict(width=0))
    for i in range(8):
        c = '#C41E3A' if i % 2 == 0 else 'white'
        fig.add_shape(type='rect', x0=-0.6+i*0.42, x1=-0.6+(i+1)*0.42, y0=2.45, y1=2.6, fillcolor=c, line=dict(width=0))
    
    # Rede
    for i in range(-5, 10):
        fig.add_shape(type='line', x0=-0.5, x1=2.5, y0=-0.5+i*0.4, y1=0.5+i*0.4, line=dict(color='rgba(150,150,150,0.15)', width=1))
        fig.add_shape(type='line', x0=-0.5, x1=2.5, y0=2.5-i*0.4, y1=1.5-i*0.4, line=dict(color='rgba(150,150,150,0.15)', width=1))
    
    # Labels
    fig.add_annotation(x=0, y=-0.75, text="Esq", showarrow=False, font=dict(size=10, color='#666'))
    fig.add_annotation(x=1, y=-0.75, text="Centro", showarrow=False, font=dict(size=10, color='#666'))
    fig.add_annotation(x=2, y=-0.75, text="Dir", showarrow=False, font=dict(size=10, color='#666'))
    fig.add_annotation(x=-0.85, y=2, text="Sup", showarrow=False, font=dict(size=10, color='#666'))
    fig.add_annotation(x=-0.85, y=1, text="Meio", showarrow=False, font=dict(size=10, color='#666'))
    fig.add_annotation(x=-0.85, y=0, text="Inf", showarrow=False, font=dict(size=10, color='#666'))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)), height=height,
        xaxis=dict(showgrid=False, showticklabels=False, range=[-1.1, 3.1]),
        yaxis=dict(showgrid=False, showticklabels=False, scaleanchor='x', range=[-1, 3.1]),
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# =============================================================================
# CALCULAR PROBS H2O
# =============================================================================
def calcular_probs_gr(gr, predictor, dist, vel, minuto, dif):
    """Retorna grid 3x3 e média"""
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
    
    grid = np.array(probs).reshape(3, 3)
    media = np.mean(probs)
    return grid, media, probs

# =============================================================================
# GERAR RECOMENDAÇÕES TÁTICAS
# =============================================================================
def gerar_recomendacoes_posicionamento(zona_adv_forte, zona_gr_fraca, minuto, diferenca, probs_gr, adv_info):
    """Gera recomendações táticas específicas de posicionamento"""
    
    recomendacoes = []
    
    zonas_nome = {
        0: "Superior Esquerda", 1: "Superior Centro", 2: "Superior Direita",
        3: "Meio Esquerda", 4: "Meio Centro", 5: "Meio Direita",
        6: "Inferior Esquerda", 7: "Inferior Centro", 8: "Inferior Direita"
    }
    
    # =================================================================
    # 1. ALERTA CRÍTICO (sempre primeiro)
    # =================================================================
    if zona_adv_forte == zona_gr_fraca:
        recomendacoes.append({
            'icon': '🚨', 'titulo': f'RISCO CRÍTICO - {zonas_nome[zona_adv_forte]}',
            'descricao': 'Zona fraca = Zona preferida do adversário! Reforçar este lado.',
            'prioridade': 'critica'
        })
    
    # =================================================================
    # 2. POSIÇÃO LATERAL (baseada no padrão do adversário)
    # =================================================================
    # Zonas esquerdas: 0, 3, 6 | Zonas direitas: 2, 5, 8 | Centro: 1, 4, 7
    zonas_esq = [0, 3, 6]
    zonas_dir = [2, 5, 8]
    zonas_centro = [1, 4, 7]
    
    if zona_adv_forte in zonas_esq:
        recomendacoes.append({
            'icon': '⬅️', 'titulo': 'Descair para ESQUERDA',
            'descricao': 'Adversário ataca mais pela esquerda - aproximar do poste esquerdo',
            'prioridade': 'alta'
        })
    elif zona_adv_forte in zonas_dir:
        recomendacoes.append({
            'icon': '➡️', 'titulo': 'Descair para DIREITA',
            'descricao': 'Adversário ataca mais pela direita - aproximar do poste direito',
            'prioridade': 'alta'
        })
    else:
        recomendacoes.append({
            'icon': '⚖️', 'titulo': 'Manter CENTRO',
            'descricao': 'Adversário ataca pelo centro - posição central equilibrada',
            'prioridade': 'media'
        })
    
    # =================================================================
    # 3. POSIÇÃO VERTICAL (baseada na altura do ataque + velocidade)
    # =================================================================
    vel_adv = adv_info['velocidade_media_remate_kmh']
    
    # Zonas altas: 0, 1, 2 | Zonas médias: 3, 4, 5 | Zonas baixas: 6, 7, 8
    if zona_adv_forte in [0, 1, 2]:
        # Ataca alto
        if vel_adv >= 95:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'Posição RECUADA + ALTA',
                'descricao': f'Remates altos e fortes ({vel_adv:.0f}km/h) - recuar 30cm, braços altos',
                'prioridade': 'alta'
            })
        else:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'Posição NEUTRA + ALTA',
                'descricao': f'Remates altos mas lentos ({vel_adv:.0f}km/h) - manter posição, braços altos',
                'prioridade': 'media'
            })
    elif zona_adv_forte in [6, 7, 8]:
        # Ataca baixo
        recomendacoes.append({
            'icon': '📍', 'titulo': 'Posição AVANÇADA + BAIXA',
            'descricao': 'Remates baixos - avançar 30-40cm, baixar centro de gravidade',
            'prioridade': 'alta'
        })
        recomendacoes.append({
            'icon': '🦵', 'titulo': 'Pernas ATIVAS',
            'descricao': 'Flexionar joelhos, peso na ponta dos pés, pronto para mergulhar',
            'prioridade': 'alta'
        })
    else:
        # Ataca meio
        if vel_adv >= 95:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'Posição ligeiramente RECUADA',
                'descricao': f'Remates fortes ({vel_adv:.0f}km/h) - recuar 15-20cm para ter tempo',
                'prioridade': 'media'
            })
        else:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'Posição NEUTRA',
                'descricao': 'Manter posição base, braços preparados',
                'prioridade': 'media'
            })
    
    # =================================================================
    # 4. COMPENSAR ZONA FRACA DO GR
    # =================================================================
    prob_min = min(probs_gr)
    if prob_min < 45:
        lado_fraco = ""
        if zona_gr_fraca in zonas_esq:
            lado_fraco = "esquerdo"
        elif zona_gr_fraca in zonas_dir:
            lado_fraco = "direito"
        else:
            lado_fraco = "central"
        
        altura_fraca = ""
        if zona_gr_fraca in [0, 1, 2]:
            altura_fraca = "alto"
        elif zona_gr_fraca in [6, 7, 8]:
            altura_fraca = "baixo"
        else:
            altura_fraca = "meia-altura"
        
        recomendacoes.append({
            'icon': '🎯', 'titulo': f'Compensar zona FRACA ({prob_min:.0f}%)',
            'descricao': f'Canto {altura_fraca} {lado_fraco} - antecipar e pré-posicionar nesse lado',
            'prioridade': 'media'
        })
    
    # =================================================================
    # 5. CONTEXTO: RESULTADO + MINUTO (sem contradições)
    # =================================================================
    if diferenca <= -3:
        recomendacoes.append({
            'icon': '⚡', 'titulo': 'A PERDER muito - ARRISCAR',
            'descricao': 'Nada a perder - posição avançada, provocar erros, sair da baliza',
            'prioridade': 'alta'
        })
    elif diferenca < 0:
        if minuto >= 50:
            recomendacoes.append({
                'icon': '⚡', 'titulo': 'Final a PERDER - ARRISCAR',
                'descricao': 'Pouco tempo - ser agressivo, avançar na baliza',
                'prioridade': 'alta'
            })
        else:
            recomendacoes.append({
                'icon': '💪', 'titulo': 'A PERDER - Ser AGRESSIVO',
                'descricao': 'Precisas de defesas - posição mais avançada',
                'prioridade': 'media'
            })
    elif diferenca >= 3:
        recomendacoes.append({
            'icon': '🛡️', 'titulo': 'A GANHAR muito - GERIR',
            'descricao': 'Confortável - não arriscar, cobrir bem a baliza',
            'prioridade': 'media'
        })
    elif diferenca > 0:
        if minuto >= 50:
            recomendacoes.append({
                'icon': '🛡️', 'titulo': 'Final a GANHAR - CONSERVADOR',
                'descricao': 'Proteger vantagem - posição segura, não sair da baliza',
                'prioridade': 'alta'
            })
        else:
            recomendacoes.append({
                'icon': '✅', 'titulo': 'A GANHAR - Manter',
                'descricao': 'Continuar o que está a funcionar',
                'prioridade': 'baixa'
            })
    else:
        if minuto >= 50:
            recomendacoes.append({
                'icon': '⚖️', 'titulo': 'Final EMPATADO - Equilibrado',
                'descricao': 'Não cometer erros, esperar oportunidade',
                'prioridade': 'alta'
            })
        elif minuto <= 15:
            recomendacoes.append({
                'icon': '🟢', 'titulo': 'Início EMPATADO - Impor ritmo',
                'descricao': 'Ser agressivo, assumir riscos calculados',
                'prioridade': 'media'
            })
    
    return recomendacoes

# =============================================================================
# VERIFICAR H2O
# =============================================================================
if not predictor:
    st.error("⚠️ Modelo H2O não disponível")
    st.stop()

# =============================================================================
# SIDEBAR - CONTEXTO
# =============================================================================
with st.sidebar:
    st.markdown("## ⚡ CONTEXTO")
    
    query = "SELECT id, nome FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        advs = pd.read_sql_query(query, conn)
    
    adv_nome = st.selectbox("Adversário", advs['nome'].tolist())
    adv_id = int(advs[advs['nome'] == adv_nome]['id'].values[0])
    
    query = "SELECT * FROM adversarios WHERE id = ?"
    with db.get_connection() as conn:
        adv_info = pd.read_sql_query(query, conn, params=(adv_id,)).iloc[0]
    
    st.divider()
    
    query = "SELECT * FROM guarda_redes"
    with db.get_connection() as conn:
        grs = pd.read_sql_query(query, conn)
    
    gr_atual_nome = st.selectbox("GR em Campo", grs['nome'].tolist())
    gr_atual = grs[grs['nome'] == gr_atual_nome].iloc[0]
    
    st.divider()
    
    minuto = st.slider("Minuto", 0, 60, 42)
    
    col1, col2 = st.columns(2)
    with col1:
        golo_abc = st.number_input("ABC", 0, 50, 24)
    with col2:
        golo_adv = st.number_input("ADV", 0, 50, 24)
    
    diferenca = golo_abc - golo_adv
    
    st.divider()
    
    dist = st.slider("Distância", 6.0, 12.0, 9.0, 0.5)
    vel = st.slider("Velocidade", 70, 120, int(adv_info['velocidade_media_remate_kmh']))

# =============================================================================
# DISTRIBUIÇÃO ADVERSÁRIO
# =============================================================================
def get_dist_adversario(adv):
    alta = adv['remates_zona_alta_perc']
    media = adv['remates_zona_media_perc']
    baixa = adv['remates_zona_baixa_perc']
    
    return np.array([
        [alta * 0.28, alta * 0.44, alta * 0.28],
        [media * 0.35, media * 0.30, media * 0.35],
        [baixa * 0.30, baixa * 0.40, baixa * 0.30]
    ])

dist_adv = get_dist_adversario(adv_info)
zona_adv_forte_idx = np.argmax(dist_adv.flatten())

# =============================================================================
# CALCULAR RANKING
# =============================================================================
ranking = []
for _, gr in grs.iterrows():
    grid, media, probs = calcular_probs_gr(gr, predictor, dist, vel, minuto, diferenca)
    ranking.append({
        'id': gr['id'], 'nome': gr['nome'], 'altura': gr['altura_cm'],
        'envergadura': gr['envergadura_cm'], 'grid': grid, 'media': media, 'probs': probs
    })

ranking = sorted(ranking, key=lambda x: x['media'], reverse=True)
gr_atual_data = next(r for r in ranking if r['nome'] == gr_atual_nome)
melhor = ranking[0]
zona_gr_fraca_idx = np.argmin(gr_atual_data['probs'])

# =============================================================================
# HEADER
# =============================================================================
st.markdown(f"""
<div style="background: linear-gradient(90deg, #1a1a2e, #16213e); 
            padding: 15px 25px; border-radius: 10px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 28px; font-weight: bold; color: white;">⏱️ TIMEOUT</span>
            <span style="font-size: 18px; color: #ccc; margin-left: 20px;">Min {minuto} | vs {adv_nome}</span>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 32px; font-weight: bold; color: {'#28a745' if diferenca > 0 else '#dc3545' if diferenca < 0 else '#ffc107'};">
                {golo_abc} - {golo_adv}
            </span>
            <span style="font-size: 16px; color: #ccc; margin-left: 10px;">({diferenca:+d})</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# TABS: JOGO NORMAL vs PENALTY
# =============================================================================
tab_jogo, tab_penalty = st.tabs(["⚽ Jogo Normal", "🎯 Penalty (7m)"])

# =============================================================================
# TAB 1: JOGO NORMAL
# =============================================================================
with tab_jogo:
    st.markdown("### 🥅 QUEM DEVE ESTAR EM CAMPO?")
    cols = st.columns(3)
    
    for i, r in enumerate(ranking):
        with cols[i]:
            taxa = r['media']
            is_atual = r['nome'] == gr_atual_nome
            is_melhor = i == 0
            
            if taxa >= 55:
                cor, icon = "#28a745", "✅"
            elif taxa >= 45:
                cor, icon = "#ffc107", "➡️"
            else:
                cor, icon = "#dc3545", "⚠️"
            
            if is_atual and is_melhor:
                borda, badge = "4px solid gold", "⭐ EM CAMPO + RECOMENDADO"
            elif is_atual:
                borda, badge = "4px solid #17a2b8", "🔵 EM CAMPO"
            elif is_melhor:
                borda, badge = "4px solid gold", "⭐ RECOMENDADO"
            else:
                borda, badge = f"2px solid {cor}", ""
            
            # ESTE BLOCO TEM DE ESTAR AQUI DENTRO DO FOR
            st.markdown(f"""
            <div style="background: {cor}22; border: {borda}; border-radius: 12px; 
                        padding: 20px 15px; text-align: center; min-height: 180px; 
                        display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 28px; margin-bottom: 5px;">{icon}</div>
                <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">{r['nome']}</div>
                <div style="font-size: 42px; font-weight: bold; color: {cor}; line-height: 1;">{taxa:.0f}%</div>
                <div style="font-size: 11px; color: #888; margin-top: 8px;">{r['altura']}cm | {r['envergadura']}cm</div>
                <div style="font-size: 11px; color: gold; min-height: 16px; margin-top: 4px;">{badge if badge else ""}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # HEATMAP + DECISÃO
    col_heat, col_decisao = st.columns([2, 1])
    
    with col_heat:
        st.markdown(f"### 🗺️ {gr_atual_nome} - Prob. Defesa")
        fig = heatmap_baliza(gr_atual_data['grid'], f"Min {minuto} | {dist}m | {vel}km/h", 420)
        st.plotly_chart(fig, use_container_width=True)
        
        zonas_nome = ['Sup.Esq', 'Sup.Centro', 'Sup.Dir', 'Meio.Esq', 'Meio.Centro', 'Meio.Dir', 'Inf.Esq', 'Inf.Centro', 'Inf.Dir']
        probs_flat = gr_atual_data['probs']
        col1, col2 = st.columns(2)
        col1.success(f"✅ Forte: {zonas_nome[np.argmax(probs_flat)]} ({max(probs_flat):.0f}%)")
        col2.error(f"⚠️ Fraca: {zonas_nome[np.argmin(probs_flat)]} ({min(probs_flat):.0f}%)")

    with col_decisao:
        st.markdown("### 💡 DECISÃO")
        diff = melhor['media'] - gr_atual_data['media']
        
        if melhor['nome'] == gr_atual_nome:
            st.markdown(f"""
            <div style="background: #28a74533; border: 3px solid #28a745; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 40px;">✅</div>
                <div style="font-size: 22px; font-weight: bold; color: #28a745;">MANTER</div>
                <div style="font-size: 16px;">{gr_atual_nome}</div>
            </div>
            """, unsafe_allow_html=True)
        elif diff > 5:
            st.markdown(f"""
            <div style="background: #dc354533; border: 3px solid #dc3545; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 40px;">🔄</div>
                <div style="font-size: 22px; font-weight: bold; color: #dc3545;">TROCAR</div>
                <div style="font-size: 14px;">{gr_atual_nome} → <b>{melhor['nome']}</b></div>
                <div style="font-size: 24px; color: #28a745;">+{diff:.0f}pp</div>
            </div>
            """, unsafe_allow_html=True)
        elif diff > 2:
            st.markdown(f"""
            <div style="background: #ffc10733; border: 3px solid #ffc107; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 40px;">🤔</div>
                <div style="font-size: 22px; font-weight: bold; color: #ffc107;">CONSIDERAR</div>
                <div style="font-size: 14px;">{melhor['nome']} +{diff:.0f}pp</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #17a2b833; border: 3px solid #17a2b8; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 40px;">✅</div>
                <div style="font-size: 22px; font-weight: bold; color: #17a2b8;">MANTER</div>
                <div style="font-size: 16px;">{gr_atual_nome}</div>
                <div style="font-size: 12px; color: #666;">Dif. mínima ({diff:.0f}pp)</div>
            </div>
            """, unsafe_allow_html=True)
    
    # RECOMENDAÇÕES TÁTICAS
    st.divider()
    
    # RECOMENDAÇÕES TÁTICAS
    # RECOMENDAÇÕES TÁTICAS
    st.divider()
    st.markdown("### 📋 INSTRUÇÕES TÁTICAS")
    
    recomendacoes = gerar_recomendacoes_posicionamento(
        zona_adv_forte_idx, zona_gr_fraca_idx, minuto, diferenca, gr_atual_data['probs'], adv_info
    )
    
    for rec in recomendacoes:
        cor_map = {
            'critica': ('#dc354533', '#dc3545', '#fff'), 
            'alta': ('#ffc10733', '#ffc107', '#000'), 
            'media': ('#17a2b833', '#17a2b8', '#fff'), 
            'baixa': ('#28a74533', '#28a745', '#fff')
        }
        cor_bg, cor_borda, cor_texto = cor_map.get(rec['prioridade'], ('#17a2b833', '#17a2b8', '#fff'))
        
        st.markdown(f"""
        <div style="background: {cor_bg}; border-left: 6px solid {cor_borda}; 
                    padding: 16px 20px; border-radius: 0 12px 12px 0; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-size: 32px;">{rec['icon']}</span>
                <div>
                    <div style="font-size: 18px; font-weight: bold; color: {cor_borda};">{rec['titulo']}</div>
                    <div style="font-size: 14px; color: #888; margin-top: 4px;">{rec['descricao']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# TAB 2: PENALTY
# =============================================================================
with tab_penalty:
    st.markdown("### 🎯 Quem deve defender o PENALTY?")
    
    # Velocidade do penalty
    col_info, col_vel = st.columns([2, 1])
    with col_info:
        st.caption(f"Adversário: **{adv_nome}** | Vel. média: {adv_info['velocidade_media_remate_kmh']} km/h")
    with col_vel:
        vel_penalty = st.slider("Vel. Penalty", 80, 120, int(adv_info['velocidade_media_remate_kmh']), key="vel_pen")
    
    st.markdown("")
    
    # Calcular ranking para penalties (dist=7m)
    ranking_pen = []
    for _, gr in grs.iterrows():
        grid, media, probs = calcular_probs_gr(gr, predictor, 7.0, vel_penalty, minuto, diferenca)
        ranking_pen.append({
            'nome': gr['nome'], 'altura': gr['altura_cm'],
            'grid': grid, 'media': media, 'probs': probs
        })
    
    ranking_pen = sorted(ranking_pen, key=lambda x: x['media'], reverse=True)
    
    # Semáforo
    cols = st.columns(3)
    for i, r in enumerate(ranking_pen):
        with cols[i]:
            taxa = r['media']
            is_atual = r['nome'] == gr_atual_nome
            is_melhor = i == 0
            
            if taxa >= 55:
                cor, icon = "#28a745", "✅"
            elif taxa >= 45:
                cor, icon = "#ffc107", "➡️"
            else:
                cor, icon = "#dc3545", "⚠️"
            
            # Definir badge
            if is_atual and is_melhor:
                borda = "4px solid gold"
                badge = "⭐ EM CAMPO + RECOMENDADO"
            elif is_atual:
                borda = "4px solid #17a2b8"
                badge = "🔵 EM CAMPO"
            elif is_melhor:
                borda = "4px solid gold"
                badge = "⭐ RECOMENDADO"
            else:
                borda = f"2px solid {cor}"
                badge = ""
            
            st.markdown(f"""
            <div style="background: {cor}22; border: {borda}; border-radius: 12px; 
                        padding: 20px 15px; text-align: center; min-height: 180px;
                        display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 28px; margin-bottom: 5px;">{icon}</div>
                <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">{r['nome']}</div>
                <div style="font-size: 42px; font-weight: bold; color: {cor}; line-height: 1;">{taxa:.0f}%</div>
                <div style="font-size: 11px; color: #888; margin-top: 8px;">7 metros | {r['altura']}cm</div>
                <div style="font-size: 11px; color: gold; min-height: 16px; margin-top: 4px;">{badge}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Decisão rápida
    melhor_pen = ranking_pen[0]
    atual_pen = next(r for r in ranking_pen if r['nome'] == gr_atual_nome)
    diff_pen = melhor_pen['media'] - atual_pen['media']
    
    if melhor_pen['nome'] == gr_atual_nome:
        st.success(f"✅ **MANTER {gr_atual_nome}** para o penalty - é o melhor!")
    elif diff_pen > 5:
        st.error(f"🔄 **TROCAR para {melhor_pen['nome']}** (+{diff_pen:.0f}pp)")
    elif diff_pen > 2:
        st.warning(f"🤔 **Considerar {melhor_pen['nome']}** (+{diff_pen:.0f}pp)")
    else:
        st.info(f"✅ **MANTER {gr_atual_nome}** - diferença mínima ({diff_pen:.0f}pp)")
    
    st.divider()
    
    # Heatmaps - UM POR LINHA (maiores)
    st.markdown("### 🗺️ Comparação por Zona (7m)")
    
    for i, r in enumerate(ranking_pen):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = heatmap_baliza(r['grid'], "", 320)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown(f"""
            <div style="padding: 20px; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 24px; font-weight: bold; margin-bottom: 10px;">{r['nome']}</div>
                <div style="font-size: 48px; font-weight: bold; color: {'#28a745' if r['media'] >= 50 else '#ffc107' if r['media'] >= 40 else '#dc3545'};">{r['media']:.0f}%</div>
                <div style="font-size: 14px; color: #888; margin-top: 10px;">Média de defesa a 7m</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">Altura: {r['altura']}cm</div>
            </div>
            """, unsafe_allow_html=True)
        
        if i < len(ranking_pen) - 1:
            st.divider()
# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("⏱️ Timeout ABC Braga | H2O.ai AutoML | Decisão em 90s")