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
    """grid[0]=Superior, grid[1]=Meio, grid[2]=Inferior"""
    grid_plot = np.flipud(grid)
    
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=grid_plot,
        x=['Esq', 'Centro', 'Dir'],
        y=['Inf', 'Meio', 'Sup'],
        colorscale='RdYlGn',
        zmin=0, zmax=100,
        text=np.round(grid_plot, 0),
        texttemplate='%{text}%',
        textfont=dict(size=16, color='black', family='Arial Black'),
        showscale=False
    ))
    
    # Postes
    fig.add_shape(type='rect', x0=-0.55, x1=-0.45, y0=-0.5, y1=2.5,
                  fillcolor='#C41E3A', line=dict(width=0))
    fig.add_shape(type='rect', x0=2.45, x1=2.55, y0=-0.5, y1=2.5,
                  fillcolor='white', line=dict(color='#ccc', width=1))
    fig.add_shape(type='rect', x0=-0.55, x1=2.55, y0=2.45, y1=2.55,
                  fillcolor='white', line=dict(color='#ccc', width=1))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)),
        height=height,
        xaxis=dict(constrain='domain', showgrid=False),
        yaxis=dict(scaleanchor='x', showgrid=False),
        margin=dict(l=10, r=10, t=40, b=10)
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
# GERAR RECOMENDAÇÕES TÁTICAS DE POSICIONAMENTO
# =============================================================================
def gerar_recomendacoes_posicionamento(zona_adv_forte, zona_gr_fraca, minuto, diferenca, probs_gr):
    """
    Gera recomendações táticas específicas de posicionamento
    
    zona_adv_forte: índice 0-8 da zona mais atacada pelo adversário
    zona_gr_fraca: índice 0-8 da zona mais fraca do GR
    minuto: minuto do jogo (0-60)
    diferenca: diferença de golos (positivo = a ganhar)
    probs_gr: lista de 9 probabilidades do GR
    """
    
    recomendacoes = []
    
    # Mapeamento de zonas
    # 0=Sup.Esq, 1=Sup.Centro, 2=Sup.Dir
    # 3=Meio.Esq, 4=Meio.Centro, 5=Meio.Dir
    # 6=Inf.Esq, 7=Inf.Centro, 8=Inf.Dir
    
    zonas_nome = {
        0: "Superior Esquerda", 1: "Superior Centro", 2: "Superior Direita",
        3: "Meio Esquerda", 4: "Meio Centro", 5: "Meio Direita",
        6: "Inferior Esquerda", 7: "Inferior Centro", 8: "Inferior Direita"
    }
    
    # =========================================================================
    # 1. POSIÇÃO BASE (baseada na zona preferida do adversário)
    # =========================================================================
    
    # Adversário prefere zonas ALTAS (0, 1, 2)
    if zona_adv_forte in [0, 1, 2]:
        recomendacoes.append({
            'tipo': 'POSIÇÃO',
            'icon': '📍',
            'titulo': 'Posição mais RECUADA',
            'descricao': 'Adversário ataca zonas altas - ficar 20-30cm mais atrás para ter tempo de reação',
            'prioridade': 'alta'
        })
        
        if zona_adv_forte == 0:  # Sup Esquerda
            recomendacoes.append({
                'tipo': 'LATERAL',
                'icon': '↖️',
                'titulo': 'Descair para ESQUERDA',
                'descricao': 'Zona preferida: Superior Esquerda - posicionar ligeiramente à esquerda do centro',
                'prioridade': 'alta'
            })
        elif zona_adv_forte == 2:  # Sup Direita
            recomendacoes.append({
                'tipo': 'LATERAL',
                'icon': '↗️',
                'titulo': 'Descair para DIREITA',
                'descricao': 'Zona preferida: Superior Direita - posicionar ligeiramente à direita do centro',
                'prioridade': 'alta'
            })
        else:  # Sup Centro
            recomendacoes.append({
                'tipo': 'LATERAL',
                'icon': '⬆️',
                'titulo': 'Manter CENTRO',
                'descricao': 'Zona preferida: Superior Centro - manter posição central, braços altos',
                'prioridade': 'media'
            })
    
    # Adversário prefere zonas MÉDIAS (3, 4, 5)
    elif zona_adv_forte in [3, 4, 5]:
        recomendacoes.append({
            'tipo': 'POSIÇÃO',
            'icon': '📍',
            'titulo': 'Posição NEUTRA',
            'descricao': 'Adversário ataca zonas médias - manter posição base a 1m da linha',
            'prioridade': 'media'
        })
        
        if zona_adv_forte == 3:  # Meio Esquerda
            recomendacoes.append({
                'tipo': 'LATERAL',
                'icon': '⬅️',
                'titulo': 'Braço ESQUERDO ativo',
                'descricao': 'Zona preferida: Meio Esquerda - manter braço esquerdo preparado',
                'prioridade': 'alta'
            })
        elif zona_adv_forte == 5:  # Meio Direita
            recomendacoes.append({
                'tipo': 'LATERAL',
                'icon': '➡️',
                'titulo': 'Braço DIREITO ativo',
                'descricao': 'Zona preferida: Meio Direita - manter braço direito preparado',
                'prioridade': 'alta'
            })
    
    # Adversário prefere zonas BAIXAS (6, 7, 8)
    else:
        recomendacoes.append({
            'tipo': 'POSIÇÃO',
            'icon': '📍',
            'titulo': 'Posição mais AVANÇADA',
            'descricao': 'Adversário ataca zonas baixas - avançar 30-40cm para reduzir ângulo',
            'prioridade': 'alta'
        })
        
        recomendacoes.append({
            'tipo': 'CORPO',
            'icon': '🦵',
            'titulo': 'Baixar centro de gravidade',
            'descricao': 'Flexionar mais os joelhos - pernas prontas para defesas rasteiras',
            'prioridade': 'alta'
        })
        
        if zona_adv_forte == 6:  # Inf Esquerda
            recomendacoes.append({
                'tipo': 'LATERAL',
                'icon': '↙️',
                'titulo': 'Encostar ao POSTE ESQUERDO',
                'descricao': 'Remates cruzados para inferior esquerda - aproximar do poste',
                'prioridade': 'media'
            })
        elif zona_adv_forte == 8:  # Inf Direita
            recomendacoes.append({
                'tipo': 'LATERAL',
                'icon': '↘️',
                'titulo': 'Encostar ao POSTE DIREITO',
                'descricao': 'Remates cruzados para inferior direita - aproximar do poste',
                'prioridade': 'media'
            })
    
    # =========================================================================
    # 2. AJUSTES BASEADOS NO MINUTO DO JOGO
    # =========================================================================
    
    if minuto <= 15:
        recomendacoes.append({
            'tipo': 'TEMPO',
            'icon': '🟢',
            'titulo': 'Início de jogo - SER AGRESSIVO',
            'descricao': 'Momento para assumir riscos - posição mais avançada, pressionar o rematador',
            'prioridade': 'media'
        })
    elif minuto >= 50:
        recomendacoes.append({
            'tipo': 'TEMPO',
            'icon': '🔴',
            'titulo': 'Final de jogo - SER CONSERVADOR',
            'descricao': 'Momento crítico - não arriscar, cobrir bem a baliza, evitar erros',
            'prioridade': 'alta'
        })
    elif minuto >= 25 and minuto <= 35:
        recomendacoes.append({
            'tipo': 'TEMPO',
            'icon': '🟡',
            'titulo': 'Meio do jogo - MANTER FOCO',
            'descricao': 'Período de transição - manter concentração, não relaxar',
            'prioridade': 'media'
        })
    
    # =========================================================================
    # 3. AJUSTES BASEADOS NA DIFERENÇA DE GOLOS
    # =========================================================================
    
    if diferenca <= -3:
        recomendacoes.append({
            'tipo': 'RESULTADO',
            'icon': '⚡',
            'titulo': 'A PERDER por muito - ARRISCAR',
            'descricao': 'Nada a perder - posição muito avançada, tentar provocar erros do adversário',
            'prioridade': 'alta'
        })
    elif diferenca < 0:
        recomendacoes.append({
            'tipo': 'RESULTADO',
            'icon': '💪',
            'titulo': 'A PERDER - Aumentar agressividade',
            'descricao': 'Precisas de defesas - ser mais agressivo no posicionamento',
            'prioridade': 'media'
        })
    elif diferenca >= 3:
        recomendacoes.append({
            'tipo': 'RESULTADO',
            'icon': '🛡️',
            'titulo': 'A GANHAR por muito - GERIR',
            'descricao': 'Confortável - não arriscar, manter posição segura, evitar surpresas',
            'prioridade': 'media'
        })
    elif diferenca > 0:
        recomendacoes.append({
            'tipo': 'RESULTADO',
            'icon': '✅',
            'titulo': 'A GANHAR - Manter solidez',
            'descricao': 'Situação favorável - continuar a fazer o que está a funcionar',
            'prioridade': 'baixa'
        })
    
    # =========================================================================
    # 4. ALERTA SE ZONA FRACA DO GR = ZONA FORTE DO ADVERSÁRIO
    # =========================================================================
    
    if zona_adv_forte == zona_gr_fraca:
        recomendacoes.insert(0, {
            'tipo': 'ALERTA',
            'icon': '🚨',
            'titulo': f'RISCO CRÍTICO - {zonas_nome[zona_adv_forte]}',
            'descricao': f'A tua zona mais fraca é onde o adversário mais ataca! Reforçar posicionamento nesta zona.',
            'prioridade': 'critica'
        })
    
    # =========================================================================
    # 5. RECOMENDAÇÃO ESPECIAL BASEADA NA PROB MAIS BAIXA
    # =========================================================================
    
    prob_min = min(probs_gr)
    if prob_min < 45:
        recomendacoes.append({
            'tipo': 'TREINO',
            'icon': '📝',
            'titulo': f'Zona a trabalhar: {zonas_nome[zona_gr_fraca]}',
            'descricao': f'Probabilidade de apenas {prob_min:.0f}% - compensar com posicionamento preventivo',
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
# SIDEBAR - CONTEXTO RÁPIDO
# =============================================================================
with st.sidebar:
    st.markdown("## ⚡ CONTEXTO")
    
    # Adversário
    query = "SELECT id, nome FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        advs = pd.read_sql_query(query, conn)
    
    adv_nome = st.selectbox("Adversário", advs['nome'].tolist())
    adv_id = int(advs[advs['nome'] == adv_nome]['id'].values[0])
    
    # Info adversário
    query = "SELECT * FROM adversarios WHERE id = ?"
    with db.get_connection() as conn:
        adv_info = pd.read_sql_query(query, conn, params=(adv_id,)).iloc[0]
    
    st.divider()
    
    # GR atual
    query = "SELECT * FROM guarda_redes"
    with db.get_connection() as conn:
        grs = pd.read_sql_query(query, conn)
    
    gr_atual_nome = st.selectbox("GR em Campo", grs['nome'].tolist())
    gr_atual = grs[grs['nome'] == gr_atual_nome].iloc[0]
    
    st.divider()
    
    # Situação
    minuto = st.slider("Minuto", 0, 60, 42)
    
    col1, col2 = st.columns(2)
    with col1:
        golo_abc = st.number_input("ABC", 0, 50, 24)
    with col2:
        golo_adv = st.number_input("ADV", 0, 50, 24)
    
    diferenca = golo_abc - golo_adv
    
    st.divider()
    
    # Parâmetros remate
    dist = st.slider("Distância", 6.0, 12.0, 9.0, 0.5)
    vel = st.slider("Velocidade", 70, 120, int(adv_info['velocidade_media_remate_kmh']))

# =============================================================================
# DISTRIBUIÇÃO ADVERSÁRIO
# =============================================================================
def get_dist_adversario(adv):
    alta = adv['remates_zona_alta_perc']
    media = adv['remates_zona_media_perc']
    baixa = adv['remates_zona_baixa_perc']
    
    grid = np.array([
        [alta * 0.28, alta * 0.44, alta * 0.28],
        [media * 0.35, media * 0.30, media * 0.35],
        [baixa * 0.30, baixa * 0.40, baixa * 0.30]
    ])
    return grid

dist_adv = get_dist_adversario(adv_info)
zona_adv_forte_idx = np.argmax(dist_adv.flatten())

# =============================================================================
# CALCULAR RANKING DOS 3 GRs
# =============================================================================
ranking = []
for _, gr in grs.iterrows():
    grid, media, probs = calcular_probs_gr(gr, predictor, dist, vel, minuto, diferenca)
    ranking.append({
        'id': gr['id'],
        'nome': gr['nome'],
        'altura': gr['altura_cm'],
        'envergadura': gr['envergadura_cm'],
        'grid': grid,
        'media': media,
        'probs': probs
    })

ranking = sorted(ranking, key=lambda x: x['media'], reverse=True)
gr_atual_data = next(r for r in ranking if r['nome'] == gr_atual_nome)
melhor = ranking[0]

# Zona fraca do GR atual
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
# LINHA 1: SEMÁFORO DOS 3 GRs
# =============================================================================
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
                    padding: 15px; text-align: center; height: 160px;">
            <div style="font-size: 28px;">{icon}</div>
            <div style="font-size: 18px; font-weight: bold;">{r['nome']}</div>
            <div style="font-size: 38px; font-weight: bold; color: {cor};">{taxa:.0f}%</div>
            <div style="font-size: 10px; color: #888;">{r['altura']}cm | {r['envergadura']}cm</div>
            {f"<div style='font-size: 10px; color: gold;'>{badge}</div>" if badge else ""}
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# =============================================================================
# LINHA 2: HEATMAP + DECISÃO
# =============================================================================
col_heat, col_decisao = st.columns([2, 1])

with col_heat:
    st.markdown(f"### 🗺️ {gr_atual_nome} - Prob. Defesa")
    fig = heatmap_baliza(gr_atual_data['grid'], f"Min {minuto} | {dist}m | {vel}km/h", 280)
    st.plotly_chart(fig, use_container_width=True)
    
    zonas_nome = ['Sup.Esq', 'Sup.Centro', 'Sup.Dir', 
                  'Meio.Esq', 'Meio.Centro', 'Meio.Dir',
                  'Inf.Esq', 'Inf.Centro', 'Inf.Dir']
    
    probs_flat = gr_atual_data['probs']
    col1, col2 = st.columns(2)
    col1.success(f"✅ Forte: {zonas_nome[np.argmax(probs_flat)]} ({max(probs_flat):.0f}%)")
    col2.error(f"⚠️ Fraca: {zonas_nome[np.argmin(probs_flat)]} ({min(probs_flat):.0f}%)")

with col_decisao:
    st.markdown("### 💡 DECISÃO")
    
    diff = melhor['media'] - gr_atual_data['media']
    
    if melhor['nome'] == gr_atual_nome:
        st.markdown(f"""
        <div style="background: #28a74533; border: 3px solid #28a745; 
                    border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 40px;">✅</div>
            <div style="font-size: 22px; font-weight: bold; color: #28a745;">MANTER</div>
            <div style="font-size: 16px; margin-top: 5px;">{gr_atual_nome}</div>
            <div style="font-size: 12px; color: #666; margin-top: 5px;">Melhor opção</div>
        </div>
        """, unsafe_allow_html=True)
    elif diff > 5:
        st.markdown(f"""
        <div style="background: #dc354533; border: 3px solid #dc3545; 
                    border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 40px;">🔄</div>
            <div style="font-size: 22px; font-weight: bold; color: #dc3545;">TROCAR</div>
            <div style="font-size: 14px; margin-top: 5px;">{gr_atual_nome} → <b>{melhor['nome']}</b></div>
            <div style="font-size: 24px; color: #28a745; margin-top: 5px;">+{diff:.0f}pp</div>
        </div>
        """, unsafe_allow_html=True)
    elif diff > 2:
        st.markdown(f"""
        <div style="background: #ffc10733; border: 3px solid #ffc107; 
                    border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 40px;">🤔</div>
            <div style="font-size: 22px; font-weight: bold; color: #ffc107;">CONSIDERAR</div>
            <div style="font-size: 14px; margin-top: 5px;">{melhor['nome']} +{diff:.0f}pp</div>
            <div style="font-size: 12px; color: #666; margin-top: 5px;">Avaliar fatores</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #17a2b833; border: 3px solid #17a2b8; 
                    border-radius: 12px; padding: 20px; text-align: center;">
            <div style="font-size: 40px;">✅</div>
            <div style="font-size: 22px; font-weight: bold; color: #17a2b8;">MANTER</div>
            <div style="font-size: 16px; margin-top: 5px;">{gr_atual_nome}</div>
            <div style="font-size: 12px; color: #666; margin-top: 5px;">Dif. mínima ({diff:.0f}pp)</div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# LINHA 3: RECOMENDAÇÕES TÁTICAS DE POSICIONAMENTO
# =============================================================================
st.divider()
st.markdown("### 📋 INSTRUÇÕES TÁTICAS PARA O GUARDA-REDES")

# Gerar recomendações
recomendacoes = gerar_recomendacoes_posicionamento(
    zona_adv_forte_idx, 
    zona_gr_fraca_idx, 
    minuto, 
    diferenca,
    gr_atual_data['probs']
)

# Mostrar recomendações em cards
cols_rec = st.columns(2)

for i, rec in enumerate(recomendacoes):
    col_idx = i % 2
    
    # Cor baseada na prioridade
    if rec['prioridade'] == 'critica':
        cor_bg = "#dc354522"
        cor_borda = "#dc3545"
    elif rec['prioridade'] == 'alta':
        cor_bg = "#ffc10722"
        cor_borda = "#ffc107"
    else:
        cor_bg = "#17a2b822"
        cor_borda = "#17a2b8"
    
    with cols_rec[col_idx]:
        st.markdown(f"""
        <div style="background: {cor_bg}; border-left: 4px solid {cor_borda}; 
                    padding: 12px 15px; border-radius: 0 8px 8px 0; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">{rec['icon']}</span>
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: {cor_borda};">{rec['titulo']}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 3px;">{rec['descricao']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

"""
Dashboard Penalties (7 metros) - Digital Twin ABC Braga
Análise específica para livres de 7 metros
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
st.set_page_config(page_title="Penalties - ABC Braga", page_icon="🎯", layout="wide")

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
def heatmap_baliza(grid, titulo="", height=350, escala_max=100):
    """grid[0]=Superior, grid[1]=Meio, grid[2]=Inferior"""
    grid_plot = np.flipud(grid)
    
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=grid_plot,
        x=['Esq', 'Centro', 'Dir'],
        y=['Inf', 'Meio', 'Sup'],
        colorscale='RdYlGn',
        zmin=0, zmax=escala_max,
        text=np.round(grid_plot, 0),
        texttemplate='%{text}%',
        textfont=dict(size=16, color='black', family='Arial Black'),
        showscale=False
    ))
    
    # Postes
    fig.add_shape(type='rect', x0=-0.55, x1=-0.45, y0=-0.5, y1=2.5,
                  fillcolor='#C41E3A', line=dict(width=0))
    fig.add_shape(type='rect', x0=2.45, x1=2.55, y0=-0.5, y1=2.5,
                  fillcolor='white', line=dict(color='#ccc', width=1))
    fig.add_shape(type='rect', x0=-0.55, x1=2.55, y0=2.45, y1=2.55,
                  fillcolor='white', line=dict(color='#ccc', width=1))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)),
        height=height,
        xaxis=dict(constrain='domain', showgrid=False),
        yaxis=dict(scaleanchor='x', showgrid=False),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

# =============================================================================
# CALCULAR PROBS H2O PARA PENALTIES (dist=7m)
# =============================================================================
def calcular_probs_penalty(gr, predictor, vel, minuto, dif):
    """Calcula probs para penalty (distância fixa = 7m)"""
    probs = []
    for zona in range(1, 10):
        try:
            p = predictor.predict(
                zona=zona, 
                distancia=7.0,  # SEMPRE 7m para penalty
                velocidade=vel,
                altura_gr=int(gr['altura_cm']),
                envergadura_gr=int(gr['envergadura_cm']),
                vel_lateral_gr=float(gr['velocidade_lateral_ms']),
                minuto=minuto, 
                diferenca_golos=dif
            )
            probs.append(p)
        except:
            probs.append(50.0)
    
    grid = np.array(probs).reshape(3, 3)
    media = np.mean(probs)
    return grid, media, probs

# =============================================================================
# VERIFICAR H2O
# =============================================================================
if not predictor:
    st.error("⚠️ Modelo H2O não disponível")
    st.stop()

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div style="background: linear-gradient(90deg, #8B0000, #DC143C); 
            padding: 20px 30px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
    <span style="font-size: 36px; font-weight: bold; color: white;">🎯 PENALTIES - 7 METROS</span>
    <p style="color: #ffcccc; margin: 5px 0 0 0;">Análise especializada para livres de 7 metros</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("## ⚙️ CONTEXTO")
    
    # Adversário
    query = "SELECT id, nome FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        advs = pd.read_sql_query(query, conn)
    
    adv_nome = st.selectbox("Adversário", advs['nome'].tolist())
    adv_id = int(advs[advs['nome'] == adv_nome]['id'].values[0])
    
    st.divider()
    
    # Contexto do jogo
    minuto = st.slider("Minuto", 0, 60, 30)
    diferenca = st.slider("Diferença Golos", -5, 5, 0)
    
    st.divider()
    
    # Velocidade típica de penalty
    vel_penalty = st.slider("Velocidade Esperada", 80, 120, 95, 
                            help="Penalties costumam ser 90-100 km/h")

# =============================================================================
# CARREGAR DADOS
# =============================================================================
# GRs
query = "SELECT * FROM guarda_redes"
with db.get_connection() as conn:
    grs = pd.read_sql_query(query, conn)

# Histórico de penalties por GR
query_hist = """
SELECT gr.nome,
       COUNT(*) as total,
       SUM(CASE WHEN l.resultado = 'Defesa' THEN 1 ELSE 0 END) as defesas,
       ROUND(AVG(CASE WHEN l.resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa
FROM lances l
JOIN jogos j ON l.jogo_id = j.id
JOIN guarda_redes gr ON j.guarda_redes_id = gr.id
WHERE l.tipo_remate = '7 metros'
GROUP BY gr.id
ORDER BY taxa DESC
"""
with db.get_connection() as conn:
    hist_grs = pd.read_sql_query(query_hist, conn)

# Histórico de penalties vs adversário selecionado
query_adv = """
SELECT gr.nome,
       COUNT(*) as total,
       SUM(CASE WHEN l.resultado = 'Defesa' THEN 1 ELSE 0 END) as defesas,
       ROUND(AVG(CASE WHEN l.resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa
FROM lances l
JOIN jogos j ON l.jogo_id = j.id
JOIN guarda_redes gr ON j.guarda_redes_id = gr.id
WHERE l.tipo_remate = '7 metros' AND j.adversario_id = ?
GROUP BY gr.id
ORDER BY taxa DESC
"""
with db.get_connection() as conn:
    hist_vs_adv = pd.read_sql_query(query_adv, conn, params=(adv_id,))

# Padrões de zona do adversário em penalties
query_zonas_adv = """
SELECT l.zona_baliza_id, l.zona_baliza_nome,
       COUNT(*) as total,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as perc
FROM lances l
JOIN jogos j ON l.jogo_id = j.id
WHERE l.tipo_remate = '7 metros' AND j.adversario_id = ?
GROUP BY l.zona_baliza_id
ORDER BY l.zona_baliza_id
"""
with db.get_connection() as conn:
    zonas_adv = pd.read_sql_query(query_zonas_adv, conn, params=(adv_id,))

# =============================================================================
# TABS
# =============================================================================
tab1, tab2 = st.tabs(["🥅 Qual GR para Penalties?", "🎯 Padrões do Adversário"])

# =============================================================================
# TAB 1: QUAL GR USAR
# =============================================================================
with tab1:
    st.markdown("### 🥅 Quem deve defender o penalty?")
    
    # Calcular ranking H2O
    ranking = []
    for _, gr in grs.iterrows():
        grid, media, probs = calcular_probs_penalty(gr, predictor, vel_penalty, minuto, diferenca)
        
        # Buscar histórico
        hist_row = hist_grs[hist_grs['nome'] == gr['nome']]
        hist_taxa = hist_row['taxa'].values[0] if len(hist_row) > 0 else None
        hist_total = hist_row['total'].values[0] if len(hist_row) > 0 else 0
        
        # Buscar histórico vs adversário
        hist_adv_row = hist_vs_adv[hist_vs_adv['nome'] == gr['nome']]
        hist_adv_taxa = hist_adv_row['taxa'].values[0] if len(hist_adv_row) > 0 else None
        hist_adv_total = hist_adv_row['total'].values[0] if len(hist_adv_row) > 0 else 0
        
        ranking.append({
            'nome': gr['nome'],
            'altura': gr['altura_cm'],
            'envergadura': gr['envergadura_cm'],
            'grid': grid,
            'media_h2o': media,
            'hist_taxa': hist_taxa,
            'hist_total': hist_total,
            'hist_adv_taxa': hist_adv_taxa,
            'hist_adv_total': hist_adv_total,
            'probs': probs
        })
    
    ranking = sorted(ranking, key=lambda x: x['media_h2o'], reverse=True)
    
    # Semáforo
    st.markdown("#### Predição H2O (contexto atual)")
    cols = st.columns(3)
    
    for i, r in enumerate(ranking):
        with cols[i]:
            taxa = r['media_h2o']
            
            if taxa >= 55:
                cor, icon = "#28a745", "✅"
            elif taxa >= 45:
                cor, icon = "#ffc107", "➡️"
            else:
                cor, icon = "#dc3545", "⚠️"
            
            borda = "4px solid gold" if i == 0 else f"2px solid {cor}"
            
            st.markdown(f"""
            <div style="background: {cor}22; border: {borda}; border-radius: 12px; 
                        padding: 15px; text-align: center;">
                <div style="font-size: 24px;">{icon}</div>
                <div style="font-size: 16px; font-weight: bold;">{r['nome']}</div>
                <div style="font-size: 32px; font-weight: bold; color: {cor};">{taxa:.0f}%</div>
                <div style="font-size: 10px; color: #888;">H2O | {r['altura']}cm</div>
                {"<div style='color: gold; font-size: 11px;'>⭐ RECOMENDADO</div>" if i==0 else ""}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Histórico Real
    st.markdown("#### 📊 Histórico Real em Penalties")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Geral (todos os jogos)**")
        for _, r in enumerate(ranking):
            if r['hist_taxa']:
                st.markdown(f"- **{r['nome']}**: {r['hist_taxa']:.0f}% ({r['hist_total']} penalties)")
            else:
                st.markdown(f"- **{r['nome']}**: Sem dados")
    
    with col2:
        st.markdown(f"**vs {adv_nome}**")
        if len(hist_vs_adv) > 0:
            for _, r in enumerate(ranking):
                if r['hist_adv_taxa']:
                    st.markdown(f"- **{r['nome']}**: {r['hist_adv_taxa']:.0f}% ({r['hist_adv_total']} penalties)")
                else:
                    st.markdown(f"- **{r['nome']}**: Sem dados vs este adversário")
        else:
            st.info(f"Sem histórico de penalties vs {adv_nome}")
    
    st.divider()
    
    # Heatmaps
    st.markdown("#### 🗺️ Probabilidade de Defesa por Zona (7m)")
    cols_h = st.columns(3)
    
    for i, r in enumerate(ranking):
        with cols_h[i]:
            st.markdown(f"**{r['nome']}** ({r['media_h2o']:.0f}%)")
            fig = heatmap_baliza(r['grid'], "", 250)
            st.plotly_chart(fig, use_container_width=True)
            
            # Zona forte/fraca
            zonas = ['Sup.E', 'Sup.C', 'Sup.D', 'Mei.E', 'Mei.C', 'Mei.D', 'Inf.E', 'Inf.C', 'Inf.D']
            st.caption(f"✅ Forte: {zonas[np.argmax(r['probs'])]} | ⚠️ Fraca: {zonas[np.argmin(r['probs'])]}")

# =============================================================================
# TAB 2: PADRÕES DO ADVERSÁRIO
# =============================================================================
with tab2:
    st.markdown(f"### 🎯 Como o **{adv_nome}** marca penalties?")
    
    if len(zonas_adv) > 0:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Criar grid de distribuição
            if len(zonas_adv) == 9:
                dist_grid = zonas_adv['perc'].values.reshape(3, 3)
            else:
                # Preencher zonas em falta com 0
                dist_grid = np.zeros((3, 3))
                for _, row in zonas_adv.iterrows():
                    idx = int(row['zona_baliza_id']) - 1
                    i, j = idx // 3, idx % 3
                    dist_grid[i, j] = row['perc']
            
            st.markdown("#### 📍 Onde costumam rematar?")
            fig = heatmap_baliza(dist_grid, f"Distribuição penalties - {adv_nome}", 350, escala_max=max(30, dist_grid.max()))
            st.plotly_chart(fig, use_container_width=True)
            
            # Zona mais atacada
            max_idx = np.argmax(dist_grid.flatten())
            zonas_nome = ['Superior Esq', 'Superior Centro', 'Superior Dir',
                          'Meio Esq', 'Meio Centro', 'Meio Dir',
                          'Inferior Esq', 'Inferior Centro', 'Inferior Dir']
            
            st.warning(f"⚠️ **Zona preferida**: {zonas_nome[max_idx]} ({dist_grid.flatten()[max_idx]:.0f}%)")
        
        with col2:
            st.markdown("#### 📋 Estatísticas")
            
            total_penalties = zonas_adv['total'].sum()
            st.metric("Total Penalties", total_penalties)
            
            st.markdown("**Top 3 Zonas:**")
            zonas_ord = zonas_adv.sort_values('perc', ascending=False).head(3)
            for _, z in zonas_ord.iterrows():
                st.markdown(f"- {z['zona_baliza_nome']}: **{z['perc']:.0f}%**")
            
            st.divider()
            
            # Recomendação
            st.markdown("#### 💡 Recomendação")
            
            # Melhor GR para a zona mais atacada
            zona_forte_adv = max_idx + 1  # 1-indexed
            
            melhor_para_zona = None
            melhor_prob = 0
            for r in ranking:
                prob_zona = r['probs'][max_idx]
                if prob_zona > melhor_prob:
                    melhor_prob = prob_zona
                    melhor_para_zona = r['nome']
            
            st.success(f"""
            **{melhor_para_zona}** é o melhor para defender contra {adv_nome}
            
            - Prob. na zona preferida deles: **{melhor_prob:.0f}%**
            - {adv_nome} ataca {zonas_nome[max_idx]} em **{dist_grid.flatten()[max_idx]:.0f}%** dos penalties
            """)
            
            # Instrução tática
            instrucoes_zona = {
                0: "Descair para esquerda, posição alta",
                1: "Manter centro, braços altos",
                2: "Descair para direita, posição alta",
                3: "Cobrir lado esquerdo, meia altura",
                4: "Centro da baliza, reagir rápido",
                5: "Cobrir lado direito, meia altura",
                6: "Baixar, cobrir inferior esquerdo",
                7: "Posição baixa, pernas prontas",
                8: "Baixar, cobrir inferior direito"
            }
            
            st.info(f"📍 **Posicionamento sugerido**: {instrucoes_zona[max_idx]}")
    
    else:
        st.warning(f"⚠️ Sem dados de penalties do {adv_nome}")
        
        st.markdown("#### 📊 Estatísticas Gerais de Penalties")
        
        # Mostrar distribuição geral
        query_geral = """
        SELECT zona_baliza_nome,
               COUNT(*) as total,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as perc,
               ROUND(AVG(CASE WHEN resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa_defesa
        FROM lances
        WHERE tipo_remate = '7 metros'
        GROUP BY zona_baliza_id
        ORDER BY zona_baliza_id
        """
        with db.get_connection() as conn:
            zonas_geral = pd.read_sql_query(query_geral, conn)
        
        st.dataframe(zonas_geral, use_container_width=True)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("🎯 Análise Penalties | Digital Twin ABC Braga | H2O.ai (dist=7m)")