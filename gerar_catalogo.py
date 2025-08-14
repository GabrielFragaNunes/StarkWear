import os
import json
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

BASE_DIR = r"C:\Users\Gabriel\Documents\GitHub\StarkWear"
PDF_OUTPUT = os.path.join(BASE_DIR, "catalogo.pdf")

def baixar_imagem(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except Exception:
        pass
    return None

def adicionar_produto_pdf(c, produto, y):
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, produto["titulo"])
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Categoria: {produto.get('categoria', '')}")
    y -= 15
    c.drawString(40, y, f"Tamanhos: {', '.join(produto.get('tamanhos', []))}")
    y -= 15

    imagens = produto.get("imagens", [])
    if imagens:
        for img_url in imagens[:2]:  # Mostra até 2 imagens por produto
            img_data = baixar_imagem(img_url)
            if img_data:
                try:
                    c.drawImage(ImageReader(img_data), 40, y-120, width=120, height=120, preserveAspectRatio=True)
                    y -= 130
                except Exception:
                    continue
    else:
        y -= 130

    y -= 10
    c.line(30, y, 550, y)
    y -= 20
    return y

def unir_produtos_por_titulo(lista_produtos):
    produtos_unicos = {}
    for produto in lista_produtos:
        titulo = produto["titulo"]
        if titulo in produtos_unicos:
            # Atualiza tamanhos (evita duplicidade)
            tamanhos_antigos = set(produtos_unicos[titulo]["tamanhos"])
            tamanhos_novos = set(produto.get("tamanhos", []))
            produtos_unicos[titulo]["tamanhos"] = sorted(tamanhos_antigos.union(tamanhos_novos))
        else:
            produtos_unicos[titulo] = produto.copy()
    return list(produtos_unicos.values())

def gerar_catalogo():
    c = canvas.Canvas(PDF_OUTPUT, pagesize=A4)
    width, height = A4
    y = height - 40

    # Junta todos os produtos dos JSONs
    todos_produtos = []
    for filename in os.listdir(BASE_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(BASE_DIR, filename), encoding="utf-8") as f:
                produtos = json.load(f)
                todos_produtos.extend(produtos)

    # Remove duplicados e une tamanhos
    produtos_unicos = unir_produtos_por_titulo(todos_produtos)

    # Filtrar somente camisetas com tamanho G3
    camisetas_g3 = [
        dict(p) for p in produtos_unicos
        if "G3" in p.get("tamanhos", []) and "camiseta" in p["titulo"].lower()
    ]
    # Remover o campo url_produto dos produtos filtrados
    for produto in camisetas_g3:
        if "url_produto" in produto:
            del produto["url_produto"]

    for produto in camisetas_g3:
        if y < 180:
            c.showPage()
            y = height - 40
        y = adicionar_produto_pdf(c, produto, y)
    c.save()
    print(f"PDF gerado em: {PDF_OUTPUT}")


if __name__ == "__main__":
    gerar_catalogo()