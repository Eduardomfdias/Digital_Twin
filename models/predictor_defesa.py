"""
PREDICTOR - Modelo de Probabilidade de Defesa
Classe para fazer predições usando o modelo H2O.ai treinado
"""

import h2o
import json
import os
from pathlib import Path


class DefesaPredictor:
    """
    Preditor de probabilidade de defesa usando H2O.ai
    
    Uso:
        predictor = DefesaPredictor()
        prob = predictor.predict(
            zona=5, distancia=9, velocidade=95,
            altura_gr=185, envergadura_gr=190, vel_lateral_gr=4.2,
            minuto=42, diferenca_golos=0
        )
        print(f"Probabilidade de defesa: {prob}%")
    """
    
    def __init__(self, model_dir='.'):
        """Inicializa predictor e carrega modelo"""
        self.model_dir = Path(model_dir)
        self.model = None
        self.metadata = None
        self.h2o_started = False
        
        # Carregar metadados
        metadata_path = self.model_dir / 'modelo_defesa_metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        
        # Inicializar H2O e carregar modelo
        self._init_h2o()
        self._load_model()
    
    def _init_h2o(self):
        """Inicializa cluster H2O (se ainda não estiver)"""
        try:
            # Tenta conectar a cluster existente
            h2o.connect(verbose=False)
            self.h2o_started = False
            print("✅ Conectado a cluster H2O existente")
        except:
            # Inicia novo cluster
            try:
                h2o.init(max_mem_size="2G", verbose=False)
                self.h2o_started = True
                print("✅ Novo cluster H2O iniciado")
            except Exception as e:
                print(f"❌ Erro ao iniciar H2O: {e}")
                raise
    
    def _load_model(self):
        """Carrega modelo treinado"""
        if self.metadata and 'model_path' in self.metadata:
            model_path = self.metadata['model_path']
            if os.path.exists(model_path):
                self.model = h2o.load_model(model_path)
                print(f"✅ Modelo carregado: AUC={self.metadata.get('auc', 'N/A'):.3f}")
            else:
                raise FileNotFoundError(f"Modelo não encontrado em: {model_path}")
        else:
            raise FileNotFoundError("Metadados não encontrados. Execute train_modelo_defesa.py primeiro!")
    
    def predict(self, zona, distancia, velocidade, altura_gr, envergadura_gr, 
                vel_lateral_gr, minuto, diferenca_golos):
        """
        Prevê probabilidade de defesa para um lance
        
        Args:
            zona (int): ID da zona da baliza (1-9)
            distancia (float): Distância do remate em metros
            velocidade (float): Velocidade do remate em km/h
            altura_gr (int): Altura do GR em cm
            envergadura_gr (int): Envergadura do GR em cm
            vel_lateral_gr (float): Velocidade lateral do GR em m/s
            minuto (int): Minuto do jogo (0-60)
            diferenca_golos (int): Diferença de golos (positivo = a ganhar)
        
        Returns:
            float: Probabilidade de defesa (0-100%)
        """
        
        if self.model is None:
            raise RuntimeError("Modelo não carregado!")
        
        # Converter minuto para fase (modelo V3)
        if minuto <= 15:
            fase = 'inicio'
        elif minuto <= 30:
            fase = 'meio_1'
        elif minuto <= 45:
            fase = 'meio_2'
        else:
            fase = 'final'
        
        # Criar H2OFrame com o lance
        lance = h2o.H2OFrame({
            'zona_baliza_id': [int(zona)],
            'distancia_remate_m': [float(distancia)],
            'velocidade_remate_kmh': [float(velocidade)],
            'fase_jogo': [fase],  # MUDANÇA: fase em vez de minuto
            'diferenca_golos_momento': [int(diferenca_golos)],
            'altura_cm': [int(altura_gr)],
            'envergadura_cm': [int(envergadura_gr)],
            'velocidade_lateral_ms': [float(vel_lateral_gr)]
        })
        
        # Fazer fase categórica
        lance['fase_jogo'] = lance['fase_jogo'].asfactor()
        
        # Fazer predição
        pred = self.model.predict(lance)
        
        # p1 = probabilidade da classe 1 (defesa)
        prob_defesa = pred['p1'][0, 0] * 100
        
        return round(prob_defesa, 1)
    
    def predict_batch(self, lances_df):
        """
        Prevê probabilidade para múltiplos lances
        
        Args:
            lances_df (DataFrame): DataFrame com colunas:
                - zona_baliza_id
                - distancia_remate_m
                - velocidade_remate_kmh
                - minuto_jogo (será convertido para fase_jogo)
                - diferenca_golos_momento
                - altura_cm
                - envergadura_cm
                - velocidade_lateral_ms
        
        Returns:
            list: Lista de probabilidades (0-100%)
        """
        
        if self.model is None:
            raise RuntimeError("Modelo não carregado!")
        
        # Converter minuto para fase
        import pandas as pd
        df = lances_df.copy()
        df['fase_jogo'] = pd.cut(
            df['minuto_jogo'],
            bins=[0, 15, 30, 45, 60],
            labels=['inicio', 'meio_1', 'meio_2', 'final']
        )
        
        # Remover minuto_jogo (não é mais usado)
        df = df.drop('minuto_jogo', axis=1)
        
        # Converter para H2OFrame
        hf = h2o.H2OFrame(df)
        hf['fase_jogo'] = hf['fase_jogo'].asfactor()
        
        # Fazer predições
        preds = self.model.predict(hf)
        
        # Extrair probabilidades
        probs = [round(p * 100, 1) for p in preds['p1'].as_data_frame()['p1'].tolist()]
        
        return probs
    
    def get_model_info(self):
        """Retorna informações sobre o modelo"""
        if self.metadata:
            return {
                'AUC': self.metadata.get('auc', 'N/A'),
                'Accuracy': self.metadata.get('accuracy', 'N/A'),
                'Data Treino': self.metadata.get('trained_date', 'N/A'),
                'N Treino': self.metadata.get('n_train', 'N/A'),
                'N Teste': self.metadata.get('n_test', 'N/A')
            }
        return {}
    
    def shutdown(self):
        """Desliga cluster H2O (se foi iniciado por este predictor)"""
        if self.h2o_started:
            h2o.cluster().shutdown(prompt=False)
    
    def __del__(self):
        """Cleanup ao destruir objeto"""
        self.shutdown()


