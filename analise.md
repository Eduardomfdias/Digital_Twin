# 📊 ANÁLISE EXPLORATÓRIA - DIGITAL TWIN ABC BRAGA

**Data:** Dezembro 2024  
**Dataset:** 1.622 lances, 30 jogos, 3 guarda-redes  
**Autor:** Eduardo Dias

---

## 🎯 DADOS GERAIS

- **Total de lances:** 1.622
- **Total de jogos:** 30
- **Guarda-redes:** 3 (Humberto, Diogo, Tiago)
- **Adversários:** 14 equipas
- **Treinos registados:** 360
- **Taxa Global de Defesa:** 43.6% (708 defesas vs 914 golos)

---

## 🥅 GUARDA-REDES

### Características Físicas

| Nome | Altura | Envergadura | Velocidade Lateral | Anos Experiência |
|------|--------|-------------|-------------------|------------------|
| Humberto Gomes | 185cm | 190cm | 4.2 m/s | 8 anos |
| Diogo Ribeiro | 186cm | 192cm | 3.8 m/s | 12 anos |
| Tiago Ferreira | 191cm | 198cm | 4.5 m/s | 3 anos |

### Performance Época 2025

| Nome | Jogos | Remates Sofridos | Defesas | Taxa Defesa (Época) |
|------|-------|------------------|---------|---------------------|
| Humberto Gomes | 20 | 568 | 338 | **59.5%** |
| Diogo Ribeiro | 12 | 285 | 178 | **62.5%** ⭐ |
| Tiago Ferreira | 15 | 368 | 212 | **57.6%** |

### Performance nos Lances (BD completa)

| Nome | Lances | Taxa Defesa |
|------|--------|-------------|
| Tiago Ferreira | 168 | 45.2% |
| Humberto Gomes | 1258 | 43.6% |
| Diogo Ribeiro | 196 | 42.3% |

**⚠️ DISCREPÂNCIA IMPORTANTE:**
- Taxa na **tabela épocas:** 59-62%
- Taxa nos **lances totais:** 42-45%
- **Hipótese:** BD pode ter lances de treino misturados com jogo

---

## 🗺️ TAXA DE DEFESA POR ZONA

### Ranking de Zonas

| Posição | Zona | Nome | Lances | Defesas | Taxa |
|---------|------|------|--------|---------|------|
| 1º | 5 | Média Centro | 178 | 113 | **63.5%** ⭐ |
| 2º | 6 | Média Direita | 190 | 98 | 51.6% |
| 3º | 4 | Média Esquerda | 186 | 95 | 51.1% |
| 4º | 2 | Superior Centro | 163 | 80 | 49.1% |
| 5º | 8 | Inferior Centro | 179 | 86 | 48.0% |
| 6º | 7 | Inferior Esquerda | 178 | 65 | 36.5% |
| 7º | 9 | Inferior Direita | 174 | 56 | 32.2% |
| 8º | 1 | Superior Esquerda | 174 | 55 | 31.6% |
| 9º | 3 | Superior Direita | 200 | 60 | **30.0%** ⚠️ |

### Heatmap 3x3 (%)

```
╔════════════╦════════════╦════════════╗
║  SUPERIOR  ║            ║            ║
╠════════════╬════════════╬════════════╣
║   31.6%    ║   49.1%    ║   30.0%    ║  ← Cantos superiores DIFÍCEIS
║  Esquerda  ║   Centro   ║  Direita   ║
╠════════════╬════════════╬════════════╣
║            ║   MEIO     ║            ║
╠════════════╬════════════╬════════════╣
║   51.1%    ║   63.5%    ║   51.6%    ║  ← Centro DOMINANTE
║  Esquerda  ║   Centro   ║  Direita   ║
╠════════════╬════════════╬════════════╣
║            ║  INFERIOR  ║            ║
╠════════════╬════════════╬════════════╣
║   36.5%    ║   48.0%    ║   32.2%    ║  ← Laterais baixas difíceis
║  Esquerda  ║   Centro   ║  Direita   ║
╚════════════╩════════════╩════════════╝
```

**🎯 CONCLUSÕES:**
- **Zona mais fácil:** Centro-Meio (5) → 63.5%
- **Zona mais difícil:** Superior Direita (3) → 30.0%
- **Padrão:** Centro > Laterais | Meio > Alto/Baixo
- **Diferença:** 33.5pp entre melhor e pior zona!

