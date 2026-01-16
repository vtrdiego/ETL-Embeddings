# Pipeline de Embeddings - Vector Search do Google Cloud

Este projeto é uma ferramenta de ETL (Extração, Transformação e Carga) desenvolvida em Python para automatizar a criação de bases de conhecimento para RAG (Retrieval-Augmented Generation).

## Objetivo:

Ler documentos não estruturados (`.pdf` e `.docx`) armazenados no Google Cloud Storage, transformá-los em vetores numéricos (embeddings) utilizando o próprio modelo do Vertex AI e gerar um arquivo JSON formatado e pronto para indexação no **Vertex AI Vector Search**, do Google Cloud, podendo ser utilizando para diversas outras tarefas, como no próprio RAG Engine.

## Funcionamento da Aplicação:

A aplicação foi modularizada para eficiência de memória e performance:

1.  **Extração (`main.py`):**
    - Conecta ao Bucket do GCS.
    - Utiliza **Generators (`yield`)** para baixar e carregar na memória apenas um arquivo por vez, evitando travamentos.
    - Extrai o texto bruto de PDFs e arquivos Docx.

2.  **Processamento (`processing.py`):**
    - **Chunking:** Divide o texto em pedaços menores (ex: 600 caracteres) com overlap de 100 para manter o contexto.
    - **Embedding em Lote:** Envia pacotes de 100 chunks por vez para a API da Vertex AI, utilizando o modelo 'text-embedding-004', otimizando o tempo de rede.
    - **Estruturação:** Formata o JSON final com `id`, `embedding`, filtros (`restricts`) e metadados (`original_text`) para permitir futuro RAG.

3.  **Carga (`main.py`):**
    - Após a geração do JSON final, faz o upload do arquivo em uma segunda pasta no Cloud Storage.

## Bibliotecas Utilizadas:

* **`vertexai`**: SDK oficial para acesso aos modelos de IA (Text Embedding) do Google Cloud.
* **`google-cloud-storage`**: Para download dos arquivos de entrada e upload do dataset final.
* **`langchain-text-splitters`**: Para realizar o "Chunking" do texto.
* **`langchain-community`**: Fornece os loaders (`PyPDFLoader`, `Docx2txtLoader`).
* **`pypdf`**: Motor de leitura de arquivos PDF.
* **`docx2txt`**: Motor de leitura de arquivos Word (.docx).
* **`python-dotenv`**: Para gerenciamento seguro de variáveis de ambiente.

## Como Rodar:

### 1. Pré-requisitos
* Python 3.9+
* Bucket criado no GCS com uma pasta de entrada contendo os arquivos, e uma segunda pasta para armazenar o JSON final.
* Crie um .env na raiz como mostra os dados de exemplo.

### 2. Instalação e Login
É recomendado o uso de um ambiente virtual para evitar conflitos de versões.

**Criar o ambiente virtual**
python3 -m venv venv

**Ativar o ambiente**
source venv/bin/activate

**Instalar bibliotecas**
pip install -r requirements.txt

**Autenticação no Google Cloud**
* Login: gcloud auth application-default login
* Definir o projeto: gcloud config set project SEU_ID_DO_PROJETO