# EXEMPLO DE USO
if __name__ == "__main__":
    print("="*60)
    print("TESTE DO PREDICTOR DE DEFESA")
    print("="*60)
    
    # Inicializar predictor
    predictor = DefesaPredictor()
    
    # Info do modelo
    print("\n📊 Informações do Modelo:")
    for k, v in predictor.get_model_info().items():
        print(f"   {k}: {v}")
    
    # Teste 1: Lance fácil (zona central, perto, lento)
    print("\n🎯 TESTE 1: Lance Fácil")
    prob1 = predictor.predict(
        zona=8,                 # Inferior Centro
        distancia=6.5,          # 6.5m (perto)
        velocidade=70,          # 70 km/h (lento)
        altura_gr=185,
        envergadura_gr=190,
        vel_lateral_gr=4.2,
        minuto=10,
        diferenca_golos=2       # A ganhar
    )
    print(f"   Probabilidade de defesa: {prob1}%")
    
    # Teste 2: Lance difícil (canto superior, longe, rápido)
    print("\n🎯 TESTE 2: Lance Difícil")
    prob2 = predictor.predict(
        zona=1,                 # Superior Esquerdo
        distancia=11.5,         # 11.5m (longe)
        velocidade=110,         # 110 km/h (rápido!)
        altura_gr=185,
        envergadura_gr=190,
        vel_lateral_gr=4.2,
        minuto=55,
        diferenca_golos=-1      # A perder
    )
    print(f"   Probabilidade de defesa: {prob2}%")
    
    # Teste 3: Lance médio
    print("\n🎯 TESTE 3: Lance Médio")
    prob3 = predictor.predict(
        zona=5,                 # Centro
        distancia=9.0,          # 9m
        velocidade=95,          # 95 km/h
        altura_gr=185,
        envergadura_gr=190,
        vel_lateral_gr=4.2,
        minuto=30,
        diferenca_golos=0
    )
    print(f"   Probabilidade de defesa: {prob3}%")
    
    print("\n✅ Testes concluídos!")
    
    # Shutdown
    predictor.shutdown()