"""
MODELO 2 - H2O.AI: Compatibilidade GR vs Adversário
Prevê taxa de defesa de um GR contra adversário específico
"""

import h2o
from h2o.automl import H2OAutoML
import pandas as pd
import sqlite3
from datetime import datetime

print("="*60)
print("MODELO 2: COMPATIBILIDADE GR vs ADVERSÁRIO")
print("="*60)

# 1. INICIALIZAR H2O
print("\n1️⃣ Inicializando H2O...")
h2o.init(max_mem_size="4G")

# 2. CARREGAR DADOS DA BD
print("\n2️⃣ Carregando dados da base de dados...")

conn = sqlite3.connect('handball_dt.db')

# Query que junta compatibilidades + características GR + características adversário
query = """
SELECT 
    -- Características do GR
    gr.altura_cm,
    gr.envergadura_cm,
    gr.velocidade_lateral_ms,
    gr.alcance_vertical_cm,
    gr.agilidade_ttest_s,
    gr.anos_experiencia,
    
    -- Características do Adversário
    adv.ranking_liga,
    adv.media_golos_jogo,
    adv.velocidade_media_remate_kmh,
    adv.remates_zona_alta_perc,
    adv.remates_zona_media_perc,
    adv.remates_zona_baixa_perc,
    adv.eficacia_primeira_linha_perc,
    adv.eficacia_segunda_linha_perc,
    adv.transicoes_rapidas_jogo,
    
    -- Target: Taxa de defesa
    c.taxa_defesa_perc
    
FROM compatibilidades_gr_adversario c
JOIN guarda_redes gr ON c.guarda_redes_id = gr.id
JOIN adversarios adv ON c.adversario_id = adv.id
"""

df = pd.read_sql_query(query, conn)
conn.close()

print(f"   ✅ {len(df)} combinações GR-Adversário carregadas")
print(f"   📊 Taxa média: {df['taxa_defesa_perc'].mean():.1f}%")
print(f"   📊 Range: {df['taxa_defesa_perc'].min():.1f}% - {df['taxa_defesa_perc'].max():.1f}%")

# 3. VERIFICAR DADOS
print("\n3️⃣ Verificando qualidade dos dados...")

# Remover NaNs se houver
df_clean = df.dropna()
print(f"   ✅ {len(df_clean)} registos válidos (após limpeza)")

if len(df_clean) < 20:
    print("   ⚠️ AVISO: Poucos dados! Modelo pode ter baixa precisão.")

# 4. CONVERTER PARA H2O FRAME
print("\n4️⃣ Convertendo para H2O Frame...")
hf = h2o.H2OFrame(df_clean)

print("   ✅ Dados convertidos")

# 5. SPLIT TREINO/TESTE
print("\n5️⃣ Dividindo dados (70% treino, 30% teste)...")
train, test = hf.split_frame(ratios=[0.7], seed=42)

print(f"   ✅ Treino: {train.nrows} combinações")
print(f"   ✅ Teste: {test.nrows} combinações")

# 6. DEFINIR FEATURES E TARGET
features = [
    # GR
    'altura_cm',
    'envergadura_cm',
    'velocidade_lateral_ms',
    'alcance_vertical_cm',
    'agilidade_ttest_s',
    'anos_experiencia',
    # Adversário
    'ranking_liga',
    'media_golos_jogo',
    'velocidade_media_remate_kmh',
    'remates_zona_alta_perc',
    'remates_zona_media_perc',
    'remates_zona_baixa_perc',
    'eficacia_primeira_linha_perc',
    'eficacia_segunda_linha_perc',
    'transicoes_rapidas_jogo'
]

target = 'taxa_defesa_perc'

print(f"\n   📋 Features: {len(features)}")
print("      GR (6): altura, envergadura, velocidade, alcance, agilidade, experiência")
print("      Adversário (9): ranking, golos/jogo, velocidade, zonas, eficácia, transições")

# 7. TREINAR MODELO COM AutoML
print("\n6️⃣ Treinando modelo com H2O AutoML...")
print("   ⏳ Isto pode demorar 2-5 minutos...")

