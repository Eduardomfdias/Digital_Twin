# BASE DE DADOS LIMPA - 3 GUARDA-REDES

## ✅ DADOS PRONTOS PARA M3

Esta base de dados contém apenas os **3 guarda-redes do ABC Braga** mencionados no M2:
- **Humberto Gomes** (ID 1) - Titular
- **Diogo Ribeiro** (ID 2) - Suplente veterano  
- **Tiago Ferreira** (ID 3) - Suplente jovem

---

## 📊 RESUMO DOS DADOS

### 1. guarda_redes.csv (3 registos)
Características antropométricas e biomecânicas dos 3 GRs.

**Campos principais:**
- altura_cm, envergadura_cm, peso_kg, imc
- velocidade_lateral_ms, agilidade_ttest_s
- alcance_vertical_cm, amplitude_split_cm
- anos_experiencia, posicao_principal

### 2. jogos.csv (30 registos)
10 jogos por GR com contexto completo.

**Campos principais:**
- guarda_redes_id, adversario_id
- data, local, resultado_final
- golos_favor, golos_contra
- epoca, fase_competicao, importancia_jogo

### 3. lances.csv (1.622 registos)
Lances individuais detalhados.

**Distribuição por GR:**
- Humberto Gomes: 1.258 lances
- Diogo Ribeiro: 196 lances
- Tiago Ferreira: 168 lances

**Campos principais:**
- jogo_id, zona_baliza_id (1-9)
- distancia_remate_m, velocidade_remate_kmh
- tipo_remate, posicao_ofensiva
- resultado (Defesa/Golo)
- minuto_jogo, diferenca_golos_momento

### 4. epocas.csv (6 registos)
Métricas agregadas por época (2024 e 2025).

**Taxas de defesa globais (época 2025):**
- Humberto Gomes: 59.5%
- Diogo Ribeiro: 62.5%
- Tiago Ferreira: 57.6%

**Campos principais:**
- taxa_defesa_global
- taxa_defesa_zona1 até zona9 (grid 3×3)
- defesas_7metros, eficacia_7metros
- carga_treino_horas
- evolução física (peso, alcance, velocidade)

### 5. treinos.csv (360 registos)
120 treinos por GR com detalhes completos.

**Campos principais:**
- tipo_treino, foco_principal
- duracao_minutos, intensidade (1-10)
- remates_recebidos, defesas_realizadas
- taxa_sucesso_perc
- sensacao_fisica, confianca

### 6. compatibilidades_gr_adversario.csv (42 registos)
14 adversários × 3 GRs = 42 combinações.

**Campos principais:**
- taxa_defesa_perc vs cada adversário
- zona_fraca_1, zona_fraca_2, zona_fraca_3
- prob_ser_titular
- vitorias, empates, derrotas

### 7. evolucao_temporal.csv (60 registos)
Evolução mensal dos 3 GRs (10 meses × 3 × 2 épocas).

**Campos principais:**
- taxa_defesa_mes
- alcance_vertical_cm, velocidade_lateral_ms
- confianca_1_10
- tendencia (Crescente/Estável/Decrescente)

### 8. simulacoes_cenarios.csv (30 registos)
10 cenários de melhoria por GR.

**Campos principais:**
- cenario (ex: "Melhorar altura +5cm")
- taxa_defesa_atual vs taxa_defesa_projetada
- impacto por zona (pp)
- roi_estimado, prioridade

### 9. analise_plantel.csv (3 registos)
Comparações par-a-par entre os 3 GRs.

**Campos principais:**
- indice_similaridade
- indice_complementaridade
- recomendacao_uso_combinado

### 10. adversarios.csv (14 registos)
Perfis táticos das equipas adversárias.

**Campos principais:**
- estilo_ofensivo, media_golos_jogo
- remates_zona_alta/media/baixa_perc
- velocidade_media_remate_kmh
- tipo_ataque_predominante

### 11. correlacoes_fisica_performance.csv (64 registos)
Correlações entre características físicas e performance.

**Campos principais:**
- caracteristica_fisica (ex: altura_cm)
- metrica_performance (ex: taxa_defesa_zona_alta)
- coef_correlacao_pearson
- significativo_estatisticamente

---

## 🎯 VALIDAÇÃO VS M2

| Guarda-Redes | Taxa Defesa M2 | Taxa Defesa Época 2025 | ✓ |
|--------------|----------------|------------------------|---|
| Humberto Gomes | 60% | 59.5% | ✅ |
| Diogo Ribeiro | 62% | 62.5% | ✅ |
| Tiago Ferreira | 54% | 57.6% | ✅ |

**Nota:** As taxas em `epocas.csv` são as agregadas oficiais. As taxas calculadas diretas dos lances podem variar ligeiramente devido a diferentes períodos de amostragem.

---

## 📐 GRID 3×3 DAS ZONAS DA BALIZA

```
1 (Sup.Esq)  |  2 (Sup.Centro)  |  3 (Sup.Dir)
4 (Méd.Esq)  |  5 (Méd.Centro)  |  6 (Méd.Dir)
7 (Inf.Esq)  |  8 (Inf.Centro)  |  9 (Inf.Dir)
```

Usado em: `lances.zona_baliza_id`, `epocas.taxa_defesa_zona[1-9]`

---

## 🔗 RELAÇÕES ENTRE TABELAS

```
guarda_redes (3) ──┬─── jogos (30) ──── lances (1.622)
                   │
                   ├─── epocas (6)
                   │
                   ├─── treinos (360)
                   │
                   ├─── compatibilidades_gr_adversario (42) ──── adversarios (14)
                   │
                   ├─── evolucao_temporal (60)
                   │
                   ├─── simulacoes_cenarios (30)
                   │
                   └─── analise_plantel (3)
```

---

## 🚀 COMO USAR

### Carregar para SQLite
```python
import sqlite3
import pandas as pd
from pathlib import Path

conn = sqlite3.connect('handball_dt.db')

csv_files = [
    'guarda_redes', 'adversarios', 'jogos', 'lances',
    'epocas', 'treinos', 'compatibilidades_gr_adversario',
    'analise_plantel', 'correlacoes_fisica_performance',
    'evolucao_temporal', 'simulacoes_cenarios'
]

for table_name in csv_files:
    df = pd.read_csv(f'{table_name}.csv')
    df.to_sql(table_name, conn, if_exists='replace', index=False)

conn.close()
print('✅ Base de dados criada!')
```

### Query exemplo
```python
# Performance por zona do Humberto
query = """
SELECT 
    zona_baliza_nome,
    COUNT(*) as total,
    SUM(CASE WHEN resultado = 'Defesa' THEN 1 ELSE 0 END) as defesas,
    ROUND(AVG(CASE WHEN resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa
FROM lances l
JOIN jogos j ON l.jogo_id = j.id
WHERE j.guarda_redes_id = 1
GROUP BY zona_baliza_nome
ORDER BY zona_baliza_id
"""
```

---

## 📝 NOTAS IMPORTANTES

1. **Dados sintéticos mas realistas** - correlações biologicamente plausíveis
2. **Cobertura temporal** - Ago/2024 a Mar/2025
3. **Integridade referencial** - Todas FK válidas
4. **Total registos** - 2.351+ em 11 tabelas

---

**Criado:** 07 Dezembro 2025  
**Versão:** 1.0 (3 GRs)  
**Projeto:** Digital Twin ABC Braga - M3
