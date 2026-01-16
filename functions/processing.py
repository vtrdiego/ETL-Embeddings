import os
from dotenv import load_dotenv
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
MODEL_EMBEDDING = os.environ["MODEL"]

def geracao_embeddings(documentos_storage):
    """
    Etapa responsável por receber os documentos extraídos, quebrar em chunks e 
    gerar o arquivo jsonl contendo embeddings e metadados.
    """
    # Configurações do Modelo e Splitter
    model = TextEmbeddingModel.from_pretrained(MODEL_EMBEDDING)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=60,
        separators=["\n\n", "\n", " ", ""]
    )
    
    lista_final_para_indexar = []

    # Iteração sobre cada documento
    for doc in documentos_storage:
        nome_arquivo = doc['file_name']
        texto_bruto = doc['text']
        tipo_arquivo = doc['type']
        
        print(f"> Processando: {nome_arquivo}")

        # 1. Chunking
        chunks = text_splitter.split_text(texto_bruto)
        
        # 2. Embedding em Batch
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_texts = chunks[i : i + batch_size]
            
            inputs = [TextEmbeddingInput(text, "RETRIEVAL_DOCUMENT") for text in batch_texts]
            
            try:
                embeddings = model.get_embeddings(inputs)
                
                # 3. Formatação JSONL para Vector Search
                for j, emb_object in enumerate(embeddings):
                    idx_global = i + j
                    
                    vetor_estruturado = {
                        "id": f"{nome_arquivo}_chunk_{idx_global}",
                        "embedding": emb_object.values, 
                        "restricts": [
                            {"namespace": "source", "allow": [nome_arquivo]},
                            {"namespace": "type", "allow": [tipo_arquivo]}
                        ],
                        "embedding_metadata": {
                            "original_text": batch_texts[j],
                            "source_file": nome_arquivo,
                            "page_chunk": idx_global
                        }
                    }
                    lista_final_para_indexar.append(vetor_estruturado)
                    
            except Exception as e:
                print(f"   [ERRO API VERTEX] Falha no lote {i} do arquivo {nome_arquivo}: {e}")

    return lista_final_para_indexar