aml = H2OAutoML(
    max_models=10,
    max_runtime_secs=300,
    seed=42,
    sort_metric='RMSE'  # Regressão: minimizar erro
)

aml.train(
    x=features,
    y=target,
    training_frame=train
)

print("\n   ✅ Treino completo!")

# 8. AVALIAR MODELO
print("\n7️⃣ Avaliando modelo...")

# Leaderboard
lb = aml.leaderboard
print("\n   📊 Top 3 Modelos:")
print(lb.head(3))

# Melhor modelo
best_model = aml.leader

# Performance no teste
perf = best_model.model_performance(test)

print(f"\n   🎯 Performance no Teste:")
print(f"      RMSE: {perf.rmse():.2f}%")
print(f"      MAE: {perf.mae():.2f}%")
print(f"      R²: {perf.r2():.3f}")

# 9. IMPORTÂNCIA DAS FEATURES
print("\n8️⃣ Importância das Features:")
varimp = best_model.varimp(use_pandas=True)
print(varimp.head(10))

# 10. GUARDAR MODELO
print("\n9️⃣ Guardando modelo...")

model_path = h2o.save_model(
    model=best_model,
    path="./models",
    force=True
)

print(f"   ✅ Modelo guardado em: {model_path}")

# 11. TESTE DE PREDIÇÃO
print("\n🔟 Teste de Predição:")

# Exemplo: Humberto Gomes vs FC Porto
exemplo = h2o.H2OFrame({
    # GR: Humberto
    'altura_cm': [185],
    'envergadura_cm': [190],
    'velocidade_lateral_ms': [4.2],
    'alcance_vertical_cm': [75],
    'agilidade_ttest_s': [9.5],
    'anos_experiencia': [5],
    # Adversário: FC Porto (forte)
    'ranking_liga': [1],
    'media_golos_jogo': [32.5],
    'velocidade_media_remate_kmh': [105],
    'remates_zona_alta_perc': [35],
    'remates_zona_media_perc': [40],
    'remates_zona_baixa_perc': [25],
    'eficacia_primeira_linha_perc': [70],
    'eficacia_segunda_linha_perc': [55],
    'transicoes_rapidas_jogo': [22]
})

pred = best_model.predict(exemplo)
taxa_compatibilidade = pred[0, 0]

print(f"\n   📊 Exemplo: Humberto Gomes vs FC Porto")
print(f"   🎯 PREDIÇÃO: {taxa_compatibilidade:.1f}% taxa de defesa esperada")

# 12. GUARDAR METADADOS
print("\n1️⃣1️⃣ Guardando metadados...")

metadata = {
    'model_path': model_path,
    'rmse': perf.rmse(),
    'mae': perf.mae(),
    'r2': perf.r2(),
    'features': features,
    'trained_date': datetime.now().isoformat(),
    'n_train': train.nrows,
    'n_test': test.nrows,
    'taxa_media': float(df_clean['taxa_defesa_perc'].mean()),
    'taxa_std': float(df_clean['taxa_defesa_perc'].std())
}

import json
with open('models/modelo_compatibilidade_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("   ✅ Metadados guardados")

# 13. SHUTDOWN H2O
print("\n" + "="*60)
print("✅ TREINO COMPLETO!")
print("="*60)
print(f"""
📊 RESULTADOS:
   • Modelo: {best_model.model_id}
   • RMSE: {perf.rmse():.2f}%
   • MAE: {perf.mae():.2f}%
   • R²: {perf.r2():.3f}
   • Path: {model_path}

🎯 INTERPRETAÇÃO:
   • RMSE ~{perf.rmse():.0f}%: Erro médio das predições
   • R² {perf.r2():.2f}: Modelo explica {perf.r2()*100:.0f}% da variação
   
💡 PRÓXIMOS PASSOS:
   1. Use predictor_compatibilidade.py para predições
   2. Integre no dashboard Pre_Jogo.py
   3. Compare predições vs dados históricos!
""")

h2o.cluster().shutdown(prompt=False)
print("\n✅ H2O desligado. Processo concluído!")