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
    
    # Fundo
    fig.add_shape(type='rect', x0=-1.5, x1=3.5, y0=-1.2, y1=3.5,
                  fillcolor='#2C3E50', line=dict(width=0), layer='below')
    fig.add_shape(type='rect', x0=-1.2, x1=3.2, y0=-0.8, y1=-0.5,
                  fillcolor='#3498DB', line=dict(width=0), layer='below')
    fig.add_shape(type='rect', x0=-0.8, x1=2.8, y0=-0.7, y1=-0.5,
                  fillcolor='#2980B9', line=dict(color='white', width=2), layer='below')
    
    # Heatmap
    fig.add_trace(go.Heatmap(
        z=grid_plot, x=[0, 1, 2], y=[0, 1, 2],
        colorscale='RdYlGn', zmin=0, zmax=100,
        text=np.round(grid_plot, 0), texttemplate='%{text}%',
        textfont=dict(size=20, color='black', family='Arial Black'),
        showscale=False, xgap=4, ygap=4
    ))
    
    # Postes listrados
    for i in range(10):
        c = '#C41E3A' if i % 2 == 0 else 'white'
        fig.add_shape(type='rect', x0=-0.7, x1=-0.48, y0=-0.5+i*0.35, y1=-0.5+(i+1)*0.35,
                      fillcolor=c, line=dict(color='#333', width=1))
        fig.add_shape(type='rect', x0=2.48, x1=2.7, y0=-0.5+i*0.35, y1=-0.5+(i+1)*0.35,
                      fillcolor=c, line=dict(color='#333', width=1))
    for i in range(9):
        c = '#C41E3A' if i % 2 == 0 else 'white'
        fig.add_shape(type='rect', x0=-0.7+i*0.38, x1=-0.7+(i+1)*0.38, y0=2.48, y1=2.7,
                      fillcolor=c, line=dict(color='#333', width=1))
    
    # Rede
    for i in range(8):
        fig.add_shape(type='line', x0=-0.5+i*0.43, x1=-0.5+i*0.43, y0=-0.5, y1=2.5,
                      line=dict(color='rgba(200,200,200,0.3)', width=1))
        fig.add_shape(type='line', x0=-0.5, x1=2.5, y0=-0.5+i*0.43, y1=-0.5+i*0.43,
                      line=dict(color='rgba(200,200,200,0.3)', width=1))
    
    # Destacar zonas fracas com borda
    if destacar_fracas:
        for zona_idx in destacar_fracas:
            row = zona_idx // 3
            col = zona_idx % 3
            # Converter para coordenadas do plot (invertido)
            y_plot = 2 - row
            x_plot = col
            fig.add_shape(type='rect', 
                         x0=x_plot-0.48, x1=x_plot+0.48, 
                         y0=y_plot-0.48, y1=y_plot+0.48,
                         line=dict(color='#ff0000', width=4),
                         fillcolor='rgba(0,0,0,0)')
    
    # Labels
    fig.add_annotation(x=0, y=-0.95, text="ESQ", showarrow=False, font=dict(size=11, color='white', family='Arial Black'))
    fig.add_annotation(x=1, y=-0.95, text="CENTRO", showarrow=False, font=dict(size=11, color='white', family='Arial Black'))
    fig.add_annotation(x=2, y=-0.95, text="DIR", showarrow=False, font=dict(size=11, color='white', family='Arial Black'))
    fig.add_annotation(x=-1.0, y=2, text="SUP", showarrow=False, font=dict(size=11, color='white', family='Arial Black'))
    fig.add_annotation(x=-1.0, y=1, text="MEIO", showarrow=False, font=dict(size=11, color='white', family='Arial Black'))
    fig.add_annotation(x=-1.0, y=0, text="INF", showarrow=False, font=dict(size=11, color='white', family='Arial Black'))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14, color='white')),
        height=height,
        xaxis=dict(showgrid=False, showticklabels=False, range=[-1.5, 3.5], fixedrange=True),
        yaxis=dict(showgrid=False, showticklabels=False, scaleanchor='x', range=[-1.2, 3.3], fixedrange=True),
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor='#2C3E50', paper_bgcolor='#1a1a2e'
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
# Dados do GR selecionado
grid_gr, media_gr, probs_gr = calcular_probs_gr(gr_data, predictor, treino_dist, treino_vel)

# Identificar 3 zonas mais fracas
zonas_ordenadas = np.argsort(probs_gr)
zonas_fracas = zonas_ordenadas[:3].tolist()

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

dist_adv = get_dist_adversario(adv_info)
zona_adv_forte = np.argmax(dist_adv.flatten())

# =============================================================================
# TABS
# =============================================================================
tab1, tab2, tab3 = st.tabs(["📊 Análise Individual", "👥 Comparação Plantel", "🎯 Plano Semanal"])

