"""
Módulo de acesso à base de dados - Digital Twin ABC Braga
"""

import sqlite3
import pandas as pd
from typing import Optional

class HandballDataAccess:
    """Classe para acesso estruturado aos dados"""
    
    def __init__(self, db_path="handball_dt.db"):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_all_goalkeepers(self):
        """Retorna lista de todos os guarda-redes"""
        query = "SELECT id, nome, altura_cm, envergadura_cm, posicao_principal, velocidade_lateral_ms FROM guarda_redes"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)
    
    def get_zone_performance(self, gr_id: int, adversario_id: Optional[int] = None):
        """Performance por zona de um GR"""
        query = """
        SELECT 
            l.zona_baliza_id,
            l.zona_baliza_nome,
            COUNT(*) as total_remates,
            SUM(CASE WHEN l.resultado = 'Defesa' THEN 1 ELSE 0 END) as defesas,
            ROUND(AVG(CASE WHEN l.resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa_defesa
        FROM lances l
        JOIN jogos j ON l.jogo_id = j.id
        WHERE j.guarda_redes_id = ?
        """
        params = [gr_id]
        
        if adversario_id:
            query += " AND j.adversario_id = ?"
            params.append(adversario_id)
        
        query += " GROUP BY l.zona_baliza_id, l.zona_baliza_nome ORDER BY l.zona_baliza_id"
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def get_compatibility_matrix(self, adversario_id: int):
        """Matriz compatibilidade todos GRs vs adversário"""
        query = """
        SELECT 
            gr.nome,
            c.taxa_defesa_perc,
            c.prob_ser_titular,
            c.zona_fraca_1,
            c.zona_fraca_2
        FROM compatibilidades_gr_adversario c
        JOIN guarda_redes gr ON c.guarda_redes_id = gr.id
        WHERE c.adversario_id = ?
        ORDER BY c.taxa_defesa_perc DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(adversario_id,))
    
    def get_training_scenarios(self, gr_id: int, top_n: int = 5):
        """Top N cenários de treino por ROI"""
        query = """
        SELECT 
            cenario,
            taxa_defesa_projetada - taxa_defesa_atual as ganho_esperado,
            roi_estimado,
            tempo_resultados_semanas,
            prioridade
        FROM simulacoes_cenarios
        WHERE guarda_redes_id = ?
        ORDER BY roi_estimado DESC
        LIMIT ?
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(gr_id, top_n))
    
    def get_evolution(self, gr_id: int, last_n_months: int = 6):
        """Evolução temporal de um GR"""
        query = """
        SELECT 
            mes,
            taxa_defesa_mes,
            alcance_vertical_cm,
            velocidade_lateral_ms,
            confianca_1_10,
            tendencia
        FROM evolucao_temporal
        WHERE guarda_redes_id = ?
        ORDER BY id DESC
        LIMIT ?
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(gr_id, last_n_months))

# Exemplo de uso
if __name__ == "__main__":
    db = HandballDataAccess()
    
    print("Guarda-redes disponíveis:")
    print(db.get_all_goalkeepers())
    
    print("\nPerformance Humberto por zona:")
    print(db.get_zone_performance(gr_id=1))
    
    print("\nCompatibilidade vs FC Porto:")
    print(db.get_compatibility_matrix(adversario_id=1))