---

## 📏 IMPACTO DA DISTÂNCIA

| Categoria | Distância | Lances | Taxa Defesa |
|-----------|-----------|--------|-------------|
| Muito Perto | 6-7m | 521 | 40.5% |
| Perto | 7-9m | 659 | **46.6%** ⭐ |
| Médio | 9-11m | 442 | 43.0% |

**Estatísticas Descritivas:**
- Média: 8.1m
- Desvio padrão: 1.3m
- Mínimo: 6.0m | Máximo: 11.0m

**📊 PADRÃO INESPERADO:** 
- Taxa AUMENTA de 6-7m para 7-9m
- Depois DIMINUI ligeiramente para 9-11m
- **Hipótese:** Remates muito perto podem ser "surpresa", remates de 7-9m são mais previsíveis

**Correlação Distância-Defesa:** -0.022 (quase zero!)

---

## ⚡ IMPACTO DA VELOCIDADE

| Categoria | Velocidade | Lances | Taxa Defesa |
|-----------|------------|--------|-------------|
| Lento | <85 km/h | 2 | 0.0% |
| Médio | 85-95 km/h | 478 | 45.8% |
| Rápido | 95-105 km/h | 515 | 41.4% |
| Muito Rápido | >105 km/h | 627 | 44.0% |

**Estatísticas Descritivas:**
- Média: 101.4 km/h
- Desvio padrão: 9.5 km/h
- Mínimo: 85 km/h | Máximo: 118 km/h

**📊 PADRÃO IRREGULAR:**
- Velocidade média (85-95) tem melhor taxa (45.8%)
- Rápidos (95-105) têm PIOR taxa (41.4%)
- Muito rápidos (>105) recuperam para 44.0%

**Correlação Velocidade-Defesa:** -0.010 (quase zero!)

---

## ⏱️ EVOLUÇÃO TEMPORAL (FADIGA?)

### Taxa de Defesa por Fase

| Fase | Minutos | Lances | Taxa Defesa | Vel. Média | Dist. Média |
|------|---------|--------|-------------|------------|-------------|
| Início | 0-15 | 404 | 45.0% | 101.3 km/h | 8.2m |
| Meio 1ª Parte | 16-30 | 385 | **40.5%** ⚠️ | 100.7 km/h | 8.1m |
| Meio 2ª Parte | 31-45 | 420 | **49.3%** ⭐ | 102.0 km/h | 8.0m |
| Final | 46-60 | 413 | **39.5%** ⚠️ | 101.7 km/h | 8.2m |

**🔥 PICO ANÓMALO IDENTIFICADO:**
- Minutos 31-45 têm **49.3%** de taxa de defesa
- **+8.8pp** vs Meio 1ª Parte (40.5%)
- **+9.8pp** vs Final (39.5%)

**Possíveis Explicações:**
1. **Táticas adversárias:** Mais conservadores quando empatados
2. **Foco pós-intervalo:** GRs mais concentrados após pausa
3. **Qualidade dos lances:** Menos remates de alta qualidade nessa fase
4. **Artefacto estatístico:** Amostra pequena (420 lances)

**Correlação Minuto-Defesa:** -0.033 (negativa mas quase zero!)

---

## 🔗 ANÁLISE DE CORRELAÇÕES

### Correlações com Probabilidade de Defesa

| Feature | Correlação | Interpretação |
|---------|------------|---------------|
| **Minuto do jogo** | **-0.033** | Quase zero → não afeta |
| Diferença de golos | -0.024 | Quase zero |
| Distância | -0.022 | Quase zero |
| Velocidade | -0.010 | Quase zero |

**💡 CONCLUSÃO IMPORTANTE:**
- **Nenhuma feature isolada** tem correlação forte (todas < 0.05)
- Modelo ML precisa capturar **interações complexas**
- Combinação de múltiplas variáveis é essencial
- Justifica uso de **ensemble models** (H2O AutoML)

---

## ⚔️ PERFORMANCE VS ADVERSÁRIOS

### TOP 5 Adversários (Melhor Taxa Defesa)

| Posição | Adversário | Jogos | Remates | Taxa Defesa |
|---------|-----------|-------|---------|-------------|
| 1º | Farense | 2 | 113 | 50.4% |
| 2º | Avanca | 2 | 124 | 48.4% |
| 3º | Póvoa | 2 | 119 | 46.2% |
| 4º | SC Braga | 2 | 111 | 45.9% |
| 5º | Águas Santas | 2 | 98 | 45.9% |

