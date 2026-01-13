"""
Dashboard Treino - Digital Twin ABC Braga
Planeamento de treino baseado em dados
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data_access import HandballDataAccess
import sys
sys.path.append('..')

try:
    from models.predictor_defesa import DefesaPredictor
    H2O_OK = True
except:
    H2O_OK = False

# =============================================================================
# CONFIG
# =============================================================================
st.set_page_config(page_title="Treino - ABC Braga", page_icon="🏋️", layout="wide")

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
# BANCO DE EXERCÍCIOS
# =============================================================================
EXERCICIOS = {
    0: {  # Superior Esquerda
        'zona': 'Superior Esquerda',
        'problema': 'Dificuldade em alcançar o canto alto esquerdo',
        'exercicios': [
            {'nome': 'Salto lateral explosivo', 'desc': 'Saltar do centro para o canto superior esquerdo', 'reps': '3x10', 'tempo': '10min'},
            {'nome': 'Envergadura com elástico', 'desc': 'Esticar braço esquerdo contra resistência', 'reps': '3x15', 'tempo': '8min'},
            {'nome': 'Reação a bola alta', 'desc': 'Treinador lança bolas altas, GR defende', 'reps': '3x12', 'tempo': '12min'},
        ],
        'dicas': ['Manter braço esquerdo mais alto na posição base', 'Trabalhar impulsão da perna direita', 'Antecipar remates ao ângulo']
    },
    1: {  # Superior Centro
        'zona': 'Superior Centro',
        'problema': 'Remates altos ao centro passam por cima',
        'exercicios': [
            {'nome': 'Salto vertical', 'desc': 'Saltar na vertical com braços esticados', 'reps': '3x12', 'tempo': '10min'},
            {'nome': 'Defesa em X', 'desc': 'Posição X com braços e pernas abertos', 'reps': '3x10', 'tempo': '8min'},
            {'nome': 'Bolas altas em sequência', 'desc': 'Defender bolas altas consecutivas', 'reps': '4x8', 'tempo': '15min'},
        ],
        'dicas': ['Posição mais recuada contra rematadores de longe', 'Mãos sempre acima dos ombros', 'Não baixar a guarda']
    },
    2: {  # Superior Direita
        'zona': 'Superior Direita',
        'problema': 'Dificuldade em alcançar o canto alto direito',
        'exercicios': [
            {'nome': 'Salto lateral explosivo', 'desc': 'Saltar do centro para o canto superior direito', 'reps': '3x10', 'tempo': '10min'},
            {'nome': 'Envergadura com elástico', 'desc': 'Esticar braço direito contra resistência', 'reps': '3x15', 'tempo': '8min'},
            {'nome': 'Reação cruzada', 'desc': 'Bola do lado esquerdo para canto direito alto', 'reps': '3x10', 'tempo': '12min'},
        ],
        'dicas': ['Manter braço direito mais alto', 'Trabalhar impulsão da perna esquerda', 'Atenção a remates cruzados']
    },
    3: {  # Meio Esquerda
        'zona': 'Meio Esquerda',
        'problema': 'Reação lenta ao lado esquerdo',
        'exercicios': [
            {'nome': 'Deslocamento lateral', 'desc': 'Deslocamentos rápidos para a esquerda', 'reps': '4x10', 'tempo': '10min'},
            {'nome': 'Defesa com step', 'desc': 'Step lateral + defesa com braço', 'reps': '3x12', 'tempo': '12min'},
            {'nome': 'Reação a luz/som', 'desc': 'Reagir a estímulo e defender esquerda', 'reps': '3x15', 'tempo': '10min'},
        ],
        'dicas': ['Peso mais no pé direito para arrancar', 'Braço esquerdo sempre ativo', 'Antecipar o lado do remate']
    },
    4: {  # Meio Centro
        'zona': 'Meio Centro',
        'problema': 'Bolas ao corpo não são defendidas',
        'exercicios': [
            {'nome': 'Defesa corporal', 'desc': 'Usar o corpo para bloquear bolas ao centro', 'reps': '3x15', 'tempo': '10min'},
            {'nome': 'Posição fechada', 'desc': 'Treinar posição compacta', 'reps': '3x10', 'tempo': '8min'},
            {'nome': 'Reação rápida ao centro', 'desc': 'Bolas rápidas ao corpo', 'reps': '4x12', 'tempo': '12min'},
        ],
        'dicas': ['Fechar mais o corpo na posição base', 'Usar pernas para bolas ao centro-baixo', 'Não abrir demasiado cedo']
    },
    5: {  # Meio Direita
        'zona': 'Meio Direita',
        'problema': 'Reação lenta ao lado direito',
        'exercicios': [
            {'nome': 'Deslocamento lateral', 'desc': 'Deslocamentos rápidos para a direita', 'reps': '4x10', 'tempo': '10min'},
            {'nome': 'Defesa com step', 'desc': 'Step lateral + defesa com braço', 'reps': '3x12', 'tempo': '12min'},
            {'nome': 'Espelho', 'desc': 'Seguir movimentos do treinador', 'reps': '3x2min', 'tempo': '8min'},
        ],
        'dicas': ['Peso mais no pé esquerdo para arrancar', 'Braço direito sempre ativo', 'Treinar velocidade lateral']
    },
    6: {  # Inferior Esquerda
        'zona': 'Inferior Esquerda',
        'problema': 'Dificuldade em mergulhos para a esquerda',
        'exercicios': [
            {'nome': 'Mergulho lateral', 'desc': 'Mergulhar para o canto inferior esquerdo', 'reps': '3x8', 'tempo': '12min'},
            {'nome': 'Flexibilidade anca', 'desc': 'Alongamentos dinâmicos da anca', 'reps': '3x30s', 'tempo': '5min'},
            {'nome': 'Spagat lateral', 'desc': 'Trabalhar abertura lateral', 'reps': '3x20s', 'tempo': '5min'},
        ],
        'dicas': ['Baixar mais o centro de gravidade', 'Perna esquerda mais flexionada', 'Atacar a bola, não esperar']
    },
    7: {  # Inferior Centro
        'zona': 'Inferior Centro',
        'problema': 'Bolas rasteiras passam entre as pernas',
        'exercicios': [
            {'nome': 'Fecho de pernas', 'desc': 'Fechar pernas rapidamente', 'reps': '4x12', 'tempo': '10min'},
            {'nome': 'Posição baixa', 'desc': 'Manter posição baixa prolongada', 'reps': '3x30s', 'tempo': '5min'},
            {'nome': 'Bolas rasteiras', 'desc': 'Defender bolas pelo chão', 'reps': '3x15', 'tempo': '12min'},
        ],
        'dicas': ['Joelhos mais fletidos', 'Nunca cruzar as pernas', 'Peso na ponta dos pés']
    },
    8: {  # Inferior Direita
        'zona': 'Inferior Direita',
        'problema': 'Dificuldade em mergulhos para a direita',
        'exercicios': [
            {'nome': 'Mergulho lateral', 'desc': 'Mergulhar para o canto inferior direito', 'reps': '3x8', 'tempo': '12min'},
            {'nome': 'Flexibilidade anca', 'desc': 'Alongamentos dinâmicos da anca', 'reps': '3x30s', 'tempo': '5min'},
            {'nome': 'Queda controlada', 'desc': 'Treinar técnica de queda para a direita', 'reps': '3x10', 'tempo': '8min'},
        ],
        'dicas': ['Baixar mais o centro de gravidade', 'Perna direita mais flexionada', 'Atacar a bola com a mão']
    }
}

ZONAS_NOME = ['Sup.Esq', 'Sup.Centro', 'Sup.Dir', 'Meio.Esq', 'Meio.Centro', 'Meio.Dir', 'Inf.Esq', 'Inf.Centro', 'Inf.Dir']

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
def calcular_probs_gr(gr, predictor, dist=9.0, vel=95, minuto=30, dif=0):
    """Retorna grid 3x3, média e lista de probs"""
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
# VERIFICAR H2O
# =============================================================================
if not predictor:
    st.error("⚠️ Modelo H2O não disponível")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("## ⚙️ CONFIGURAÇÃO")
    
    # GRs
    query = "SELECT * FROM guarda_redes"
    with db.get_connection() as conn:
        grs = pd.read_sql_query(query, conn)
    
    gr_selecionado = st.selectbox("Guarda-Redes", grs['nome'].tolist())
    gr_data = grs[grs['nome'] == gr_selecionado].iloc[0]
    
    st.divider()
    
    # Adversários
    query = "SELECT id, nome FROM adversarios ORDER BY ranking_liga"
    with db.get_connection() as conn:
        advs = pd.read_sql_query(query, conn)
    
    adv_nome = st.selectbox("Próximo Adversário", advs['nome'].tolist())
    adv_id = int(advs[advs['nome'] == adv_nome]['id'].values[0])
    
    query = "SELECT * FROM adversarios WHERE id = ?"
    with db.get_connection() as conn:
        adv_info = pd.read_sql_query(query, conn, params=(adv_id,)).iloc[0]
    
    st.divider()
    
    st.markdown("## 📊 Condições Treino")
    treino_dist = st.slider("Distância (m)", 6.0, 12.0, 9.0, 0.5)
    treino_vel = st.slider("Velocidade (km/h)", 70, 120, int(adv_info['velocidade_media_remate_kmh']))

# =============================================================================
# HEADER
# =============================================================================
st.markdown(f"""
<div style="background: linear-gradient(90deg, #1a1a2e, #16213e); 
            padding: 15px 25px; border-radius: 10px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 28px; font-weight: bold; color: white;">🏋️ PLANEAMENTO DE TREINO</span>
            <span style="font-size: 18px; color: #ccc; margin-left: 20px;">Melhoria contínua baseada em dados</span>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 20px; color: white;">Próximo jogo: <b>{adv_nome}</b></span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# CALCULAR DADOS
