"""
MODELO DEFESA V2 - Corrigido para FADIGA realista
Testa 3 abordagens para feature temporal
"""

import h2o
from h2o.automl import H2OAutoML
import pandas as pd
import sqlite3
from datetime import datetime
import json

print("="*70)
print("RETREINO MODELO - 3 VERSÕES PARA COMPARAR")
print("="*70)

# Inicializar H2O
h2o.init(max_mem_size="4G")

# Carregar dados
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

print(f"\n✅ {len(df)} lances carregados")

# =============================================================================
# VERSÃO 1: SEM feature temporal (baseline)
# =============================================================================
print("\n" + "="*70)
print("VERSÃO 1: SEM minuto_jogo (baseline)")
print("="*70)

df_v1 = df.copy()

hf_v1 = h2o.H2OFrame(df_v1)
hf_v1['defesa'] = hf_v1['defesa'].asfactor()

train_v1, test_v1 = hf_v1.split_frame(ratios=[0.8], seed=42)

features_v1 = [
    'zona_baliza_id',
    'distancia_remate_m', 
    'velocidade_remate_kmh',
    # SEM minuto_jogo
    'diferenca_golos_momento',
    'altura_cm',
    'envergadura_cm',
    'velocidade_lateral_ms'
]

aml_v1 = H2OAutoML(
    max_models=10,
    max_runtime_secs=180,
    seed=42,
    balance_classes=True,
    sort_metric='AUC'
)

aml_v1.train(x=features_v1, y='defesa', training_frame=train_v1)

perf_v1 = aml_v1.leader.model_performance(test_v1)
print(f"\n✅ V1 - AUC: {perf_v1.auc():.3f} | Accuracy: {perf_v1.accuracy()[0][1]:.3f}")

# =============================================================================
# VERSÃO 2: Com FADIGA explícita (linear)
# =============================================================================
print("\n" + "="*70)
print("VERSÃO 2: Com feature FADIGA (0-1 linear)")
print("="*70)

df_v2 = df.copy()
# Fadiga cresce linearmente com o tempo
df_v2['fadiga'] = df_v2['minuto_jogo'] / 60.0  # 0.0 no início, 1.0 aos 60min

hf_v2 = h2o.H2OFrame(df_v2)
hf_v2['defesa'] = hf_v2['defesa'].asfactor()

train_v2, test_v2 = hf_v2.split_frame(ratios=[0.8], seed=42)

features_v2 = [
    'zona_baliza_id',
    'distancia_remate_m', 
    'velocidade_remate_kmh',
    'fadiga',  # NOVA feature
    'diferenca_golos_momento',
    'altura_cm',
    'envergadura_cm',
    'velocidade_lateral_ms'
]

aml_v2 = H2OAutoML(
    max_models=10,
    max_runtime_secs=180,
    seed=42,
    balance_classes=True,
    sort_metric='AUC'
)

aml_v2.train(x=features_v2, y='defesa', training_frame=train_v2)

perf_v2 = aml_v2.leader.model_performance(test_v2)
print(f"\n✅ V2 - AUC: {perf_v2.auc():.3f} | Accuracy: {perf_v2.accuracy()[0][1]:.3f}")

# =============================================================================
# VERSÃO 3: Com FASE do jogo (categórica)
# =============================================================================
print("\n" + "="*70)
print("VERSÃO 3: Com FASE_JOGO categórica")
print("="*70)

df_v3 = df.copy()
# Fase categórica
df_v3['fase_jogo'] = pd.cut(
    df_v3['minuto_jogo'], 
    bins=[0, 15, 30, 45, 60],
    labels=['inicio', 'meio_1', 'meio_2', 'final']
)

hf_v3 = h2o.H2OFrame(df_v3)
hf_v3['defesa'] = hf_v3['defesa'].asfactor()
hf_v3['fase_jogo'] = hf_v3['fase_jogo'].asfactor()

train_v3, test_v3 = hf_v3.split_frame(ratios=[0.8], seed=42)

features_v3 = [
    'zona_baliza_id',
    'distancia_remate_m', 
    'velocidade_remate_kmh',
    'fase_jogo',  # NOVA feature categórica
    'diferenca_golos_momento',
    'altura_cm',
    'envergadura_cm',
    'velocidade_lateral_ms'
]

aml_v3 = H2OAutoML(
    max_models=10,
    max_runtime_secs=180,
    seed=42,
    balance_classes=True,
    sort_metric='AUC'
)

aml_v3.train(x=features_v3, y='defesa', training_frame=train_v3)

perf_v3 = aml_v3.leader.model_performance(test_v3)
print(f"\n✅ V3 - AUC: {perf_v3.auc():.3f} | Accuracy: {perf_v3.accuracy()[0][1]:.3f}")

