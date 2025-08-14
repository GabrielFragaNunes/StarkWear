import requests
from bs4 import BeautifulSoup
import json

# Carrega o JSON
with open('camisetas_overs.json', 'r', encoding='utf-8') as file:
    produtos = json.load(file)

# Lista para armazenar URLs das imagens
image_urls = []

# Loop pelos produtos
for produto in produtos:
    url_produto = produto['url_produto']  # Acessa a URL do produto
    try:
        response = requests.get(url_produto)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Procura a tag <img> (ajuste o seletor conforme o site)
            img_tag = soup.find('img', {'class': 'product-image'})  # Exemplo: classe comum
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
                if not image_url.startswith('http'):
                    image_url = 'https://www.catalogopoa.com.br' + image_url  # Completa URL se necessário
                image_urls.append({
                    'titulo': produto['titulo'],
                    'url_imagem': image_url
                })
                print(f"Imagem encontrada para {produto['titulo']}: {image_url}")
    except Exception as e:
        print(f"Erro ao acessar {url_produto}: {e}")

# Salva as URLs das imagens em um novo JSON
with open('imagens_produtos.json', 'w', encoding='utf-8') as file:
    json.dump(image_urls, file, ensure_ascii=False, indent=2)

print(f"Total de imagens extraídas: {len(image_urls)}")