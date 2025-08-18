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
    # CORREÇÃO: Seletores de tamanho baseados na sua versão funcional original
    "sizes_selectors": [
        "ul.product_options_list li", # Seletor mais genérico e comum no site
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
    Visita a página de um produto para extrair imagens e tamanhos de forma robusta.
    """
    details = {"imagens": [], "tamanhos": []}
    try:
        driver.get(product_url)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        # 1. Coletar Imagens
        try:
            thumbnails = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, SELECTORS["thumbnail_images"])))
            if thumbnails:
                details["imagens"] = list(set([thumb.get_attribute("data-large-image") for thumb in thumbnails if thumb.get_attribute("data-large-image")]))
        except TimeoutException:
            # Se não houver thumbnails, pega a imagem principal
            try:
                main_image = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["main_image"])))
                if main_image.get_attribute("src"):
                    details["imagens"].append(main_image.get_attribute("src"))
            except TimeoutException:
                 print(f"  - Aviso: Nenhuma imagem encontrada para {product_url}")

        # 2. Coletar Tamanhos (tenta múltiplos seletores em ordem de prioridade)
        found_sizes = []
        for selector in SELECTORS["sizes_selectors"]:
            try:
                size_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if size_elements:
                    found_sizes = [el.text.strip() for el in size_elements if el.text.strip()]
                    break # Para no primeiro seletor que encontrar resultados
            except NoSuchElementException:
                continue
        
        # CORREÇÃO: Garante que os tamanhos sejam únicos usando um set e depois ordena a lista
        if found_sizes:
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
    """MODO ATUALIZAR: Varre todos os arquivos JSON e atualiza o estoque de cada produto."""
    print("🚀 Iniciando em modo 'atualizar': verificando estoque de todos os produtos existentes.")
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
        for produto in tqdm(produtos, desc=f"Verificando {file_path.name}", unit="produto"):
            details = get_product_details(driver, produto["url_produto"])
            
            produto["tamanhos"] = details["tamanhos"]
            produto["imagens"] = details["imagens"]
            
            is_bone = 'boné' in produto.get('categoria', '').lower()
            
            if produto["tamanhos"] or is_bone:
                produtos_atualizados.append(produto)
            else:
                print(f"\n❌ Produto esgotado e removido: {produto['titulo']}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(produtos_atualizados, f, ensure_ascii=False, indent=2)
        print(f"✅ Arquivo '{file_path.name}' salvo com {len(produtos_atualizados)} produtos em estoque.")

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
             "  atualizar  - (Completo) Verifica o estoque de todos os produtos existentes."
    )
    args = parser.parse_args()

    driver = setup_driver()
    try:
        if args.modo == 'adicionar':
            run_add_mode(driver)
        elif args.modo == 'atualizar':
            run_update_mode(driver)
    finally:
        driver.quit()
        print("\n🎉 Operação concluída. Navegador fechado.")

if __name__ == "__main__":
    main()