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
def heatmap_baliza(grid, titulo="", height=400, destacar_fracas=None):
    """Heatmap com baliza realista e opção de destacar zonas fracas"""
    grid_plot = np.flipud(grid)
    
    fig = go.Figure()
    
    # Heatmap
    fig.add_trace(go.Heatmap(
        z=grid_plot, x=[0, 1, 2], y=[0, 1, 2],
        colorscale='RdYlGn', zmin=0, zmax=100,
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
            'icon': '🚨', 'titulo': f'RISCO MÁXIMO - {zonas_nome[zona_adv_forte]}',
            'descricao': f'Adversário remata {zonas_nome[zona_adv_forte].upper()} (zona mais fraca). Antecipar sempre para este lado!',
            'prioridade': 'critica'
        })
    
    # =================================================================
    # 2. POSIÇÃO LATERAL (baseada no padrão do adversário)
    # =================================================================
    zonas_esq = [0, 3, 6]
    zonas_dir = [2, 5, 8]
    zonas_centro = [1, 4, 7]
    
    if zona_adv_forte in zonas_esq:
        recomendacoes.append({
            'icon': '⬅️', 'titulo': 'Descair 20-30cm para ESQUERDA',
            'descricao': 'Adversário prefere lado esquerdo. Ganhar ângulo desse lado, forçar remate à direita.',
            'prioridade': 'alta'
        })
    elif zona_adv_forte in zonas_dir:
        recomendacoes.append({
            'icon': '➡️', 'titulo': 'Descair 20-30cm para DIREITA',
            'descricao': 'Adversário prefere lado direito. Ganhar ângulo desse lado, forçar remate à esquerda.',
            'prioridade': 'alta'
        })
    else:
        recomendacoes.append({
            'icon': '⚖️', 'titulo': 'Posição CENTRAL equilibrada',
            'descricao': 'Adversário remata ao centro. Manter 50/50 nos lados, não descair prematuramente.',
            'prioridade': 'media'
        })
    
    # =================================================================
    # 3. POSIÇÃO VERTICAL (baseada na altura do ataque + velocidade)
    # =================================================================
    vel_adv = adv_info['velocidade_media_remate_kmh']
    
    if zona_adv_forte in [0, 1, 2]:
        # Ataca alto
        if vel_adv >= 95:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'RECUAR 30-40cm na baliza',
                'descricao': f'Remates altos e rápidos ({vel_adv:.0f}km/h). Ganhar tempo de reação. Braços sempre acima dos ombros.',
                'prioridade': 'alta'
            })
        else:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'Posição base NEUTRA',
                'descricao': f'Remates altos mas controláveis ({vel_adv:.0f}km/h). Manter posição base, preparar salto.',
                'prioridade': 'media'
            })
    elif zona_adv_forte in [6, 7, 8]:
        # Ataca baixo
        recomendacoes.append({
            'icon': '📍', 'titulo': 'AVANÇAR 30-40cm + baixar corpo',
            'descricao': 'Remates baixos. Ganhar ângulo inferior, fechar espaço entre pernas. Centro gravidade baixo.',
            'prioridade': 'alta'
        })
        recomendacoes.append({
            'icon': '🦵', 'titulo': 'Joelhos fletidos, peso nos pés',
            'descricao': 'Pronto para mergulho lateral. NUNCA cruzar pernas. Atacar a bola, não esperar.',
            'prioridade': 'alta'
        })
    else:
        # Ataca meio
        if vel_adv >= 95:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'RECUAR 15-20cm',
                'descricao': f'Remates fortes à meia-altura ({vel_adv:.0f}km/h). Dar margem para reação lateral.',
                'prioridade': 'media'
            })
        else:
            recomendacoes.append({
                'icon': '📍', 'titulo': 'Posição BASE equilibrada',
                'descricao': 'Velocidade normal. Posição base standard, pronto para qualquer direção.',
                'prioridade': 'media'
            })
    
    # =================================================================
    # 4. COMPENSAR ZONA FRACA DO GR
    # =================================================================
    prob_min = min(probs_gr)
    if prob_min < 45:
        lado_fraco = "esquerdo" if zona_gr_fraca in zonas_esq else "direito" if zona_gr_fraca in zonas_dir else "central"
        altura_fraca = "alto" if zona_gr_fraca in [0, 1, 2] else "baixo" if zona_gr_fraca in [6, 7, 8] else "meia-altura"
        
        recomendacoes.append({
            'icon': '🎯', 'titulo': f'PRÉ-POSICIONAR lado {lado_fraco.upper()}',
            'descricao': f'Zona fraca ({prob_min:.0f}%): {altura_fraca} {lado_fraco}. Antecipar 0.2s antes, ganhar meio passo.',
            'prioridade': 'media'
        })
    
    # =================================================================
    # 5. CONTEXTO: RESULTADO + MINUTO
    # =================================================================
    if diferenca <= -3:
        recomendacoes.append({
            'icon': '⚡', 'titulo': 'A PERDER - SER AGRESSIVO',
            'descricao': 'Posição 40-50cm avançada. Provocar erros. Sair para interceptar passes. Arriscar.',
            'prioridade': 'alta'
        })
    elif diferenca < 0:
        if minuto >= 50:
            recomendacoes.append({
                'icon': '⚡', 'titulo': 'Fim do jogo A PERDER - ASSUMIR RISCOS',
                'descricao': 'Últimos minutos. Posição muito avançada. Forçar turnovers. Jogar psicológico.',
                'prioridade': 'alta'
            })
        else:
            recomendacoes.append({
                'icon': '💪', 'titulo': 'A PERDER no meio do jogo - SER PROATIVO',
                'descricao': 'Ainda há tempo. Posição 20-30cm avançada. Mostrar confiança, pressionar adversário.',
                'prioridade': 'media'
            })
    elif diferenca >= 3:
        recomendacoes.append({
            'icon': '🛡️', 'titulo': 'A GANHAR confortável (+3) - GERIR VANTAGEM',
            'descricao': 'Posição conservadora. Não arriscar saídas. Cobrir bem os ângulos. Segurança máxima.',
            'prioridade': 'media'
        })
    elif diferenca > 0:
        if minuto >= 50:
            recomendacoes.append({
                'icon': '🛡️', 'titulo': 'Fim do jogo A GANHAR - PROTEGER RESULTADO',
                'descricao': 'Últimos minutos com vantagem. Posição base sólida. Zero riscos. Defender ângulos.',
                'prioridade': 'alta'
            })
        else:
            recomendacoes.append({
                'icon': '✅', 'titulo': 'A GANHAR - MANTER intensidade defensiva',
                'descricao': 'Meio do jogo com vantagem. Posição equilibrada. Não relaxar. Antecipar padrões adversários.',
                'prioridade': 'baixa'
            })
    else:
        if minuto >= 50:
            recomendacoes.append({
                'icon': '⚖️', 'titulo': 'Fim EMPATADO - CONCENTRAÇÃO MÁXIMA',
                'descricao': 'Minutos finais empatados. Uma defesa decide. Posição base perfeita. Zero erros.',
                'prioridade': 'alta'
            })
        elif minuto <= 15:
            recomendacoes.append({
                'icon': '🟢', 'titulo': 'Início EMPATADO - IMPOR presença',
                'descricao': 'Início de jogo. Mostrar confiança. Ocupar espaço. Comunicar alto com defesa.',
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
# TABS: JOGO NORMAL vs pênalti
# =============================================================================
tab_jogo, tab_penalty = st.tabs(["⚽ Jogo Normal", "🎯 Pênalti (7m)"])

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
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

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
                <div style="font-size: 24px; color: #28a745;">+{diff:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)
        elif diff > 2:
            st.markdown(f"""
            <div style="background: #ffc10733; border: 3px solid #ffc107; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 40px;">🤔</div>
                <div style="font-size: 22px; font-weight: bold; color: #ffc107;">CONSIDERAR</div>
                <div style="font-size: 14px;">{melhor['nome']} +{diff:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #17a2b833; border: 3px solid #17a2b8; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 40px;">✅</div>
                <div style="font-size: 22px; font-weight: bold; color: #17a2b8;">MANTER</div>
                <div style="font-size: 16px;">{gr_atual_nome}</div>
                <div style="font-size: 12px; color: #666;">Dif. mínima ({diff:.0f}%)</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Pontos forte/fraco (abaixo da decisão)
        st.markdown("<br>", unsafe_allow_html=True)
        zonas_nome = ['Sup.Esq', 'Sup.Centro', 'Sup.Dir', 'Meio.Esq', 'Meio.Centro', 'Meio.Dir', 'Inf.Esq', 'Inf.Centro', 'Inf.Dir']
        probs_flat = gr_atual_data['probs']
        
        st.markdown(f"""
        <div style="background: #28a74522; border-left: 4px solid #28a745; 
                    padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <div style="font-size: 14px; font-weight: bold; color: #28a745;">
                ✅ Forte: {zonas_nome[np.argmax(probs_flat)]} ({max(probs_flat):.0f}%)
            </div>
        </div>
        <div style="background: #dc354522; border-left: 4px solid #dc3545; 
                    padding: 12px; border-radius: 8px;">
            <div style="font-size: 14px; font-weight: bold; color: #dc3545;">
                ⚠️ Fraca: {zonas_nome[np.argmin(probs_flat)]} ({min(probs_flat):.0f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # RECOMENDAÇÕES TÁTICAS (sem dividers)
    st.markdown("<br>", unsafe_allow_html=True)
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
        
        # Dividir descrição em bullet points
        descricao_linhas = rec['descricao'].split('. ')
        descricao_html = ''.join([f"<li style='margin-bottom: 4px;'>{linha.strip()}{'.' if not linha.endswith('.') else ''}</li>" 
                                   for linha in descricao_linhas if linha.strip()])
        
        st.markdown(f"""
        <div style="background: {cor_bg}; border-left: 6px solid {cor_borda}; 
                    padding: 16px 20px; border-radius: 0 12px 12px 0; margin-bottom: 12px;">
            <div style="display: flex; align-items: flex-start; gap: 15px;">
                <span style="font-size: 32px; margin-top: 4px;">{rec['icon']}</span>
                <div style="flex: 1;">
                    <div style="font-size: 18px; font-weight: bold; color: {cor_borda}; margin-bottom: 8px;">
                        {rec['titulo']}
                    </div>
                    <ul style="font-size: 14px; color: #333; margin: 0; padding-left: 20px; list-style-type: disc;">
                        {descricao_html}
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# TAB 2: PENALTY
# =============================================================================
with tab_penalty:
    st.markdown("### 🎯 Quem deve defender o Pênalti?")
    
    # Velocidade do penalty
    col_info, col_vel = st.columns([2, 1])
    with col_info:
        st.caption(f"Adversário: **{adv_nome}** | Vel. média: {adv_info['velocidade_media_remate_kmh']} km/h")
    with col_vel:
        vel_penalty = st.slider("Vel. Pênalti", 80, 120, int(adv_info['velocidade_media_remate_kmh']), key="vel_pen")
    
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
    
    # SEMÁFORO - CARDS EM CIMA (MESMO TAMANHO)
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
            
            if is_atual and is_melhor:
                borda, badge = "4px solid gold", "⭐ EM CAMPO + RECOMENDADO"
            elif is_atual:
                borda, badge = "4px solid #17a2b8", "🔵 EM CAMPO"
            elif is_melhor:
                borda, badge = "4px solid gold", "⭐ RECOMENDADO"
            else:
                borda, badge = f"2px solid {cor}", ""
            
            st.markdown(f"""
            <div style="background: {cor}22; border: {borda}; border-radius: 12px; 
                        padding: 20px 15px; text-align: center; min-height: 180px; 
                        display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 28px; margin-bottom: 5px;">{icon}</div>
                <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">{r['nome']}</div>
                <div style="font-size: 42px; font-weight: bold; color: {cor}; line-height: 1;">{taxa:.0f}%</div>
                <div style="font-size: 11px; color: #888; margin-top: 8px;">7 metros | {r['altura']}cm</div>
                <div style="font-size: 11px; color: gold; min-height: 16px; margin-top: 4px;">{badge if badge else ""}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Decisão rápida
    melhor_pen = ranking_pen[0]
    atual_pen = next(r for r in ranking_pen if r['nome'] == gr_atual_nome)
    diff_pen = melhor_pen['media'] - atual_pen['media']
    
    if melhor_pen['nome'] == gr_atual_nome:
        st.success(f"✅ **MANTER {gr_atual_nome}** para o Pênalti é a melhor opção!")
    elif diff_pen > 5:
        st.error(f"🔄 **TROCAR para {melhor_pen['nome']}** (+{diff_pen:.0f}%)")
    elif diff_pen > 2:
        st.warning(f"🤔 **Considerar {melhor_pen['nome']}** (+{diff_pen:.0f}%)")
    else:
        st.info(f"✅ **MANTER {gr_atual_nome}** - diferença mínima ({diff_pen:.0f}%)")
    
    st.divider()
    
    # HEATMAPS - 3 LADO A LADO (grandes)
st.markdown("### 🗺️ Comparação por Zona (7 metros)")
cols_heat = st.columns(3)

for i, r in enumerate(ranking_pen):
    with cols_heat[i]:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: -50px;">
            <span style="font-size: 1.5rem; font-weight: 700; color: #333;">
                {r['nome']}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        fig = heatmap_baliza(r['grid'], "", 700)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
 