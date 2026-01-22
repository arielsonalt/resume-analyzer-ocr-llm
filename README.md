# TechMatch -- Analisador de Currículos (OCR + LLM)

## Visão Geral

O **TechMatch Analisador de Currículos** é uma API inteligente que automatiza a análise
de currículos em **PDF ou imagem (JPG/PNG)**.

O sistema realiza:

1. **OCR (Reconhecimento de Texto)** para extrair conteúdo de
   currículos.\
2. **LLM (Language Model)** para gerar **sumários** e **justificativas
   inteligentes**.\
3. **Ranking semântico** para responder perguntas de recrutamento.\
4. **Persistência de logs** em banco NoSQL (MongoDB), sem armazenar os
   arquivos originais.

O objetivo é permitir que recrutadores façam perguntas como:

> "Qual desses currículos se encaixa melhor para a vaga de Engenheiro de
> Software com Python, FastAPI e AWS?"

E recebam **ranking + justificativas**, economizando horas de leitura
manual.

---

## O que o sistema faz

### Fluxo principal

1. Recebe múltiplos currículos (PDF ou imagem).\
2. Extrai texto via OCR.\
3. Gera:
   - **Sumários individuais** (se não houver query).
   - **Ranking por similaridade semântica** (se houver query).
4. Usa LLM para:
   - Resumir currículos.
   - Explicar por que um currículo foi bem ranqueado.
5. Salva logs de uso no MongoDB:
   - request_id\
   - user_id\
   - timestamp\
   - query\
   - resultado retornado

**Obs.:** Os arquivos originais **não são armazenados**, reduzindo custo
e risco de armazenamento.

---

## Tecnologias

- FastAPI -- API REST + Swagger automático\
- OCR Engines -- Tesseract, EasyOCR, PaddleOCR\
- LLM Local -- Summarizer e Explainer\
- Ranking Semântico -- Embeddings + similaridade vetorial\
- MongoDB -- Logs de auditoria\
- Docker + Docker Compose -- Execução completa em containers

---

## Requisitos de Ambiente

### Python

- Versão recomendada: **\>=3.11 e \<3.12**
- O projeto utiliza dependências que não garantem compatibilidade com
  Python 3.12+.

### Criação do ambiente virtual

**Windows**

```
    py -3.11 -m venv .venv
    .venv\Scripts\activate
```

**Linux/Mac**

```
    python3.11 -m venv .venv
    source .venv/bin/activate
```

---

### Instalação das dependências

```
    pip install -r requirements.txt
```

---

## Execução com Docker

O projeto possui **Docker Compose** configurado com:

- API FastAPI\
- MongoDB

### Para subir o sistema

    **Certifique-se de que o docker esteja devidamente instalado (ex: docker desktop ativo)**

```
    docker compose up --build
```

Esse comando:

- Constrói as imagens\
- Inicia a API\
- Inicia o MongoDB\
- Conecta tudo automaticamente

### A API ficará disponível em

    http://localhost:8000

---

## Swagger (Documentação Interativa)

O FastAPI gera automaticamente documentação OpenAPI.

### Acesse no navegador

    http://localhost:8000/docs

### O que o Swagger permite

- Visualizar todos os endpoints\
- Ver exemplos de entrada e saída\
- Testar requisições diretamente no navegador\
- Validar parâmetros automaticamente

### Arquivo OpenAPI

    http://localhost:8000/openapi.json

---

## Endpoints Disponíveis

### POST /v1/cv/analyze

**Função:**
Analisa múltiplos currículos.

**Modos de operação:**

**1) Sem query** → Retorna sumários individuais.
**2) Com query** → Retorna ranking + justificativas.

**Parâmetros (multipart/form-data):**

  Campo        Tipo            Obrigatório   Descrição

---

  request_id   string (UUID)   sim           Identificador único da requisição (inserir um código UUID - Geralmente esse código é gerado de forma automatica, porém segui o requisito informado)
  user_id      string          sim           Identificador do solicitante (inserir um id para o usuário)
  query        string          não           Pergunta de recrutamento
  top_k        int             não           Quantidade de resultados no ranking
  ocr_engine   string          não           tesseract \| easyocr \| paddleocr
  files        arquivos        sim           PDFs ou imagens JPG/PNG

---

### GET /v1/logs

**Função:**
Lista logs armazenados no MongoDB para auditoria.

**Parâmetros opcionais:**

  Campo     Tipo     Descrição

---

  user_id   string   Filtra logs por usuário
  limit     int      Quantidade máxima de registros

---

## Estrutura do Projeto

    app/
     ├── main.py                		→ API FastAPI
     ├── ocr/                  			→ Engines OCR
     ├── llm/                   			→ Summarizer e Explainer
     ├── rank/                  		→ Ranking semântico
     ├── store/                 		→ Persistência MongoDB
     ├── docker-compose.yml.    	→ Orquestrador de múltiplos containers
     ├── Dockerfile             		→ Configurações do container
     ├── Readme.md              		→ Informações sobre o projeto
     └── requirements.txt       		→ Dependências do projetos e suas respectivas versões

---

## Logs de Auditoria

Cada requisição gera um log no MongoDB:

```json
{
  "request_id": "...",
  "user_id": "...",
  "timestamp": "...",
  "query": "...",
  "result": {...}
}
```

---

## Resumo

✔ OCR automático
✔ LLM para sumarização e explicação
✔ Ranking semântico por query
✔ Logs auditáveis em MongoDB
✔ Swagger interativo
✔ Execução simples via Docker
