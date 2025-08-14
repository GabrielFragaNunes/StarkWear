import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# Configurações
BASE_URL = "https://www.catalogopoa.com.br"
CATEGORIES = [

     "camisetas/cotton-egipcio",

]
BASE_DIR = r"C:\Users\Gabriel\Documents\GitHub\StarkWear\api-project"

def setup_driver():
    """Configura o driver do Selenium"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    
    # Desativa carregamento de imagens
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    return webdriver.Chrome(options=chrome_options)

def get_product_sizes(product_element):
    """Captura os tamanhos disponíveis do produto, identificando automaticamente o tipo"""
    try:
        # Tenta primeiro encontrar tamanhos numéricos (bermudas)
        try:
            size_elements = product_element.find_elements(
                By.CSS_SELECTOR, ".option_tamanho_de_cala_e_bermuda span.size-name-cart"
            )
            if size_elements:
                return [size.text.strip() for size in size_elements if size.text.strip()]
        except NoSuchElementException:
            pass
        
        # Se não encontrar, procura por tamanhos em letras
        try:
            size_elements = product_element.find_elements(
                By.CSS_SELECTOR, ".option_tamanho span.size-name-cart"
            )
            if size_elements:
                return [size.text.strip() for size in size_elements if size.text.strip()]
        except NoSuchElementException:
            pass
        
        # Se ainda não encontrou, tenta um seletor mais genérico
        try:
            size_elements = product_element.find_elements(
                By.CSS_SELECTOR, ".sizes .size-name-cart"
            )
            return [size.text.strip() for size in size_elements if size.text.strip()]
        except NoSuchElementException:
            return []
            
    except Exception as e:
        print(f"Erro ao buscar tamanhos: {str(e)}")
        return []

def clean_product_title(title):
    """Limpa o título do produto removendo códigos e formatação extra"""
    # Remove o código do produto no final (ex: "- 1024" ou "- sueterpremium0008")
    if " - " in title:
        title = " - ".join(title.split(" - ")[:-1]).strip()
    # Remove reticências e outros caracteres especiais
    title = title.replace("...", "").strip()
    return title

def get_product_image_url(driver, product_url):
    """Acessa a página do produto e retorna a URL da imagem principal"""
    try:
        driver.get(product_url)
        time.sleep(1.5)
        img = driver.find_element(By.CSS_SELECTOR, "img.img-fluid.product-image-area")
        return img.get_attribute("src")
    except Exception as e:
        print(f"⚠️ Erro ao coletar imagem de {product_url}: {str(e)}")
        return ""

def get_product_images(driver, product_url):
    """Acessa a página do produto e retorna uma lista com todas as URLs das imagens grandes"""
    try:
        driver.get(product_url)
        time.sleep(1.5)
        images = []
        # Coleta todas as imagens do carrossel de thumbnails
        thumbnail_lis = driver.find_elements(By.CSS_SELECTOR, "ul.product-thumbnails li[data-large-image]")
        for li in thumbnail_lis:
            img_url = li.get_attribute("data-large-image")
            if img_url and img_url not in images:
                images.append(img_url)
        # Se não encontrar thumbnails, tenta pegar a imagem principal
        if not images:
            img = driver.find_element(By.CSS_SELECTOR, "img.img-fluid.product-image-area")
            images.append(img.get_attribute("src"))
        return images
    except Exception as e:
        print(f"⚠️ Erro ao coletar imagens de {product_url}: {str(e)}")
        return []

def scrape_category(driver, category):
    """Coleta todos os produtos de uma categoria"""
    print(f"\n🔎 Iniciando categoria: {category}")
    category_url = f"{BASE_URL}/{category}"
    
    products = []
    processed_urls = set()
    
    try:
        driver.get(category_url)
        time.sleep(3)
    except Exception as e:
        print(f"❌ Erro ao acessar {category_url}: {str(e)}")
        return []

    # Coleta todas as páginas da categoria
    all_pages = set()
    try:
        # Sempre adiciona a página atual
        all_pages.add(driver.current_url)
        # Busca todos os links de paginação
        pagination = driver.find_elements(By.CSS_SELECTOR, "ul.pagination a")
        for link in pagination:
            href = link.get_attribute("href")
            if href:
                all_pages.add(href)
    except NoSuchElementException:
        pass

    produtos_basicos = []
    for page_url in sorted(all_pages):
        print(f"➡️ Processando página: {page_url}")
        try:
            driver.get(page_url)
            time.sleep(2)
            product_elements = driver.find_elements(By.CSS_SELECTOR, "div.product.product-grid")
            for product in product_elements:
                try:
                    title_element = product.find_element(By.CSS_SELECTOR, "p.product-title a")
                    product_title = clean_product_title(title_element.text.strip())
                    product_url = title_element.get_attribute("href")
                    if product_url in processed_urls:
                        continue
                    sizes = get_product_sizes(product)
                    produtos_basicos.append({
                        "titulo": product_title,
                        "tamanhos": sizes,
                        "url_produto": product_url,
                        "categoria": category.split('/')[-1]
                    })
                    processed_urls.add(product_url)
                except Exception as e:
                    print(f"⚠️ Erro ao processar produto: {str(e)}")
        except Exception as e:
            print(f"⚠️ Erro ao processar página {page_url}: {str(e)}")
            continue

    # 2º passo: Para cada produto, acessar a página e coletar as imagens
    for produto in produtos_basicos:
        imagens = get_product_images(driver, produto["url_produto"])
        produto["imagens"] = imagens
        print(f"✅ Produto adicionado: {produto['titulo']} | Tamanhos: {', '.join(produto['tamanhos'])} | Imagens: {imagens}")
        products.append(produto)

    return products

def unir_produtos_por_url(lista_produtos):
    """Remove duplicados por URL e une todos os tamanhos"""
    produtos_unicos = {}
    for produto in lista_produtos:
        url = produto["url_produto"]
        if url in produtos_unicos:
            tamanhos_antigos = set(produtos_unicos[url]["tamanhos"])
            tamanhos_novos = set(produto.get("tamanhos", []))
            produtos_unicos[url]["tamanhos"] = sorted(tamanhos_antigos.union(tamanhos_novos))
            # Atualiza imagens se necessário (mantém as primeiras encontradas)
            if "imagens" in produto and produto["imagens"]:
                if "imagens" not in produtos_unicos[url] or not produtos_unicos[url]["imagens"]:
                    produtos_unicos[url]["imagens"] = produto["imagens"]
        else:
            produtos_unicos[url] = produto.copy()
    return list(produtos_unicos.values())

def save_category_data(category, products):
    """Salva todos os produtos da categoria em um único arquivo JSON"""
    if not products:
        print(f"ℹ️ Nenhum produto encontrado para {category}")
        return

    # Remove duplicados e une tamanhos
    products = unir_produtos_por_url(products)

    # Cria pasta principal se não existir
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Nome do arquivo baseado na categoria
    category_name = category.replace('/', '_')
    filename = f" {category_name}.json"
    output_file = os.path.join(BASE_DIR, filename)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(products)} produtos salvos em: {output_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo {output_file}: {str(e)}")

def main():
    """Função principal"""
    print("🚀 Iniciando scraping de todas as categorias...")
    driver = setup_driver()

    try:
        for category in CATEGORIES:
            print(f"\n{'='*50}")
            print(f"🛒 PROCESSANDO CATEGORIA: {category.upper()}")
            print(f"{'='*50}")
            
            products = scrape_category(driver, category)
            save_category_data(category, products)
            time.sleep(3)
    finally:
        driver.quit()
        print("\n🎉 Todas as categorias foram processadas com sucesso!")

if __name__ == "__main__":
    main()