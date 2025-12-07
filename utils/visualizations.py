"""
Módulo de Visualizações Reutilizáveis
Funções para criar gráficos Plotly usados em múltiplos dashboards
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def criar_heatmap_baliza(zones_df, height=400):
    """
    Cria heatmap 3x3 da baliza com dados de performance por zona
    
    Args:
        zones_df: DataFrame com colunas 'zona_baliza_id' e 'taxa_defesa'
        height: Altura do gráfico em pixels
    
    Returns:
        Figura Plotly
    """
    # Converter IDs 1-9 para grid 3x3
    zones_grid = zones_df.set_index('zona_baliza_id')['taxa_defesa'].reindex(range(1, 10))
    zones_3x3 = zones_grid.values.reshape(3, 3)
    
    fig = go.Figure(data=go.Heatmap(
        z=zones_3x3,
        x=['Esquerda', 'Centro', 'Direita'],
        y=['Superior', 'Meio', 'Inferior'],
        colorscale='RdYlGn',
        text=np.round(zones_3x3, 0),
        texttemplate='%{text:.0f}%',
        textfont={"size": 16, "color": "white"},
        colorbar=dict(title="Taxa<br>Defesa (%)"),
        hovertemplate='<b>%{y} %{x}</b><br>Taxa Defesa: %{z:.1f}%<extra></extra>',
        zmin=0,
        zmax=100
    ))
    
    fig.update_layout(
        title="Performance por Zona da Baliza (Grid 3×3)",
        height=height,
        yaxis=dict(autorange='reversed'),
        xaxis=dict(side='bottom')
    )
    
    return fig


def criar_grafico_compatibilidade_barras(compat_df):
    """
    Cria gráfico de barras de compatibilidade GR vs Adversário
    
    Args:
        compat_df: DataFrame com colunas 'nome' e 'taxa_defesa_perc'
    
    Returns:
        Figura Plotly
    """
    fig = px.bar(
        compat_df,
        x='nome',
        y='taxa_defesa_perc',
        color='taxa_defesa_perc',
        color_continuous_scale='RdYlGn',
        text='taxa_defesa_perc',
        labels={
            'nome': 'Guarda-Redes',
            'taxa_defesa_perc': 'Taxa Defesa (%)'
        }
    )
    
    fig.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside'
    )
    
    fig.update_layout(
        title="Compatibilidade: Taxa de Defesa vs Adversário",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, 100])
    )
    
    return fig


def criar_grafico_vulnerabilidades(zones_adv, zones_gr):
    """
    Cria gráfico de barras comparando padrões adversário vs defesa GR
    
    Args:
        zones_adv: Lista com probabilidades de remate adversário por zona
        zones_gr: Lista com taxas de defesa do GR por zona
    
    Returns:
        Figura Plotly
    """
    zonas = [
        'Sup. Esq', 'Sup. Centro', 'Sup. Dir',
        'Méd. Esq', 'Méd. Centro', 'Méd. Dir',
        'Inf. Esq', 'Inf. Centro', 'Inf. Dir'
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Prob. Remate Adversário',
        x=zonas,
        y=zones_adv,
        marker_color='rgba(255, 99, 71, 0.7)',
        text=zones_adv,
        texttemplate='%{text}%'
    ))
    
    fig.add_trace(go.Bar(
        name='Taxa Defesa GR',
        x=zonas,
        y=zones_gr,
        marker_color='rgba(50, 171, 96, 0.7)',
        text=zones_gr,
        texttemplate='%{text:.0f}%'
    ))
    
    fig.update_layout(
        title="Análise de Vulnerabilidades por Zona",
        barmode='group',
        height=450,
        xaxis_title="Zona da Baliza",
        yaxis_title="Probabilidade / Taxa (%)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    return fig


def criar_grafico_gap(gap_df, nome_gr):
    """
    Cria gráfico de gap (atual vs objetivo) por zona
    
    Args:
        gap_df: DataFrame com colunas 'zona', 'atual', 'objetivo', 'gap'
        nome_gr: Nome do guarda-redes
    
    Returns:
        Figura Plotly
    """
    fig = go.Figure()
    
    # Barras de valores atuais
    fig.add_trace(go.Bar(
        name='Atual',
        x=gap_df['zona'],
        y=gap_df['atual'],
        marker_color='#ff7f0e',
        text=gap_df['atual'],
        texttemplate='%{text:.0f}%'
    ))
    
    # Barras de objetivos
    fig.add_trace(go.Bar(
        name='Objetivo',
        x=gap_df['zona'],
        y=gap_df['objetivo'],
        marker_color='#2ca02c',
        text=gap_df['objetivo'],
        texttemplate='%{text:.0f}%'
    ))
    
    # Linha de gap
    fig.add_trace(go.Scatter(
        name='Gap',
        x=gap_df['zona'],
        y=gap_df['gap'],
        mode='lines+markers',
        marker=dict(size=12, symbol='diamond', color='#d62728'),
        line=dict(width=3, color='#d62728'),
        yaxis='y2',
        text=gap_df['gap'],
        texttemplate='%{text:.0f}pp',
        textposition='top center'
    ))
    
    fig.update_layout(
        title=f"Gap de Performance - {nome_gr}",
        barmode='group',
        height=500,
        xaxis_title="Zona da Baliza",
        yaxis=dict(title="Eficácia (%)", side='left', range=[0, 100]),
        yaxis2=dict(
            title="Gap (pontos percentuais)",
            side='right',
            overlaying='y',
            range=[gap_df['gap'].min() - 5, gap_df['gap'].max() + 5]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    return fig


def criar_grafico_evolucao(evolucao_df):
    """
    Cria gráfico de evolução temporal de múltiplas métricas
    
    Args:
        evolucao_df: DataFrame com colunas 'mes', 'taxa_defesa_mes', 
                     'alcance_vertical_cm', 'velocidade_lateral_ms', 'confianca_1_10'
    
    Returns:
        Figura Plotly
    """
    # Inverter para mostrar mais recente à direita
    df = evolucao_df.iloc[::-1].copy()
    
    fig = go.Figure()
    
    # Taxa de defesa
    fig.add_trace(go.Scatter(
        x=df['mes'],
        y=df['taxa_defesa_mes'],
        mode='lines+markers',
        name='Taxa Defesa (%)',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Confiança (escalar para visualização)
    fig.add_trace(go.Scatter(
        x=df['mes'],
        y=df['confianca_1_10'] * 10,  # Escalar de 1-10 para 10-100
        mode='lines+markers',
        name='Confiança (×10)',
        line=dict(color='#2ca02c', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Evolução Temporal - Últimos 6 Meses",
        height=400,
        xaxis_title="Mês",
        yaxis_title="Valor",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def criar_radar_adversario(adv_info):
    """
    Cria gráfico radar com características do adversário
    
    Args:
        adv_info: Série Pandas com info do adversário
    
    Returns:
        Figura Plotly
    """
    categories = [
        'Eficácia 1ª Linha',
        'Eficácia 2ª Linha',
        'Zona Alta',
        'Zona Média',
        'Zona Baixa',
        'Velocidade'
    ]
    
    values = [
        adv_info['eficacia_primeira_linha_perc'],
        adv_info['eficacia_segunda_linha_perc'],
        adv_info['remates_zona_alta_perc'],
        adv_info['remates_zona_media_perc'],
        adv_info['remates_zona_baixa_perc'],
        min(100, adv_info['velocidade_media_remate_kmh'] * 0.8)  # Normalizar
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Adversário',
        line=dict(color='#ff7f0e', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        title="Perfil Ofensivo do Adversário",
        height=400
    )
    
    return fig


def criar_tabela_cenarios_roi(cenarios_df):
    """
    Cria tabela estilizada de cenários de treino por ROI
    
    Args:
        cenarios_df: DataFrame com cenários de treino
    
    Returns:
        DataFrame estilizado
    """
    # Preparar dados
    df_display = cenarios_df.copy()
    
    df_display['ROI'] = df_display['roi_estimado'].round(1)
    df_display['Ganho (%)'] = df_display['ganho_esperado'].round(1)
    df_display['Tempo (sem)'] = df_display['tempo_resultados_semanas'].astype(int)
    
    # Selecionar colunas
    df_final = df_display[[
        'cenario',
        'Ganho (%)',
        'ROI',
        'Tempo (sem)',
        'prioridade'
    ]].rename(columns={
        'cenario': 'Cenário',
        'prioridade': 'Prioridade'
    })
    
    # Aplicar estilo
    styled = df_final.style.background_gradient(
        subset=['ROI'],
        cmap='RdYlGn'
    ).format({
        'ROI': '{:.1f}',
        'Ganho (%)': '{:.1f}'
    })
    
    return styled


def criar_grafico_pizza(dados_dict, title="Distribuição"):
    """
    Cria gráfico de pizza genérico
    
    Args:
        dados_dict: Dicionário com labels e valores
        title: Título do gráfico
    
    Returns:
        Figura Plotly
    """
    fig = px.pie(
        values=list(dados_dict.values()),
        names=list(dados_dict.keys()),
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    fig.update_layout(
        height=350,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    return fig