**Nota:** Apenas 2 jogos por adversário → variância alta

---

## 📊 ESTATÍSTICAS DESCRITIVAS COMPLETAS

### Lances (1.622 registos)

| Métrica | Distância (m) | Velocidade (km/h) | Minuto |
|---------|---------------|-------------------|--------|
| **Média** | 8.1 | 101.4 | 30.6 |
| **Desvio Padrão** | 1.3 | 9.5 | 17.3 |
| **Mínimo** | 6.0 | 85.0 | 1 |
| **25%** | 7.0 | 93.5 | 16 |
| **Mediana (50%)** | 8.1 | 101.4 | 31 |
| **75%** | 9.2 | 109.5 | 46 |
| **Máximo** | 11.0 | 118.0 | 60 |

**Distribuição equilibrada** ao longo dos 60 minutos!

---

## 💡 PRINCIPAIS INSIGHTS

### 🎯 Insights Positivos

1. **Zona Centro-Meio dominante** → 63.5% taxa de defesa (33.5pp acima do pior)
2. **GRs bem balanceados** → diferença apenas 2.9pp entre melhor e pior
3. **Dataset robusto** → 1.622 lances bem distribuídos
4. **Variabilidade adequada** → boa cobertura de distâncias/velocidades/fases

### ⚠️ Desafios Identificados

1. **Discrepância época vs lances** → 59-62% vs 43.6% (possível mistura treino/jogo)
2. **Pico anómalo 31-45min** → +9pp vs outras fases (difícil de explicar)
3. **Correlações baixas** → features individuais não são preditivas
4. **Amostra pequena** → apenas 30 jogos (alta variância)
5. **Padrões não-lineares** → distância/velocidade têm efeitos irregulares

### 🔬 Para o Modelo Preditivo

**Features mais importantes:**
1. **Zona da baliza** → variação de 30-63% (33pp)
2. **Fase do jogo** → variação de 40-49% (9pp)
3. **Características do GR** → altura, envergadura, vel. lateral
4. Distância/velocidade (efeito combinado, não linear)

**Features menos importantes:**
- Minuto exato (correlação -0.033)
- Diferença de golos (-0.024)

**Recomendações:**
1. Usar **fase categórica** (início/meio1/meio2/final) em vez de minuto
2. Combinar zona + fase + características GR
3. Testar **interações** entre features
4. Considerar **não-linearidades** (árvores, GBM)
5. Validar com **split temporal** (últimos jogos como teste)

---

## ⚠️ LIMITAÇÕES DO ESTUDO

1. **Amostra reduzida:** Apenas 30 jogos → alta variância estatística
2. **Possível viés:** Mistura de dados treino/jogo (taxa 43% vs 59%)
3. **Adversários:** Apenas 2 jogos por equipa → difícil generalizar
4. **Temporal:** Dados de 1 época → sem validação longitudinal
5. **Contexto:** Falta variáveis importantes (posicionamento defensivo, tipo de ataque)
6. **Causalidade:** Correlações não implicam causalidade

---

## ✅ CONCLUSÕES FINAIS

### Para a Tese

1. **Dataset viável** para prototipagem e demonstração de conceito
2. **Padrões identificáveis** (zona, fase) justificam uso de ML
3. **Limitações conhecidas** e documentadas (transparência académica)
4. **Modelo V3** (fases categóricas) alinhado com insights dos dados

### Para os Stakeholders

1. **Zona centro-meio é ponto forte** → defender prioritariamente
2. **Cantos superiores são vulneráveis** → treino focado
3. **Performance estável** ao longo do jogo (exceto pico 31-45)
4. **GRs complementares** → escolher por adversário, não por "melhor absoluto"

### Próximos Passos

1. Coletar **mais dados** (objetivo: >100 jogos)
2. Separar **claramente** dados treino vs jogo
3. Adicionar **features contextuais** (tipo ataque, posicionamento)
4. Validar com **dados de época seguinte**
5. Integrar **feedback dos treinadores** para interpretação

---

**Análise realizada em:** Dezembro 2024  
**Ferramenta:** Python 3.12 + Pandas + SQLite  
**Dataset:** handball_dt.db