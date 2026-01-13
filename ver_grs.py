# ver_epocas.py
import sqlite3

conn = sqlite3.connect('handball_dt.db')
cursor = conn.cursor()

# Ver estrutura da tabela epocas
cursor.execute("PRAGMA table_info(epocas)")
print("\n📋 COLUNAS DA TABELA EPOCAS:")
colunas = []
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")
    colunas.append(col[1])

print("\n📊 DADOS DA TABELA EPOCAS (época 2025):")
print("-" * 120)

cursor.execute("SELECT * FROM epocas WHERE epoca = 2025")
for row in cursor.fetchall():
    for i, val in enumerate(row):
        print(f"{colunas[i]:30} = {val}")
    print("-" * 120)

print("\n🔍 JUNÇÃO GRs + EPOCAS:")
print("-" * 120)

cursor.execute("""
    SELECT 
        gr.nome,
        gr.altura_cm,
        gr.envergadura_cm,
        e.taxa_defesa_global,
        e.jogos_disputados,
        gr.posicao_principal
    FROM guarda_redes gr
    LEFT JOIN epocas e ON gr.id = e.guarda_redes_id AND e.epoca = 2025
""")

for row in cursor.fetchall():
    print(f"{row[0]:20} | {row[1]}cm | {row[2]}cm | Taxa: {row[3]:.1f}% | {row[4]} jogos | {row[5]}")

conn.close()