# =============================================================================
# COMPARAÇÃO FINAL
# =============================================================================
print("\n" + "="*70)
print("📊 COMPARAÇÃO FINAL")
print("="*70)

print("\n┌─────────────┬────────┬──────────┬─────────────┐")
print("│   Versão    │  AUC   │ Accuracy │   Feature   │")
print("├─────────────┼────────┼──────────┼─────────────┤")
print(f"│ V1 Baseline │ {perf_v1.auc():.3f}  │  {perf_v1.accuracy()[0][1]:.3f}   │ SEM tempo   │")
print(f"│ V2 Fadiga   │ {perf_v2.auc():.3f}  │  {perf_v2.accuracy()[0][1]:.3f}   │ fadiga 0-1  │")
print(f"│ V3 Fase     │ {perf_v3.auc():.3f}  │  {perf_v3.accuracy()[0][1]:.3f}   │ fase categ. │")
print("└─────────────┴────────┴──────────┴─────────────┘")

# Escolher melhor
aucs = {
    'v1': perf_v1.auc(),
    'v2': perf_v2.auc(),
    'v3': perf_v3.auc()
}

melhor = max(aucs, key=aucs.get)
print(f"\n🏆 VENCEDOR: {melhor.upper()} (AUC = {aucs[melhor]:.3f})")

# Guardar o melhor
if melhor == 'v1':
    model = aml_v1.leader
    features = features_v1
    metadata_extra = {'temporal_feature': 'none'}
elif melhor == 'v2':
    model = aml_v2.leader
    features = features_v2
    metadata_extra = {'temporal_feature': 'fadiga', 'fadiga_formula': 'minuto/60'}
else:
    model = aml_v3.leader
    features = features_v3
    metadata_extra = {'temporal_feature': 'fase_jogo', 'fases': '0-15,16-30,31-45,46-60'}

# Guardar modelo
model_path = h2o.save_model(model=model, path="./models", force=True)

# Metadados
metadata = {
    'model_path': model_path,
    'auc': aucs[melhor],
    'accuracy': perf_v1.accuracy()[0][1] if melhor=='v1' else perf_v2.accuracy()[0][1] if melhor=='v2' else perf_v3.accuracy()[0][1],
    'features': features,
    'trained_date': datetime.now().isoformat(),
    'n_train': train_v1.nrows,
    'n_test': test_v1.nrows,
    'version': melhor,
    **metadata_extra
}

with open('models/modelo_defesa_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n✅ Modelo {melhor.upper()} guardado!")
print(f"   Path: {model_path}")

# =============================================================================
# TESTE DE FADIGA
# =============================================================================
print("\n" + "="*70)
print("🧪 TESTE: Efeito da FADIGA na predição")
print("="*70)

if melhor == 'v2':
    # Testar MESMO lance em diferentes momentos
    for minuto in [10, 30, 50]:
        fadiga = minuto / 60.0
        
        exemplo = h2o.H2OFrame({
            'zona_baliza_id': [5],
            'distancia_remate_m': [9.0],
            'velocidade_remate_kmh': [95.0],
            'fadiga': [fadiga],
            'diferenca_golos_momento': [0],
            'altura_cm': [185],
            'envergadura_cm': [190],
            'velocidade_lateral_ms': [4.2]
        })
        
        pred = model.predict(exemplo)
        prob = pred['p1'][0, 0] * 100
        
        print(f"\n   Min {minuto:2d} (fadiga={fadiga:.2f}): {prob:.1f}% defesa")
    
    print("\n   ✅ Se a probabilidade DIMINUI com o tempo → fadiga funciona!")
    
elif melhor == 'v3':
    # Testar com diferentes fases
    for fase in ['inicio', 'meio_1', 'meio_2', 'final']:
        exemplo = h2o.H2OFrame({
            'zona_baliza_id': [5],
            'distancia_remate_m': [9.0],
            'velocidade_remate_kmh': [95.0],
            'fase_jogo': [fase],
            'diferenca_golos_momento': [0],
            'altura_cm': [185],
            'envergadura_cm': [190],
            'velocidade_lateral_ms': [4.2]
        })
        
        pred = model.predict(exemplo)
        prob = pred['p1'][0, 0] * 100
        
        print(f"\n   Fase {fase:7s}: {prob:.1f}% defesa")

else:
    print("\n   ℹ️ Modelo V1 não usa tempo - probabilidade é sempre igual")

# Shutdown
h2o.cluster().shutdown(prompt=False)

print("\n" + "="*70)
print("✅ ANÁLISE COMPLETA!")
print("="*70)
print(f"""
📋 RECOMENDAÇÃO:
   Usa o modelo {melhor.upper()} que tem melhor AUC.
   
   Atualiza o predictor_defesa.py para usar as novas features:
   {features}
""")