# =============================================================================
# TAB 1: ANÁLISE INDIVIDUAL
# =============================================================================
with tab1:
    st.markdown(f"### 📊 Análise de {gr_selecionado}")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Heatmap com zonas fracas destacadas
        fig = heatmap_baliza(grid_gr, f"Probabilidade de Defesa - {gr_selecionado}", 420, destacar_fracas=zonas_fracas)
        st.plotly_chart(fig, use_container_width=True)
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
                  delta=f"{media_gr - 50:.1f}pp vs 50%" if media_gr != 50 else None)
    
    st.divider()
    
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
            zonas_fracas_gr = np.argsort(gr_info['probs'])[:3].tolist()
            fig = heatmap_baliza(gr_info['grid'], gr_info['nome'], 320, destacar_fracas=zonas_fracas_gr)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 28px; font-weight: bold; color: {'#28a745' if gr_info['media'] >= 50 else '#ffc107' if gr_info['media'] >= 40 else '#dc3545'};">
                    {gr_info['media']:.1f}%
                </div>
                <div style="font-size: 12px; color: #888;">Média geral</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Matriz: Melhor GR por zona
    st.markdown("### 🏆 Especialista por Zona")
    st.caption("Quem é o melhor em cada zona da baliza?")
    
    matriz_data = []
    for zona_idx in range(9):
        melhor_gr = max(todos_grs, key=lambda x: x['probs'][zona_idx])
        pior_gr = min(todos_grs, key=lambda x: x['probs'][zona_idx])
        
        matriz_data.append({
            'Zona': ZONAS_NOME[zona_idx],
            '🥇 Melhor': f"{melhor_gr['nome']} ({melhor_gr['probs'][zona_idx]:.0f}%)",
            '⚠️ Pior': f"{pior_gr['nome']} ({pior_gr['probs'][zona_idx]:.0f}%)",
            'Diferença': f"{melhor_gr['probs'][zona_idx] - pior_gr['probs'][zona_idx]:.0f}pp"
        })
    
    df_matriz = pd.DataFrame(matriz_data)
    st.dataframe(df_matriz, use_container_width=True, hide_index=True)

# =============================================================================
# TAB 3: PLANO SEMANAL
# =============================================================================
with tab3:
    st.markdown(f"### 🎯 Plano de Treino vs **{adv_nome}**")
    
    # Cruzar zonas fracas do GR com zonas fortes do adversário
    st.markdown("#### 🔥 Zonas PRIORITÁRIAS")
    st.caption("Cruzamento: Zonas fracas do GR + Zonas preferidas do adversário")
    
    # Calcular prioridade
    prioridades = []
    for zona_idx in range(9):
        prob_defesa = probs_gr[zona_idx]
        prob_ataque = dist_adv.flatten()[zona_idx]
        
        # Prioridade = onde o adversário ataca mais E o GR defende menos
        risco = (100 - prob_defesa) * prob_ataque / 100
        
        prioridades.append({
            'zona_idx': zona_idx,
            'zona': ZONAS_NOME[zona_idx],
            'defesa': prob_defesa,
            'ataque_adv': prob_ataque,
            'risco': risco
        })
    
    prioridades = sorted(prioridades, key=lambda x: x['risco'], reverse=True)
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
                    Defesa: <b>{prio['defesa']:.0f}%</b><br>
                    Ataque ADV: <b>{prio['ataque_adv']:.1f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Plano semanal
    st.markdown("#### 📅 Plano Semanal de Treino")
    
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
    
    plano = {
        'Segunda': {
            'foco': top3_prioridades[0]['zona'],
            'zona_idx': top3_prioridades[0]['zona_idx'],
            'tipo': 'Técnico Intensivo',
            'duracao': '45min'
        },
        'Terça': {
            'foco': top3_prioridades[1]['zona'],
            'zona_idx': top3_prioridades[1]['zona_idx'],
            'tipo': 'Técnico + Reação',
            'duracao': '40min'
        },
        'Quarta': {
            'foco': 'Recuperação Ativa',
            'zona_idx': None,
            'tipo': 'Alongamentos + Mobilidade',
            'duracao': '30min'
        },
        'Quinta': {
            'foco': top3_prioridades[2]['zona'],
            'zona_idx': top3_prioridades[2]['zona_idx'],
            'tipo': 'Técnico + Velocidade',
            'duracao': '40min'
        },
        'Sexta': {
            'foco': 'Simulação de Jogo',
            'zona_idx': None,
            'tipo': f'Remates estilo {adv_nome}',
            'duracao': '35min'
        }
    }
    
    for dia in dias:
        info = plano[dia]
        zona_idx = info['zona_idx']
        
        with st.expander(f"📅 **{dia}** - {info['foco']} ({info['duracao']})", expanded=(dia == 'Segunda')):
            
            st.markdown(f"**Tipo:** {info['tipo']}")
            
            if zona_idx is not None:
                zona_info = EXERCICIOS[zona_idx]
                
                st.markdown(f"**Objetivo:** Melhorar defesa na zona {zona_info['zona']}")
                st.markdown("")
                
                # Exercícios do dia
                st.markdown("**Exercícios:**")
                tempo_total = 0
                for ex in zona_info['exercicios']:
                    tempo_total += int(ex['tempo'].replace('min', ''))
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
                for dica in zona_info['dicas'][:2]:
                    st.markdown(f"- {dica}")
            
            else:
                if dia == 'Quarta':
                    st.markdown("""
                    - Alongamentos dinâmicos (10min)
                    - Mobilidade articular (10min)
                    - Exercícios de proprioceção (10min)
                    """)
                else:
                    st.markdown(f"""
                    - Aquecimento específico (10min)
                    - Remates variados (15min)
                    - Situações de jogo (10min)
                    
                    **Simular padrões do {adv_nome}:**
                    - Velocidade média: {adv_info['velocidade_media_remate_kmh']} km/h
                    - Zona preferida: {ZONAS_NOME[zona_adv_forte]}
                    """)
    
    st.divider()
    
    # Resumo
    st.markdown("#### 📊 Resumo do Plano")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("⏱️ Tempo Total", "190 min", "3h10")
    
    with col2:
        st.metric("🎯 Zonas Trabalhadas", "3", f"{', '.join([p['zona'] for p in top3_prioridades])}")
    
    with col3:
        # Melhoria esperada (estimativa)
        melhoria_esperada = sum([100 - p['defesa'] for p in top3_prioridades]) * 0.1
        st.metric("📈 Melhoria Esperada", f"+{melhoria_esperada:.0f}pp", "Estimativa")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("🏋️ Planeamento de Treino | Digital Twin ABC Braga | H2O.ai AutoML")