from flask import jsonify
import json
import os


JSON_DIR = r"C:\Users\Gabriel\Documents\Roupas\TamanhosJsonTeste"
print("Arquivos no diretório JSON:")
print(os.listdir(JSON_DIR))

def get_all_jsons():
    """Lê todos os arquivos JSON do diretório e retorna uma lista de produtos"""
    try:
        arquivos = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
        produtos = []

        for arquivo in arquivos:
            caminho = os.path.join(JSON_DIR, arquivo)
            with open(caminho, 'r', encoding='utf-8') as f:
                try:
                    dados = json.load(f)

                    if isinstance(dados, list):
                        for item in dados:
                            item['arquivo_origem'] = arquivo
                            produtos.append(item)
                    elif isinstance(dados, dict):
                        dados['arquivo_origem'] = arquivo
                        produtos.append(dados)
                    else:
                        print(f"Formato inválido em {arquivo} - Ignorando")
                except Exception as e:
                    print(f"Erro ao processar {arquivo}: {str(e)}")
                    continue

        return produtos

    except Exception as e:
        print(f"Erro geral: {e}")
        return []

import unicodedata

def get_json_by_name(nome):
    try:
        # Normaliza o nome recebido (remove .json se existir e espaços)
        nome_arquivo = nome.replace('.json', '').strip() + '.json'
        
        # Procura o arquivo considerando espaços iniciais
        for arquivo in os.listdir(JSON_DIR):
            if arquivo.lower().strip() == nome_arquivo.lower():
                caminho = os.path.join(JSON_DIR, arquivo)
                print(f"Arquivo encontrado: {caminho}")  # Log para debug
                with open(caminho, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify(data)
                
        return jsonify({
            "erro": "Arquivo não encontrado",
            "sugestao": f"O nome exato do arquivo pode ser '{os.listdir(JSON_DIR)}'"
        }), 404
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    
