import json
import time
import argparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm

# --- CONFIGURAÇÕES GLOBAIS ---
BASE_URL = "https://www.catalogopoa.com.br"
CATEGORIES_TO_SCRAPE = [
    # Adicione ou remova categorias aqui para controlar o que será buscado.
    
    "bermudas/mauricinho-linho", # Exemplo: Mauricinho Linho
]
OUTPUT_DIR = Path(r"C:\Users\Gabriel\Documents\GitHub\StarkWear\data")
WAIT_TIMEOUT = 10

# Seletores CSS centralizados para fácil manutenção
SELECTORS = {
    "product_card": "div.product.product-grid",
    "product_title_link": "p.product-title a",
    "pagination_links": "ul.pagination a",
    "main_image": "img.img-fluid.product-image-area",
    "thumbnail_images": "ul.product-thumbnails li[data-large-image]",
    "sizes_selectors": [
        "ul.product_options_list li",
        ".option_tamanho_de_cala_e_bermuda span.size-name-cart",
        ".option_tamanho span.size-name-cart",
        ".sizes .size-name-cart"
    ]
}

# --- FUNÇÕES AUXILIARES ---

def setup_driver() -> webdriver.Chrome:
    """Configura e retorna uma instância do Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=chrome_options)

def clean_product_title(title: str) -> str:
    """Limpa o título do produto."""
    if " - " in title:
        title = " - ".join(title.split(" - ")[:-1]).strip()
    return title.replace("...", "").strip()

def get_product_details(driver: webdriver.Chrome, product_url: str) -> dict:
    """
    Visita a página de um produto para extrair imagens e tamanhos de forma robusta,
    garantindo a ordem correta das imagens.
    """
    details = {"imagens": [], "tamanhos": []}
    try:
        driver.get(product_url)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        # ======================================================================
        # --- INÍCIO DA CORREÇÃO DE ORDENAÇÃO DE IMAGENS ---
        # ======================================================================
        
        all_image_urls = []

        # 1. Tenta obter a imagem principal primeiro para garantir que ela seja uma candidata
        try:
            main_image = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["main_image"])))
            main_image_src = main_image.get_attribute("src")
            if main_image_src:
                all_image_urls.append(main_image_src)
        except TimeoutException:
            print(f"  - Aviso: Imagem principal não encontrada para {product_url}")

        # 2. Coleta as imagens das thumbnails, que ditam a ordem correta
        try:
            thumbnails = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, SELECTORS["thumbnail_images"])))
            if thumbnails:
                # Extrai as URLs na ordem em que aparecem no HTML
                thumbnail_urls = [
                    thumb.get_attribute("data-large-image") 
                    for thumb in thumbnails 
                    if thumb.get_attribute("data-large-image")
                ]
                all_image_urls.extend(thumbnail_urls)
        except TimeoutException:
            print(f"  - Aviso: Nenhuma thumbnail encontrada para {product_url}. Usando apenas a imagem principal, se existir.")
        
        # 3. Remove duplicatas mantendo a ordem (a partir do Python 3.7+)
        if all_image_urls:
            details["imagens"] = list(dict.fromkeys(all_image_urls))
        else:
             print(f"  - Aviso: Nenhuma imagem (principal ou thumbnail) foi encontrada para {product_url}")

        # ======================================================================
        # --- FIM DA CORREÇÃO ---
        # ======================================================================

        # 4. Coletar Tamanhos (lógica existente mantida)
        found_sizes = []
        for selector in SELECTORS["sizes_selectors"]:
            try:
                size_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if size_elements:
                    found_sizes = [el.text.strip() for el in size_elements if el.text.strip()]
                    break
            except NoSuchElementException:
                continue
        
        if found_sizes:
            # Garante que os tamanhos sejam únicos e ordenados
            details["tamanhos"] = sorted(list(set(found_sizes)))

    except Exception as e:
        print(f"  - Erro crítico ao processar detalhes de {product_url}: {e}")
    
    return details

# --- LÓGICAS DOS MODOS DE OPERAÇÃO ---

def run_add_mode(driver: webdriver.Chrome):
    """MODO ADICIONAR: Busca apenas produtos novos nas categorias especificadas."""
    print("🚀 Iniciando em modo 'adicionar': buscando apenas produtos novos.")
    for category in CATEGORIES_TO_SCRAPE:
        print(f"\n--- Verificando categoria: {category} ---")
        output_filename = category.replace('/', '_') + ".json"
        output_path = OUTPUT_DIR / output_filename
        
        existing_products = {}
        if output_path.is_file():
            with open(output_path, 'r', encoding='utf-8') as f:
                try:
                    existing_products = {p['url_produto']: p for p in json.load(f)}
                except (json.JSONDecodeError, TypeError, KeyError):
                    print(f"  - Aviso: Arquivo '{output_filename}' corrompido ou malformado. Será sobrescrito se novos produtos forem encontrados.")
                    existing_products = {}
        
        basic_product_info = []
        processed_urls = set()
        start_url = f"{BASE_URL}/{category}"
        driver.get(start_url)
        
        page_urls = {start_url}
        try:
            pagination_links = driver.find_elements(By.CSS_SELECTOR, SELECTORS["pagination_links"])
            for link in pagination_links:
                if link.get_attribute("href"):
                    page_urls.add(link.get_attribute("href"))
        except NoSuchElementException:
            pass
        
        for page in sorted(list(page_urls)):
            driver.get(page)
            product_cards = WebDriverWait(driver, WAIT_TIMEOUT).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, SELECTORS["product_card"])))
            for card in product_cards:
                link = card.find_element(By.CSS_SELECTOR, SELECTORS["product_title_link"])
                url = link.get_attribute("href")
                if url not in processed_urls:
                    basic_product_info.append({"titulo": clean_product_title(link.text), "url_produto": url, "categoria": category.split('/')[-1]})
                    processed_urls.add(url)
        
        new_products_to_scrape = [p for p in basic_product_info if p["url_produto"] not in existing_products]

        if not new_products_to_scrape:
            print("✅ Nenhum produto novo encontrado.")
            continue
            
        print(f"🟡 Encontrados {len(new_products_to_scrape)} produtos novos. Coletando detalhes...")
        added_products = []
        for product in tqdm(new_products_to_scrape, desc="Adicionando novos", unit="produto"):
            details = get_product_details(driver, product["url_produto"])
            product.update(details)
            if product["tamanhos"]:
                added_products.append(product)
            else:
                print(f"\n  - Info: Produto novo '{product['titulo']}' ignorado (sem tamanhos/estoque).")

        if added_products:
            final_product_list = list(existing_products.values()) + added_products
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_product_list, f, ensure_ascii=False, indent=2)
            print(f"✅ Arquivo '{output_filename}' atualizado com {len(added_products)} novos produtos em estoque.")
        else:
            print("✅ Nenhum produto novo com estoque foi adicionado.")


def run_update_mode(driver: webdriver.Chrome):
    """MODO ATUALIZAR: Varre todos os arquivos JSON e atualiza o estoque e imagens de cada produto."""
    print("🚀 Iniciando em modo 'atualizar': verificando estoque e imagens de todos os produtos existentes.")
    json_files = list(OUTPUT_DIR.glob("*.json"))
    if not json_files:
        print("Nenhum arquivo JSON encontrado para atualizar.")
        return

    for file_path in json_files:
        print(f"\n--- Atualizando arquivo: {file_path.name} ---")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                produtos = json.load(f)
        except json.JSONDecodeError:
            print(f"  - Erro: Arquivo '{file_path.name}' está corrompido. Pulando.")
            continue
        
        produtos_atualizados = []
        produtos_removidos_count = 0
        for produto in tqdm(produtos, desc=f"Verificando {file_path.name}", unit="produto"):
            details = get_product_details(driver, produto["url_produto"])
            
            # Atualiza sempre as imagens e os tamanhos
            produto["imagens"] = details["imagens"]
            produto["tamanhos"] = details["tamanhos"]
            
            is_bone = 'boné' in produto.get('categoria', '').lower()
            
            # Mantém o produto se ele tiver tamanhos, imagens ou for um boné (que pode não ter tamanho)
            if produto["tamanhos"] or is_bone or produto["imagens"]:
                produtos_atualizados.append(produto)
            else:
                print(f"\n❌ Produto esgotado e removido: {produto['titulo']}")
                produtos_removidos_count += 1
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(produtos_atualizados, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Arquivo '{file_path.name}' salvo com {len(produtos_atualizados)} produtos.")
        if produtos_removidos_count > 0:
            print(f"  - {produtos_removidos_count} produto(s) removido(s) por falta de estoque/imagens.")

def main():
    """Função principal que interpreta os argumentos e executa o modo correto."""
    parser = argparse.ArgumentParser(description="Gerenciador de Catálogo StarkWear.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        '--modo', 
        type=str, 
        default='adicionar', 
        choices=['adicionar', 'atualizar'],
        help="Modo de operação:\n"
             "  adicionar  - (Rápido) Busca apenas produtos novos nas categorias.\n"
             "  atualizar  - (Completo) Verifica estoque e imagens de todos os produtos."
    )
    args = parser.parse_args()

    driver = setup_driver()
    start_time = time.time()
    try:
        if args.modo == 'adicionar':
            run_add_mode(driver)
        elif args.modo == 'atualizar':
            run_update_mode(driver)
    finally:
        driver.quit()
        end_time = time.time()
        print(f"\n🎉 Operação concluída em {end_time - start_time:.2f} segundos. Navegador fechado.")

if __name__ == "__main__":
    main()