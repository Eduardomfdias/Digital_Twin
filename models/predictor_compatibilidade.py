"""
PREDICTOR - Modelo de Compatibilidade GR vs Adversário
Classe para prever taxa de defesa de um GR contra adversário específico
"""

import h2o
import json
import os
from pathlib import Path


class CompatibilidadePredictor:
    """
    Preditor de compatibilidade GR vs Adversário usando H2O.ai
    
    Uso:
        predictor = CompatibilidadePredictor()
        taxa = predictor.predict(
            # GR
            altura_gr=185, envergadura_gr=190, velocidade_gr=4.2,
            alcance_gr=75, agilidade_gr=9.5, experiencia_gr=5,
            # Adversário
            ranking_adv=1, golos_jogo_adv=32.5, vel_remate_adv=105,
            zona_alta_adv=35, zona_media_adv=40, zona_baixa_adv=25,
            efic_1linha_adv=70, efic_2linha_adv=55, transicoes_adv=22
        )
        print(f"Taxa de defesa prevista: {taxa}%")
    """
    
    def __init__(self, model_dir='.'):
        """Inicializa predictor e carrega modelo"""
        self.model_dir = Path(model_dir)
        self.model = None
        self.metadata = None
        self.h2o_started = False
        
        # Carregar metadados
        metadata_path = self.model_dir / 'modelo_compatibilidade_metadata.json'
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
                print(f"✅ Modelo carregado: RMSE={self.metadata.get('rmse', 'N/A'):.2f}%")
            else:
                raise FileNotFoundError(f"Modelo não encontrado em: {model_path}")
        else:
            raise FileNotFoundError("Metadados não encontrados. Execute train_modelo_compatibilidade.py primeiro!")
    
    def predict(self, altura_gr, envergadura_gr, velocidade_gr, alcance_gr, 
                agilidade_gr, experiencia_gr, ranking_adv, golos_jogo_adv,
                vel_remate_adv, zona_alta_adv, zona_media_adv, zona_baixa_adv,
                efic_1linha_adv, efic_2linha_adv, transicoes_adv):
        """
        Prevê taxa de defesa de um GR contra um adversário
        
        Args GR:
            altura_gr (int): Altura em cm
            envergadura_gr (int): Envergadura em cm
            velocidade_gr (float): Velocidade lateral em m/s
            alcance_gr (int): Alcance vertical em cm
            agilidade_gr (float): Tempo T-test em segundos
            experiencia_gr (int): Anos de experiência
        
        Args Adversário:
            ranking_adv (int): Posição no ranking (1-14)
            golos_jogo_adv (float): Média golos por jogo
            vel_remate_adv (int): Velocidade média remate em km/h
            zona_alta_adv (int): % remates zona alta
            zona_media_adv (int): % remates zona média
            zona_baixa_adv (int): % remates zona baixa
            efic_1linha_adv (int): % eficácia 1ª linha
            efic_2linha_adv (int): % eficácia 2ª linha
            transicoes_adv (int): Transições rápidas por jogo
        
        Returns:
            float: Taxa de defesa prevista (0-100%)
        """
        
        if self.model is None:
            raise RuntimeError("Modelo não carregado!")
        
        # Criar H2OFrame com as características
        combinacao = h2o.H2OFrame({
            'altura_cm': [int(altura_gr)],
            'envergadura_cm': [int(envergadura_gr)],
            'velocidade_lateral_ms': [float(velocidade_gr)],
            'alcance_vertical_cm': [int(alcance_gr)],
            'agilidade_ttest_s': [float(agilidade_gr)],
            'anos_experiencia': [int(experiencia_gr)],
            'ranking_liga': [int(ranking_adv)],
            'media_golos_jogo': [float(golos_jogo_adv)],
            'velocidade_media_remate_kmh': [int(vel_remate_adv)],
            'remates_zona_alta_perc': [int(zona_alta_adv)],
            'remates_zona_media_perc': [int(zona_media_adv)],
            'remates_zona_baixa_perc': [int(zona_baixa_adv)],
            'eficacia_primeira_linha_perc': [int(efic_1linha_adv)],
            'eficacia_segunda_linha_perc': [int(efic_2linha_adv)],
            'transicoes_rapidas_jogo': [int(transicoes_adv)]
        })
        
        # Fazer predição
        pred = self.model.predict(combinacao)
        
        taxa_defesa = pred[0, 0]
        
        return round(taxa_defesa, 1)
    
    def predict_from_dataframes(self, gr_row, adv_row):
        """
        Versão simplificada: recebe Series do pandas com dados do GR e adversário
        
        Args:
            gr_row (pd.Series): Dados do GR
            adv_row (pd.Series): Dados do adversário
        
        Returns:
            float: Taxa de defesa prevista
        """
        return self.predict(
            altura_gr=gr_row['altura_cm'],
            envergadura_gr=gr_row['envergadura_cm'],
            velocidade_gr=gr_row['velocidade_lateral_ms'],
            alcance_gr=gr_row['alcance_vertical_cm'],
            agilidade_gr=gr_row['agilidade_ttest_s'],
            experiencia_gr=gr_row['anos_experiencia'],
            ranking_adv=adv_row['ranking_liga'],
            golos_jogo_adv=adv_row['media_golos_jogo'],
            vel_remate_adv=adv_row['velocidade_media_remate_kmh'],
            zona_alta_adv=adv_row['remates_zona_alta_perc'],
            zona_media_adv=adv_row['remates_zona_media_perc'],
            zona_baixa_adv=adv_row['remates_zona_baixa_perc'],
            efic_1linha_adv=adv_row['eficacia_primeira_linha_perc'],
            efic_2linha_adv=adv_row['eficacia_segunda_linha_perc'],
            transicoes_adv=adv_row['transicoes_rapidas_jogo']
        )
    
    def get_model_info(self):
        """Retorna informações sobre o modelo"""
        if self.metadata:
            return {
                'RMSE': f"{self.metadata.get('rmse', 'N/A'):.2f}%",
                'MAE': f"{self.metadata.get('mae', 'N/A'):.2f}%",
                'R²': f"{self.metadata.get('r2', 'N/A'):.3f}",
                'Data Treino': self.metadata.get('trained_date', 'N/A'),
                'N Treino': self.metadata.get('n_train', 'N/A'),
                'N Teste': self.metadata.get('n_test', 'N/A'),
                'Taxa Média': f"{self.metadata.get('taxa_media', 'N/A'):.1f}%"
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
    print("TESTE DO PREDICTOR DE COMPATIBILIDADE")
    print("="*60)
    
    # Inicializar predictor
    predictor = CompatibilidadePredictor()
    
    # Info do modelo
    print("\n📊 Informações do Modelo:")
    for k, v in predictor.get_model_info().items():
        print(f"   {k}: {v}")
    
    # Teste 1: Humberto vs FC Porto (forte)
    print("\n🎯 TESTE 1: Humberto Gomes vs FC Porto")
    taxa1 = predictor.predict(
        # GR: Humberto (bom)
        altura_gr=185, envergadura_gr=190, velocidade_gr=4.2,
        alcance_gr=75, agilidade_gr=9.5, experiencia_gr=5,
        # Adversário: FC Porto (muito forte)
        ranking_adv=1, golos_jogo_adv=32.5, vel_remate_adv=105,
        zona_alta_adv=35, zona_media_adv=40, zona_baixa_adv=25,
        efic_1linha_adv=70, efic_2linha_adv=55, transicoes_adv=22
    )
    print(f"   Taxa de defesa prevista: {taxa1}%")
    
    # Teste 2: Diogo vs Farense (fraco)
    print("\n🎯 TESTE 2: Diogo Ribeiro vs Farense")
    taxa2 = predictor.predict(
        # GR: Diogo (médio)
        altura_gr=186, envergadura_gr=192, velocidade_gr=4.0,
        alcance_gr=72, agilidade_gr=10.2, experiencia_gr=3,
        # Adversário: Farense (fraco)
        ranking_adv=14, golos_jogo_adv=22.0, vel_remate_adv=88,
        zona_alta_adv=30, zona_media_adv=35, zona_baixa_adv=35,
        efic_1linha_adv=50, efic_2linha_adv=40, transicoes_adv=12
    )
    print(f"   Taxa de defesa prevista: {taxa2}%")
    
    # Teste 3: Tiago vs SL Benfica (forte)
    print("\n🎯 TESTE 3: Tiago Ferreira vs SL Benfica")
    taxa3 = predictor.predict(
        # GR: Tiago (alto mas inexperiente)
        altura_gr=191, envergadura_gr=195, velocidade_gr=3.8,
        alcance_gr=78, agilidade_gr=10.8, experiencia_gr=2,
        # Adversário: Benfica (forte)
        ranking_adv=2, golos_jogo_adv=31.0, vel_remate_adv=102,
        zona_alta_adv=40, zona_media_adv=35, zona_baixa_adv=25,
        efic_1linha_adv=68, efic_2linha_adv=52, transicoes_adv=20
    )
    print(f"   Taxa de defesa prevista: {taxa3}%")
    
    print("\n✅ Testes concluídos!")
    
    # Shutdown
    predictor.shutdown()