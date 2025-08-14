import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_DIR = r"C:\Users\Gabriel\Documents\GitHub\StarkWear\api-project"
ARQUIVO_JSON = os.path.join(BASE_DIR, "bermudas_berm-jeans.json")

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=chrome_options)

def get_product_sizes(driver, url):
    try:
        driver.get(url)
        time.sleep(1.2)
        sizes = []
        # Tenta encontrar os tamanhos (ajuste o seletor conforme necessário)
        size_elements = driver.find_elements(By.CSS_SELECTOR, "ul.product_options_list li")
        for el in size_elements:
            size = el.text.strip()
            if size:
                sizes.append(size)
        return sizes
    except Exception:
        return []

def atualizar_tamanhos():
    print("Arquivos encontrados na pasta:")
    print(os.listdir(BASE_DIR))

    # Busca o arquivo correto, ignorando espaços
    for fname in os.listdir(BASE_DIR):
        if fname.strip() == "bermudas_berm-jeans.json":
            ARQUIVO_JSON = os.path.join(BASE_DIR, fname)
            break
    else:
        raise FileNotFoundError("Arquivo bermudas_berm-jeans.json não encontrado na pasta.")

    with open(ARQUIVO_JSON, encoding="utf-8") as f:
        produtos = json.load(f)

    driver = setup_driver()
    produtos_atualizados = []
    for produto in produtos:
        url = produto["url_produto"]
        tamanhos_novos = get_product_sizes(driver, url)
        tamanhos_antigos = produto.get("tamanhos", [])
        if tamanhos_novos:
            if set(tamanhos_novos) != set(tamanhos_antigos):
                produto["tamanhos"] = tamanhos_novos
                print(f"🟢 {produto['titulo']} | Tamanhos atualizados: {', '.join(tamanhos_novos)}")
            else:
                print(f"🟡 {produto['titulo']} | Tamanhos mantidos: {', '.join(tamanhos_antigos)}")
            produtos_atualizados.append(produto)
        else:
            print(f"❌ {produto['titulo']} | Produto esgotado e removido.")

    driver.quit()

    # Salva o JSON atualizado
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(produtos_atualizados, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo {len(produtos_atualizados)} produtos atualizados em {ARQUIVO_JSON}")

def atualizar_todos_jsons():
    print("Arquivos encontrados na pasta:")
    print(os.listdir(BASE_DIR))

    arquivos_json = [f for f in os.listdir(BASE_DIR) if f.endswith(".json")]

    if not arquivos_json:
        print("Nenhum arquivo JSON encontrado na pasta.")
        return

    driver = setup_driver()

    for fname in arquivos_json:
        caminho_json = os.path.join(BASE_DIR, fname)
        print(f"\n--- Atualizando: {fname} ---")
        with open(caminho_json, encoding="utf-8") as f:
            produtos = json.load(f)

        produtos_atualizados = []
        for produto in produtos:
            url = produto["url_produto"]
            tamanhos_novos = get_product_sizes(driver, url)
            tamanhos_antigos = produto.get("tamanhos", [])
            if tamanhos_novos:
                if set(tamanhos_novos) != set(tamanhos_antigos):
                    produto["tamanhos"] = tamanhos_novos
                    print(f"🟢 {produto['titulo']} | Tamanhos atualizados: {', '.join(tamanhos_novos)}")
                else:
                    print(f"🟡 {produto['titulo']} | Tamanhos mantidos: {', '.join(tamanhos_antigos)}")
                produtos_atualizados.append(produto)
            else:
                print(f"❌ {produto['titulo']} | Produto esgotado e removido.")

        # Salva o JSON atualizado
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(produtos_atualizados, f, ensure_ascii=False, indent=2)
        print(f"Salvo {len(produtos_atualizados)} produtos atualizados em {caminho_json}")

    driver.quit()

if __name__ == "__main__":
    atualizar_todos_jsons()