"""
MODELO 1 - H2O.AI: Probabilidade de Defesa por Lance
Treina modelo preditivo para Dashboard de Timeout
"""

import h2o
from h2o.automl import H2OAutoML
import pandas as pd
import sqlite3
from datetime import datetime

print("="*60)
print("TREINO MODELO H2O.AI - PROBABILIDADE DE DEFESA")
print("="*60)

# 1. INICIALIZAR H2O
print("\n1️⃣ Inicializando H2O...")
h2o.init(max_mem_size="4G")

# 2. CARREGAR DADOS DA BD
print("\n2️⃣ Carregando dados da base de dados...")

conn = sqlite3.connect('handball_dt.db')

query = """
SELECT 
    l.zona_baliza_id,
    l.distancia_remate_m,
    l.velocidade_remate_kmh,
    l.minuto_jogo,
    l.diferenca_golos_momento,
    gr.altura_cm,
    gr.envergadura_cm,
    gr.velocidade_lateral_ms,
    CASE WHEN l.resultado = 'Defesa' THEN 1 ELSE 0 END as defesa
FROM lances l
JOIN jogos j ON l.jogo_id = j.id
JOIN guarda_redes gr ON j.guarda_redes_id = gr.id
"""

df = pd.read_sql_query(query, conn)
conn.close()

print(f"   ✅ {len(df)} lances carregados")
print(f"   📊 Distribuição: {df['defesa'].sum()} defesas, {len(df) - df['defesa'].sum()} golos")

# 3. CONVERTER PARA H2O FRAME
print("\n3️⃣ Convertendo para H2O Frame...")
hf = h2o.H2OFrame(df)

# Definir target como categórico (classificação)
hf['defesa'] = hf['defesa'].asfactor()

print("   ✅ Dados convertidos")

# 4. SPLIT TREINO/TESTE
print("\n4️⃣ Dividindo dados (80% treino, 20% teste)...")
train, test = hf.split_frame(ratios=[0.8], seed=42)

print(f"   ✅ Treino: {train.nrows} linhas")
print(f"   ✅ Teste: {test.nrows} linhas")

# 5. DEFINIR FEATURES E TARGET
features = [
    'zona_baliza_id',
    'distancia_remate_m', 
    'velocidade_remate_kmh',
    'minuto_jogo',
    'diferenca_golos_momento',
    'altura_cm',
    'envergadura_cm',
    'velocidade_lateral_ms'
]

target = 'defesa'

print(f"\n   📋 Features: {len(features)}")
for f in features:
    print(f"      - {f}")

# 6. TREINAR MODELO COM AutoML
print("\n5️⃣ Treinando modelo com H2O AutoML...")
print("   ⏳ Isto pode demorar 2-5 minutos...")

aml = H2OAutoML(
    max_models=10,              # Treinar até 10 modelos
    max_runtime_secs=300,       # Máximo 5 minutos
    seed=42,
    balance_classes=True,       # Balancear defesas/golos
    sort_metric='AUC'           # Ordenar por AUC
)

aml.train(
    x=features,
    y=target,
    training_frame=train
)

print("\n   ✅ Treino completo!")

# 7. AVALIAR MODELO
print("\n6️⃣ Avaliando modelo...")

# Leaderboard
lb = aml.leaderboard
print("\n   📊 Top 3 Modelos:")
print(lb.head(3))

# Melhor modelo
best_model = aml.leader

# Performance no teste
perf = best_model.model_performance(test)

print(f"\n   🎯 Performance no Teste:")
print(f"      AUC: {perf.auc():.3f}")
print(f"      Accuracy: {perf.accuracy()[0][1]:.3f}")
print(f"      Logloss: {perf.logloss():.3f}")

# Confusion Matrix
cm = perf.confusion_matrix()
print(f"\n   📋 Confusion Matrix:")
print(cm)

# 8. IMPORTÂNCIA DAS FEATURES
print("\n7️⃣ Importância das Features:")
varimp = best_model.varimp(use_pandas=True)
print(varimp.head(10))

# 9. GUARDAR MODELO
print("\n8️⃣ Guardando modelo...")

model_path = h2o.save_model(
    model=best_model,
    path="./models",
    force=True
)

print(f"   ✅ Modelo guardado em: {model_path}")

# 10. TESTE DE PREDIÇÃO
print("\n9️⃣ Teste de Predição:")

# Criar exemplo de lance
exemplo = h2o.H2OFrame({
    'zona_baliza_id': [5],                  # Centro
    'distancia_remate_m': [9.0],            # 9 metros
    'velocidade_remate_kmh': [95.0],        # 95 km/h
    'minuto_jogo': [42],                    # Min 42
    'diferenca_golos_momento': [0],         # Empate
    'altura_cm': [185],                     # Humberto
    'envergadura_cm': [190],
    'velocidade_lateral_ms': [4.2]
})

pred = best_model.predict(exemplo)
prob_defesa = pred['p1'][0, 0] * 100  # Probabilidade de defesa (classe 1)

print(f"\n   📊 Exemplo de Lance:")
print(f"      Zona: Centro (5)")
print(f"      Distância: 9m")
print(f"      Velocidade: 95 km/h")
print(f"      GR: Humberto Gomes (185cm)")
print(f"\n   🎯 PREDIÇÃO: {prob_defesa:.1f}% probabilidade de DEFESA")

# 11. GUARDAR METADADOS
print("\n🔟 Guardando metadados...")

metadata = {
    'model_path': model_path,
    'auc': perf.auc(),
    'accuracy': perf.accuracy()[0][1],
    'features': features,
    'trained_date': datetime.now().isoformat(),
    'n_train': train.nrows,
    'n_test': test.nrows
}

import json
with open('models/modelo_defesa_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("   ✅ Metadados guardados")

# 12. SHUTDOWN H2O
print("\n" + "="*60)
print("✅ TREINO COMPLETO!")
print("="*60)
print(f"""
📊 RESULTADOS:
   • Modelo: {best_model.model_id}
   • AUC: {perf.auc():.3f}
   • Accuracy: {perf.accuracy()[0][1]:.1%}
   • Path: {model_path}

🎯 PRÓXIMOS PASSOS:
   1. Use predictor_defesa.py para fazer predições
   2. Integre no dashboard Timeout.py
   3. Teste com dados reais!
""")

h2o.cluster().shutdown(prompt=False)
print("\n✅ H2O desligado. Processo concluído!")