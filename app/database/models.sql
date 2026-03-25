-- ============================================================
-- MODELS.SQL - ESTRUTURA DO BANCO DE DADOS
-- ============================================================
-- Responsável por:
-- - Armazenar operações
-- - Registrar decisões do sistema
-- - Controlar portfólio
-- - Monitorar performance
-- - Permitir auditoria completa
-- ============================================================

-- ============================================================
-- EXTENSÕES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USUÁRIO (FUTURO MULTI-CONTA)
-- ============================================================
CREATE TABLE usuarios (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
nome VARCHAR(100),
email VARCHAR(150) UNIQUE,
criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ATIVOS
-- ============================================================
CREATE TABLE ativos (
id SERIAL PRIMARY KEY,
ticker VARCHAR(20) UNIQUE NOT NULL,
nome VARCHAR(150),
tipo VARCHAR(50), -- ACAO, FII, CRIPTO
criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DADOS DE MERCADO (SNAPSHOT)
-- ============================================================
CREATE TABLE dados_mercado (
id BIGSERIAL PRIMARY KEY,
ativo_id INT REFERENCES ativos(id),
preco NUMERIC,
volume NUMERIC,
roe NUMERIC,
pl NUMERIC,
volatilidade NUMERIC,
rsi NUMERIC,
media_20 NUMERIC,
media_50 NUMERIC,
tendencia INT,
coletado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dados_mercado_ativo ON dados_mercado(ativo_id);
CREATE INDEX idx_dados_mercado_data ON dados_mercado(coletado_em);

-- ============================================================
-- SCORE (DECISÃO DO MODELO)
-- ============================================================
CREATE TABLE scores (
id BIGSERIAL PRIMARY KEY,
ativo_id INT REFERENCES ativos(id),

```
score_total NUMERIC,
score_fundamentos NUMERIC,
score_momento NUMERIC,
score_risco NUMERIC,
score_liquidez NUMERIC,

decisao VARCHAR(50), -- COMPRA / VENDA / HOLD

criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

CREATE INDEX idx_scores_ativo ON scores(ativo_id);

-- ============================================================
-- ORDENS (INTENÇÃO)
-- ============================================================
CREATE TABLE ordens (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
ativo_id INT REFERENCES ativos(id),

```
tipo VARCHAR(10), -- COMPRA / VENDA
preco NUMERIC,
quantidade INT,
valor_total NUMERIC,

score NUMERIC,
status VARCHAR(20), -- PENDENTE / APROVADA / EXECUTADA / CANCELADA

criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- APROVAÇÕES (USUÁRIO)
-- ============================================================
CREATE TABLE aprovacoes (
id SERIAL PRIMARY KEY,
ordem_id UUID REFERENCES ordens(id),

```
aprovado BOOLEAN,
motivo TEXT,

respondido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- EXECUÇÕES (REAL)
-- ============================================================
CREATE TABLE execucoes (
id SERIAL PRIMARY KEY,
ordem_id UUID REFERENCES ordens(id),

```
preco_execucao NUMERIC,
quantidade INT,
valor_total NUMERIC,

executado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- POSIÇÕES (CARTEIRA ATUAL)
-- ============================================================
CREATE TABLE posicoes (
id SERIAL PRIMARY KEY,
ativo_id INT REFERENCES ativos(id),

```
quantidade INT,
preco_medio NUMERIC,

atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- HISTÓRICO DE TRADES (FECHADOS)
-- ============================================================
CREATE TABLE trades (
id SERIAL PRIMARY KEY,
ativo_id INT REFERENCES ativos(id),

```
data_entrada TIMESTAMP,
data_saida TIMESTAMP,

preco_entrada NUMERIC,
preco_saida NUMERIC,

quantidade INT,

lucro NUMERIC,
retorno_percentual NUMERIC,
duracao_dias INT,

motivo_saida VARCHAR(100),

criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- CAPITAL / FINANCEIRO
-- ============================================================
CREATE TABLE capital (
id SERIAL PRIMARY KEY,

```
capital_total NUMERIC,
capital_disponivel NUMERIC,
capital_investido NUMERIC,

atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- SNAPSHOT FINANCEIRO (CURVA DE PATRIMÔNIO)
-- ============================================================
CREATE TABLE patrimonio (
id BIGSERIAL PRIMARY KEY,

```
valor_total NUMERIC,

registrado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- LOG DE EVENTOS (AUDITORIA)
-- ============================================================
CREATE TABLE logs_eventos (
id BIGSERIAL PRIMARY KEY,

```
tipo VARCHAR(50),
descricao TEXT,
dados JSONB,

criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

-- ============================================================
-- ÍNDICES IMPORTANTES
-- ============================================================
CREATE INDEX idx_ordens_status ON ordens(status);
CREATE INDEX idx_trades_ativo ON trades(ativo_id);
CREATE INDEX idx_patrimonio_data ON patrimonio(registrado_em);
