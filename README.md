# 🤾 Digital Twin - Guarda-Redes de Andebol

Dashboard interativo para apoio à decisão tática em guarda-redes de andebol.

## 🚀 Instalação e Execução

### 1. Instala as dependências
```bash
pip install -r requirements.txt
```

### 2. Executa a aplicação
```bash
streamlit run app.py
```

### 3. Abre no browser
Automaticamente abre em: `http://localhost:8501`

## 📱 Como Testar

### Interface 1: ⏱️ Timeout em Jogo (90 segundos)
**Objetivo**: Decisões rápidas durante o jogo

**Como testar**:
1. Seleciona "Timeout em Jogo" na sidebar
2. Ajusta o minuto do jogo (ex: 42 min)
3. Altera o resultado (ex: 24-24)
4. Muda o guarda-redes (Humberto, Diogo ou Tiago)
5. Observa as recomendações automáticas

**O que vês**:
- Análise de vulnerabilidades por zona
- Recomendação tática imediata
- Estado físico do atleta
- Opção de substituição

### Interface 2: 📊 Análise Pré-Jogo
**Objetivo**: Preparação antes do jogo

**Como testar**:
1. Seleciona "Análise Pré-Jogo"
2. Explora os 3 tabs:
   - **Padrões Adversário**: Mapa de calor de remates
   - **Compatibilidade GR**: Qual o melhor guarda-redes?
   - **Recomendações**: Plano tático detalhado

**O que vês**:
- Heatmap de probabilidades de remate
- Score de compatibilidade
- Estratégias de posicionamento

### Interface 3: 📚 Planeamento de Treino
**Objetivo**: Análise de gap e plano semanal

**Como testar**:
1. Seleciona "Planeamento de Treino"
2. Muda o guarda-redes na sidebar
3. Compara eficácia atual vs objetivo

**O que vês**:
- Gap de performance por zona
- Priorização de áreas de treino
- Distribuição do plano semanal
- Evolução esperada

## 🎯 Cenários de Teste Recomendados

### Cenário A: Jogo Equilibrado
```
Configuração:
- Cenário: Timeout em Jogo
- Minuto: 30
- Resultado: 15-15
- GR: Humberto Gomes
```

### Cenário B: Pressão Final (a perder)
```
Configuração:
- Cenário: Timeout em Jogo
- Minuto: 55
- Resultado: 24-25
- GR: Diogo Ribeiro
```

### Cenário C: Comparar Guarda-Redes
```
Configuração:
- Cenário: Análise Pré-Jogo
- Tab: Compatibilidade GR
- Compara os 3 atletas
```

### Cenário D: Planeamento
```
Configuração:
- Cenário: Planeamento de Treino
- Testa com cada guarda-redes
- Analisa os gaps diferentes
```

## 🔧 Troubleshooting

### Problema: Módulos não encontrados
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Problema: Porta já em uso
```bash
streamlit run app.py --server.port 8502
```

### Problema: Dashboard não abre
Abre manualmente: http://localhost:8501

## 📊 Dados Simulados

Os dados usados são **simulados** mas **realistas**, baseados em:
- Características antropométricas reais de guarda-redes
- Estatísticas de eficácia típicas
- Padrões de remate observados em jogos profissionais

### Guarda-Redes Disponíveis:

**Humberto Gomes**
- Altura: 185cm
- Envergadura: 190cm  
- Eficácia Global: 60%
- Especialidade: Agilidade lateral

**Diogo Ribeiro**
- Altura: 186cm
- Envergadura: 195cm
- Eficácia Global: 62%
- Especialidade: Posicionamento tático

**Tiago Ferreira**
- Altura: 191cm
- Envergadura: 200cm
- Eficácia Global: 54%
- Especialidade: Cobertura superior

## 🎓 Contexto Académico

**Projeto**: M3 - Defesa da Solução
**Disciplina**: Apresentação e Visualização de Informação
**Curso**: MEGSI 2025/26
**Instituição**: Universidade do Minho

**Equipa**:
- Eduardo Dias (PG61456)
- Nuno Martinho (PG47542)
- Lucas Serralha (PG60114)

## 📚 Próximos Passos (M3)

Para a implementação final em M3, o sistema irá integrar:

1. **H2O.ai** - Motor de predição de probabilidades
2. **PostgreSQL** - Base de dados real
3. **Dados Reais** - Integração com ABC Braga
4. **Análise Vídeo** - Processamento de jogos
5. **Sensores** - Dados biométricos em tempo real

## 📄 Licença

© 2025 ABC Braga Digital Twin System
Universidade do Minho - MEGSI