# =============================================================================
# Distribuição do adversário
def get_dist_adversario(adv):
    alta = adv['remates_zona_alta_perc']
    media = adv['remates_zona_media_perc']
    baixa = adv['remates_zona_baixa_perc']
    return np.array([
        [alta * 0.28, alta * 0.44, alta * 0.28],
        [media * 0.35, media * 0.30, media * 0.35],
        [baixa * 0.30, baixa * 0.40, baixa * 0.30]
    ])

# =============================================================================
# TABS
# =============================================================================
tab1, tab2, tab3 = st.tabs(["📊 Análise Individual", "👥 Comparação Plantel", "🎯 Plano Semanal"])

# =============================================================================
# TAB 1: ANÁLISE INDIVIDUAL
# =============================================================================
with tab1:
    # Calcular dados do GR selecionado
    grid_gr, media_gr, probs_gr = calcular_probs_gr(gr_data, predictor, treino_dist, treino_vel)
    zonas_fracas = np.argsort(probs_gr)[:3].tolist()
    
    st.markdown(f"### 📊 Análise de {gr_selecionado}")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Heatmap com zonas fracas destacadas
        fig = heatmap_baliza(grid_gr, f"Probabilidade de Defesa - {gr_selecionado}", 420, destacar_fracas=zonas_fracas)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.caption("🔴 Bordas vermelhas = Zonas mais fracas")
    
    with col2:
        st.markdown("### 📉 Top 3 Zonas a Melhorar")
        
        for i, zona_idx in enumerate(zonas_fracas):
            prob = probs_gr[zona_idx]
            zona_info = EXERCICIOS[zona_idx]
            
            if prob < 35:
                cor = "#dc3545"
                urgencia = "CRÍTICO"
            elif prob < 45:
                cor = "#ffc107"
                urgencia = "IMPORTANTE"
            else:
                cor = "#17a2b8"
                urgencia = "ATENÇÃO"
            
            st.markdown(f"""
            <div style="background: {cor}22; border-left: 5px solid {cor}; 
                        padding: 15px; border-radius: 0 10px 10px 0; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 14px; color: {cor}; font-weight: bold;">{urgencia}</span>
                        <div style="font-size: 18px; font-weight: bold; margin-top: 5px;">{zona_info['zona']}</div>
                    </div>
                    <div style="font-size: 32px; font-weight: bold; color: {cor};">{prob:.0f}%</div>
                </div>
                <div style="font-size: 12px; color: #888; margin-top: 8px;">{zona_info['problema']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Média geral
        st.markdown("")
        st.metric("📊 Média Geral", f"{media_gr:.1f}%", 
                  delta=f"{media_gr - 50:.1f}% vs 50%" if media_gr != 50 else None)
    
 
    
    # Exercícios recomendados
    st.markdown("### 🏋️ Exercícios Recomendados")
    
    for zona_idx in zonas_fracas:
        zona_info = EXERCICIOS[zona_idx]
        
        with st.expander(f"📍 {zona_info['zona']} ({probs_gr[zona_idx]:.0f}%)", expanded=(zona_idx == zonas_fracas[0])):
            
            st.markdown(f"**Problema:** {zona_info['problema']}")
            st.markdown("")
            
            # Exercícios
            for ex in zona_info['exercicios']:
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 12px 15px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 16px; font-weight: bold;">🔹 {ex['nome']}</div>
                            <div style="font-size: 13px; color: #666; margin-top: 4px;">{ex['desc']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 14px; font-weight: bold; color: #17a2b8;">{ex['reps']}</div>
                            <div style="font-size: 12px; color: #888;">⏱️ {ex['tempo']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Dicas
            st.markdown("")
            st.markdown("**💡 Dicas:**")
            for dica in zona_info['dicas']:
                st.markdown(f"- {dica}")

# =============================================================================
# TAB 2: COMPARAÇÃO PLANTEL
# =============================================================================
    
with tab2:
    st.markdown("### 👥 Comparação dos Guarda-Redes")
    
    # Calcular dados de todos os GRs
    todos_grs = []
    for _, gr in grs.iterrows():
        grid, media, probs = calcular_probs_gr(gr, predictor, treino_dist, treino_vel)
        todos_grs.append({
            'nome': gr['nome'],
            'altura': gr['altura_cm'],
            'grid': grid,
            'media': media,
            'probs': probs
        })
    
    # Heatmaps lado a lado
    cols = st.columns(3)
    for i, gr_info in enumerate(todos_grs):
        with cols[i]:
            # Nome do GR em destaque
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.4rem; font-weight: 700; color: #333;">
                    {gr_info['nome']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            zonas_fracas_gr = np.argsort(gr_info['probs'])[:3].tolist()
            fig = heatmap_baliza(gr_info['grid'], "", 450, destacar_fracas=zonas_fracas_gr)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Card com estatísticas
            cor = '#28a745' if gr_info['media'] >= 50 else '#ffc107' if gr_info['media'] >= 40 else '#dc3545'
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {cor}15 0%, {cor}30 100%); 
                        padding: 1rem; border-radius: 12px; text-align: center;
                        border-left: 5px solid {cor}; margin-top: 0.5rem;">
                <div style="font-size: 2.2rem; font-weight: 800; color: {cor}; margin-bottom: 0.2rem;">
                    {gr_info['media']:.1f}%
                </div>
                <div style="font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: 1px;">
                    Eficácia Média
                </div>
                <div style="margin-top: 0.6rem; padding-top: 0.6rem; border-top: 1px solid {cor}40;">
                    <div style="font-size: 0.8rem; color: #888;">
                        🎯 Altura: <b>{gr_info['altura']} cm</b>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Especialista por Zona
st.markdown("### 🏆 Especialista por Zona")
st.caption("Quem é o melhor em cada zona da baliza?")

# Grid 3x3 de cards - ALTURA REDUZIDA + LETRA MAIOR
zona_idx = 0
for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        melhor_gr = max(todos_grs, key=lambda x: x['probs'][zona_idx])
        pior_gr = min(todos_grs, key=lambda x: x['probs'][zona_idx])
        diff = melhor_gr['probs'][zona_idx] - pior_gr['probs'][zona_idx]
        
        with cols[col]:
            st.markdown(f"""
            <div style="background: white; padding: 12px 15px; border-radius: 6px; 
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-top: 2px solid #28a745;
                        max-width: 300px; margin: 0 auto;">
                <div style="font-size: 13px; color: #888; font-weight: 600; 
                            text-transform: uppercase; margin-bottom: 10px;">
                    {ZONAS_NOME[zona_idx]}
                </div>
                <div style="margin-bottom: 10px;">
                    <div style="font-size: 13px; color: #28a745;">🥇 {melhor_gr['nome']}</div>
                    <div style="font-size: 28px; font-weight: 800; color: #28a745; line-height: 1;">
                        {melhor_gr['probs'][zona_idx]:.0f}%
                    </div>
                </div>
                <div style="border-top: 1px solid #eee; padding-top: 8px; margin-top: 8px; margin-bottom: 8px;">
                    <div style="font-size: 13px; color: #dc3545;">
                        ⚠️ {pior_gr['nome']} ({pior_gr['probs'][zona_idx]:.0f}%)
                    </div>
                </div>
                <div style="padding: 6px; background: #f8f9fa; border-radius: 4px; text-align: center;">
                    <span style="font-size: 12px; color: #666;">Gap:</span>
                    <span style="font-size: 18px; font-weight: 700; color: #667eea; margin-left: 4px;">{diff:.0f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        zona_idx += 1
        
# =============================================================================
# TAB 3: PLANO SEMANAL
# =============================================================================
with tab3:
    # RECALCULAR tudo para o GR atual
    grid_gr, media_gr, probs_gr = calcular_probs_gr(gr_data, predictor, treino_dist, treino_vel)
    zonas_fracas = np.argsort(probs_gr)[:3].tolist()
    dist_adv = get_dist_adversario(adv_info)
    zona_adv_forte = np.argmax(dist_adv.flatten())
    
    st.markdown(f"### 🎯 Plano de Treino: **{gr_selecionado}**")
    
    # Informação sobre adversário (contexto)
    st.info(f"💡 Próximo adversário: **{adv_nome}** | Zona preferida: **{ZONAS_NOME[zona_adv_forte]}** ({dist_adv.flatten()[zona_adv_forte]:.1f}%)")
    
    # TREINO FOCA NAS PIORES ZONAS DO GR (desenvolvimento a longo prazo)
    st.markdown("#### 🔥 Zonas PRIORITÁRIAS para Treino")
    st.caption(f"Zonas mais fracas do **{gr_selecionado}** (desenvolvimento individual)")
    
    prioridades = []
    for zona_idx in range(9):
        prob_defesa = probs_gr[zona_idx]
        prob_ataque = dist_adv.flatten()[zona_idx]
        
        # Prioridade baseada na LACUNA do GR
        lacuna = 100 - prob_defesa
        
        prioridades.append({
            'zona_idx': zona_idx,
            'zona': ZONAS_NOME[zona_idx],
            'defesa': prob_defesa,
            'ataque_adv': prob_ataque,
            'lacuna': lacuna
        })

    # Ordenar pelas PIORES zonas do GR
    prioridades = sorted(prioridades, key=lambda x: x['lacuna'], reverse=True)
    top3_prioridades = prioridades[:3]
    
    # Mostrar prioridades
    cols_prio = st.columns(3)
    for i, prio in enumerate(top3_prioridades):
        with cols_prio[i]:
            cor = "#dc3545" if i == 0 else "#ffc107" if i == 1 else "#17a2b8"
            
            st.markdown(f"""
            <div style="background: {cor}22; border: 3px solid {cor}; 
                        border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 14px; color: {cor};">PRIORIDADE {i+1}</div>
                <div style="font-size: 22px; font-weight: bold; margin: 10px 0;">{prio['zona']}</div>
                <div style="font-size: 13px; color: #666;">
                    Defesa GR: <b>{prio['defesa']:.0f}%</b><br>
                    Lacuna: <b>{prio['lacuna']:.0f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # RESUMO DO PLANO (mostrar objetivos primeiro!)
    st.markdown("#### 📊 Objetivos do Plano Semanal")
    
    col1, col2, col3 = st.columns(3)
    
    tempo_total = 90*3 + 45 + 90  # Segunda/Terça/Quinta/Sexta + Quarta
    
    with col1:
        st.metric("⏱️ Tempo Total Semanal", f"{tempo_total} min", f"{tempo_total//60}h{tempo_total%60}min")
    
    with col2:
        zonas_trabalhadas = f"{top3_prioridades[0]['zona']}, {top3_prioridades[1]['zona']}, {top3_prioridades[2]['zona']}"
        st.metric("🎯 Zonas Prioritárias", "3", zonas_trabalhadas)
    
    with col3:
        # Melhoria esperada baseada nas lacunas
        lacuna_media = np.mean([100 - p['defesa'] for p in top3_prioridades])
        melhoria_esperada = lacuna_media * 0.15  # 15% de melhoria na lacuna
        st.metric("📈 Melhoria Esperada", f"+{melhoria_esperada:.1f}%", "Por zona (1 mês)")
    
    st.divider()
    
    # Calcular duração baseada na lacuna
    def calcular_duracao_treino(prob_defesa):
        """Quanto pior a zona, mais tempo de treino"""
        if prob_defesa < 35:
            return 30  # CRÍTICO - 30min
        elif prob_defesa < 45:
            return 25  # IMPORTANTE - 25min
        else:
            return 20  # ATENÇÃO - 20min
    
    # Plano semanal
    st.markdown("#### 📅 Plano Semanal de Treino (1h30 por sessão)")
    
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
    
    duracao_zona1 = calcular_duracao_treino(top3_prioridades[0]['defesa'])
    duracao_zona2 = calcular_duracao_treino(top3_prioridades[1]['defesa'])
    duracao_zona3 = calcular_duracao_treino(top3_prioridades[2]['defesa'])
    
    plano = {
        'Segunda': {
            'foco': top3_prioridades[0]['zona'],
            'zona_idx': top3_prioridades[0]['zona_idx'],
            'tipo': 'Técnico Intensivo',
            'duracao_especifica': duracao_zona1,
            'duracao_total': '1h30'
        },
        'Terça': {
            'foco': top3_prioridades[1]['zona'],
            'zona_idx': top3_prioridades[1]['zona_idx'],
            'tipo': 'Técnico + Reação',
            'duracao_especifica': duracao_zona2,
            'duracao_total': '1h30'
        },
        'Quarta': {
            'foco': 'Recuperação Ativa',
            'zona_idx': None,
            'tipo': 'Alongamentos + Mobilidade',
            'duracao_especifica': None,
            'duracao_total': '45min'
        },
        'Quinta': {
            'foco': top3_prioridades[2]['zona'],
            'zona_idx': top3_prioridades[2]['zona_idx'],
            'tipo': 'Técnico + Velocidade',
            'duracao_especifica': duracao_zona3,
            'duracao_total': '1h30'
        },
        'Sexta': {
            'foco': 'Simulação de Jogo',
            'zona_idx': None,
            'tipo': f'Remates estilo {adv_nome}',
            'duracao_especifica': None,
            'duracao_total': '1h30'
        }
    }
    
    for dia in dias:
        info = plano[dia]
        zona_idx = info['zona_idx']
        
        with st.expander(f"📅 **{dia}** - {info['foco']} ({info['duracao_total']})", expanded=(dia == 'Segunda')):
            
            st.markdown(f"**Tipo de Treino:** {info['tipo']}")
            
            if zona_idx is not None:
                zona_info = EXERCICIOS[zona_idx]
                duracao_esp = info['duracao_especifica']
                
                st.markdown(f"**Objetivo:** Melhorar defesa na zona {zona_info['zona']}")
                st.markdown(f"**Tempo Zona Específica:** {duracao_esp} minutos (restante: aquecimento + exercícios gerais)")
                st.markdown("")
                
                # Exercícios específicos da zona
                st.markdown("**🎯 Exercícios Específicos da Zona:**")
                for ex in zona_info['exercicios']:
                    st.markdown(f"""
                    <div style="background: #f0f2f6; padding: 10px 15px; border-radius: 8px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔹 <b>{ex['nome']}</b> - {ex['desc']}</span>
                            <span style="color: #17a2b8;">{ex['reps']} | {ex['tempo']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("")
                st.markdown("**💡 Dicas do dia:**")
                for dica in zona_info['dicas']:
                    st.markdown(f"- {dica}")
                
                st.markdown("")
                st.markdown(f"**⏱️ Estrutura da Sessão (90min):**")
                st.markdown(f"""
                - Aquecimento geral (15min)
                - Exercícios zona específica ({duracao_esp}min)
                - Exercícios complementares ({90-15-duracao_esp}min)
                - Alongamentos finais (restante)
                """)
            
            else:
                if dia == 'Quarta':
                    st.markdown("**⏱️ Sessão de Recuperação (45min):**")
                    st.markdown("""
                    - Alongamentos dinâmicos (15min)
                    - Mobilidade articular (15min)
                    - Exercícios de proprioceção (10min)
                    - Relaxamento muscular (5min)
                    """)
                else:
                    st.markdown("**⏱️ Sessão de Jogo (90min):**")
                    st.markdown(f"""
                    - Aquecimento específico (15min)
                    - Situações reais de jogo (45min)
                    - Remates variados (20min)
                    - Análise de vídeo + feedback (10min)
                    
                    **Simular padrões do {adv_nome}:**
                    - Velocidade média: {adv_info['velocidade_media_remate_kmh']} km/h
                    - Zona preferida: {ZONAS_NOME[zona_adv_forte]}
                    - Foco nas 3 zonas prioritárias do plano
                    """)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("🏋️ Planeamento de Treino | Digital Twin ABC Braga | H2O.ai AutoML")