import os
import json
import tempfile
import vertexai
from google.cloud import storage
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from processing import geracao_embeddings

load_dotenv()

PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["LOCATION"]
BUCKET_NAME = os.environ["BUCKET_NAME"] 
PREFIX_INPUT = os.environ["FOLDER_NAME"] 
PREFIX_OUTPUT = os.environ["EMBEDDINGS_FOLDER"]
FILE_NAME = os.environ["FILE_EMBEDDINGS"]     

vertexai.init(project=PROJECT_ID, location=LOCATION)

def extracao_conteudo():
    """
    Etapa responsável por realizar o download de documentos do GCS e extração do conteúdo.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = bucket.list_blobs(prefix=PREFIX_INPUT)

    except Exception as e:
        print(f"Erro fatal ao conectar no Bucket: {e}")
        return

    for blob in blobs:
        file_name = blob.name.lower()
        
        if file_name == PREFIX_INPUT.lower() or not file_name.endswith((".pdf", ".docx")):
            continue

        suffix = ".pdf" if file_name.endswith(".pdf") else ".docx"
        temp_path = ""
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                blob.download_to_filename(temp_file.name)
                temp_path = temp_file.name

            loader = PyPDFLoader(temp_path) if suffix == ".pdf" else Docx2txtLoader(temp_path)
            
            # Carrega e consolida o texto
            paginas = loader.load()
            texto_completo = "\n".join([p.page_content for p in paginas])
            
            if texto_completo:
                yield {
                    "file_name": blob.name,
                    "type": "pdf" if suffix == ".pdf" else "docx",
                    "text": texto_completo
                }

        except Exception as e:
            print(f"[ERRO DE EXTRAÇÃO] {blob.name}: {e}")
        
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

def dataset_gcs(dados):
    """
    Etapa responsável por salvar o dataset final de embeddings no GCS
    """

    if not dados:
        print("[AVISO] Nenhum dado gerado para salvar.")
        return

    nome_arquivo_saida = FILE_NAME
    caminho_completo = f"{PREFIX_OUTPUT}{nome_arquivo_saida}"
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(caminho_completo)
        
        buffer_dados = ""
        for entry in dados:
            buffer_dados += json.dumps(entry) + "\n"
        
        blob.upload_from_string(buffer_dados, content_type="application/json")
        print(f"\nSUCESSO - Arquivo salvo em: gs://{BUCKET_NAME}/{caminho_completo}\n")
        
    except Exception as e:
        print(f"\n[ERRO UPLOAD] Falha ao salvar no bucket: {e}\n")


if __name__ == "__main__":

    # Passo 1: Inicia o gerador de extração
    gerador = extracao_conteudo()
    
    # Passo 2: Processa chunks e embeddings
    dados_vetorizados = geracao_embeddings(gerador)
    
    # Passo 3: Salva o resultado final
    dataset_gcs(dados_vetorizados)