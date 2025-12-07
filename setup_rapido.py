#!/usr/bin/env python3
"""
SETUP AUTOMÁTICO - Digital Twin ABC Braga
Procura os CSVs automaticamente e cria a base de dados
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

print("="*60)
print("SETUP AUTOMÁTICO - DIGITAL TWIN ABC BRAGA")
print("="*60)

# Lista de pastas possíveis onde podem estar os CSVs
pastas_possiveis = [
    Path('data_clean'),
    Path('Dados'),
    Path('Digital_Twin/Dados'),
    Path('../Dados'),
    Path('./'),  # pasta atual
]

# Procurar CSVs automaticamente
csv_dir = None
print("\n🔍 A procurar CSVs...")

for pasta in pastas_possiveis:
    if pasta.exists():
        # Verificar se tem pelo menos 1 CSV
        csvs = list(pasta.glob('*.csv'))
        if len(csvs) > 0:
            print(f"✅ Encontrado! {len(csvs)} CSVs em: {pasta}")
            csv_dir = pasta
            break
        else:
            print(f"⚠️  Pasta {pasta} existe mas não tem CSVs")
    else:
        print(f"❌ Pasta {pasta} não existe")

if csv_dir is None:
    print("\n❌ ERRO: Não encontrei CSVs em nenhuma pasta!")
    print("\n💡 Solução:")
    print("   1. Extrai o ZIP dados_limpos_3GRs.zip")
    print("   2. Certifica-te que tens os 11 ficheiros CSV")
    print("   3. Executa este script novamente")
    sys.exit(1)

print(f"\n📁 A usar CSVs de: {csv_dir}")

# Lista de tabelas (ordem correta)
tabelas = [
    'guarda_redes',
    'adversarios', 
    'jogos',
    'lances',
    'epocas',
    'treinos',
    'compatibilidades_gr_adversario',
    'analise_plantel',
    'correlacoes_fisica_performance',
    'evolucao_temporal',
    'simulacoes_cenarios'
]

# 1. CRIAR BASE DE DADOS
print(f"\n1️⃣ Criando base de dados SQLite...")

conn = sqlite3.connect('handball_dt.db')

csvs_carregados = 0
csvs_falhados = 0

for tabela in tabelas:
    csv_file = csv_dir / f'{tabela}.csv'
    
    if csv_file.exists():
        try:
            df = pd.read_csv(csv_file)
            df.to_sql(tabela, conn, if_exists='replace', index=False)
            print(f"  ✅ {tabela}: {len(df)} registos")
            csvs_carregados += 1
        except Exception as e:
            print(f"  ❌ ERRO ao carregar {tabela}: {e}")
            csvs_falhados += 1
    else:
        print(f"  ⚠️  Não encontrado: {csv_file.name}")
        csvs_falhados += 1

if csvs_carregados == 0:
    print("\n❌ ERRO: Nenhum CSV foi carregado!")
    conn.close()
    sys.exit(1)

print(f"\n✅ Base de dados criada: handball_dt.db")
print(f"   Carregados: {csvs_carregados}/{len(tabelas)} tabelas")

# 2. CRIAR ÍNDICES
print("\n2️⃣ Criando índices para performance...")

cursor = conn.cursor()

try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lances_jogo ON lances(jogo_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lances_zona ON lances(zona_baliza_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jogos_gr ON jogos(guarda_redes_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jogos_adv ON jogos(adversario_id)")
    print("  ✅ Índices criados")
    conn.commit()
except Exception as e:
    print(f"  ⚠️  Alguns índices falharam (normal se tabelas não existirem)")

# 3. TESTAR QUERIES
print("\n3️⃣ Testando base de dados...")

try:
    # Query 1: GRs
    print("\n📋 GUARDA-REDES:")
    query = "SELECT id, nome, altura_cm, posicao_principal FROM guarda_redes"
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    if len(df) != 3:
        print(f"\n⚠️  AVISO: Esperado 3 GRs, encontrados {len(df)}")
    
    # Query 2: Performance Humberto
    print("\n🎯 PERFORMANCE POR ZONA - HUMBERTO GOMES:")
    query = """
    SELECT 
        zona_baliza_nome,
        COUNT(*) as total,
        SUM(CASE WHEN resultado = 'Defesa' THEN 1 ELSE 0 END) as defesas,
        ROUND(AVG(CASE WHEN resultado = 'Defesa' THEN 100.0 ELSE 0 END), 1) as taxa
    FROM lances l
    JOIN jogos j ON l.jogo_id = j.id
    WHERE j.guarda_redes_id = 1
    GROUP BY zona_baliza_id, zona_baliza_nome
    ORDER BY zona_baliza_id
    """
    df = pd.read_sql_query(query, conn)
    print(df.head(3).to_string(index=False))
    print(f"   ... ({len(df)} zonas no total)")
    
    # Query 3: Compatibilidade
    print("\n⚔️  COMPATIBILIDADE vs FC PORTO:")
    query = """
    SELECT 
        gr.nome,
        c.taxa_defesa_perc,
        c.prob_ser_titular
    FROM compatibilidades_gr_adversario c
    JOIN guarda_redes gr ON c.guarda_redes_id = gr.id
    WHERE c.adversario_id = 1
    ORDER BY c.taxa_defesa_perc DESC
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
except Exception as e:
    print(f"\n⚠️  Erro ao testar queries: {e}")
    print("   (Algumas tabelas podem estar em falta)")

conn.close()

# 4. CRIAR DATA_ACCESS.PY
print("\n4️⃣ Criando módulo data_access.py...")

data_access_code = '''"""
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
        query = "SELECT id, nome, altura_cm, posicao_principal FROM guarda_redes"
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
    
    print("\\nPerformance Humberto por zona:")
    print(db.get_zone_performance(gr_id=1))
    
    print("\\nCompatibilidade vs FC Porto:")
    print(db.get_compatibility_matrix(adversario_id=1))
'''

try:
    with open('data_access.py', 'w', encoding='utf-8') as f:
        f.write(data_access_code)
    print("  ✅ Criado: data_access.py")
except Exception as e:
    print(f"  ⚠️  Erro ao criar data_access.py: {e}")

# RESUMO FINAL
print("\n" + "="*60)
print("✅ SETUP COMPLETO!")
print("="*60)
print(f"""
📦 Criado:
  ✅ handball_dt.db (base de dados SQLite)
  ✅ data_access.py (módulo de queries)

📊 Dados carregados:
  • {csvs_carregados} tabelas com dados
  • 3 guarda-redes do ABC Braga
  • Pronto para usar em Streamlit!

🚀 Próximos passos:
  1. Testa: python data_access.py
  2. Integra na app: from data_access import HandballDataAccess
  3. Começa o Dashboard de Timeout!

💡 Dica: Abre handball_dt.db com SQLite Browser para explorar os dados
""")

print("="*60)