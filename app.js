const fs = require('fs');
const path = require('path');
const wppconnect = require('@wppconnect-team/wppconnect');

// Configurações de caminho
const IMAGE_BASE_PATH = 'C:/Users/Gabriel/Documents/Roupas/StarkWear';
const JSON_BASE_PATH = 'C:/Users/Gabriel/Documents/Roupas/Tamanhos';

// Verificação de diretórios
if (!fs.existsSync(IMAGE_BASE_PATH)) {
  console.error('ERRO: Diretório de imagens não encontrado:', IMAGE_BASE_PATH);
  process.exit(1);
}

if (!fs.existsSync(JSON_BASE_PATH)) {
  try {
    fs.mkdirSync(JSON_BASE_PATH, { recursive: true });
    console.log(`Diretório criado: ${JSON_BASE_PATH}`);
  } catch (err) {
    console.error('ERRO ao criar diretório:', err);
    process.exit(1);
  }
}

// Funções auxiliares
function isImage(fileName) {
  const ext = path.extname(fileName).toLowerCase();
  return ['.jpg', '.jpeg', '.png', '.webp'].includes(ext);
}

function normalizeString(str) {
  if (!str) return '';
  return str.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9 ]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function getAllSubfolders(dir) {
  let results = [];
  try {
    const list = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of list) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        results.push(fullPath);
        results = results.concat(getAllSubfolders(fullPath));
      }
    }
  } catch (err) {
    console.error(`Erro ao ler diretório ${dir}:`, err);
  }
  return results;
}

function getAllImages(dir) {
  let results = [];
  const folders = getAllSubfolders(dir);
  for (const folder of folders) {
    try {
      const files = fs.readdirSync(folder);
      files.forEach(file => {
        if (isImage(file)) {
          results.push({
            path: path.join(folder, file),
            name: path.basename(file, path.extname(file))
          });
        }
      });
    } catch (err) {
      console.error(`Erro ao ler imagens em ${folder}:`, err);
    }
  }
  return results;
}

function findJsonForProduct(productName) {
  console.log(`\n[Busca JSON] Iniciando busca por: "${productName}"`);
  const normalizedSearch = normalizeString(productName);
  const searchTerms = normalizedSearch.split(' ').filter(term => term.length > 0);
  console.log(`Termos de busca:`, searchTerms);

  let jsonFiles = [];
  try {
    jsonFiles = fs.readdirSync(JSON_BASE_PATH)
      .filter(file => path.extname(file).toLowerCase() === '.json')
      .map(file => path.join(JSON_BASE_PATH, file));
  } catch (err) {
    console.error(`Erro ao ler JSONs em ${JSON_BASE_PATH}:`, err);
    return [];
  }

  console.log(`Total de JSONs encontrados: ${jsonFiles.length}`);

  const matchedFiles = jsonFiles.filter(jsonFile => {
    const fileName = path.basename(jsonFile, '.json');
    const normalizedFileName = normalizeString(fileName);
    console.log(`\nAnalisando JSON: ${fileName}`);

    const matchScore = searchTerms.reduce((score, term) => {
      const hasTerm = normalizedFileName.includes(term);
      console.log(`- Termo "${term}": ${hasTerm ? 'OK' : 'Não encontrado'}`);
      return hasTerm ? score + 1 : score;
    }, 0);

    console.log(`Pontuação de correspondência: ${matchScore}/${searchTerms.length}`);
    return matchScore > 0;
  });

  console.log(`JSONs correspondentes encontrados: ${matchedFiles.length}`);
  return matchedFiles;
}

function findProductInJson(jsonPath, searchName) {
  console.log(`\n[Análise JSON] Buscando produto em: ${jsonPath}`);
  console.log(`Termo buscado: "${searchName}"`);

  let fileContent, produtos;
  try {
    fileContent = fs.readFileSync(jsonPath, 'utf-8').trim();
    produtos = JSON.parse(fileContent);
  } catch (err) {
    console.error(`Erro ao ler/parsear JSON ${jsonPath}:`, err);
    return null;
  }

  const produtosArray = Array.isArray(produtos) ? produtos : [produtos];
  console.log(`Total de produtos no JSON: ${produtosArray.length}`);

  const normalizedSearch = normalizeString(searchName);
  const searchTerms = normalizedSearch.split(' ').filter(term => term.length > 0);
  console.log(`Termos de busca normalizados:`, searchTerms);

  for (const [index, produto] of produtosArray.entries()) {
    const productName = produto.product_name || produto.titulo || produto.nome || '';
    const normalizedProduct = normalizeString(productName);
    console.log(`\nProduto #${index + 1}: ${productName}`);
    console.log(`Nome normalizado: ${normalizedProduct}`);

    const matchScore = searchTerms.reduce((score, term) => {
      const hasTerm = normalizedProduct.includes(term);
      console.log(`- Termo "${term}": ${hasTerm ? 'OK' : 'Não encontrado'}`);
      return hasTerm ? score + 1 : score;
    }, 0);

    if (matchScore === searchTerms.length) {
      console.log('✔ Todos os termos correspondem! Produto encontrado.');
      return produto;
    }

    console.log(`Pontuação: ${matchScore}/${searchTerms.length}`);
  }

  console.log('✖ Nenhum produto corresponde a todos os termos');
  return null;
}

function findBestImageMatch(baseDir, modelName) {
  console.log(`\n[Busca Imagens] Iniciando busca por: "${modelName}"`);
  const images = getAllImages(baseDir);
  console.log(`Total de imagens disponíveis: ${images.length}`);

  const normalizedSearch = normalizeString(modelName);
  const searchTerms = normalizedSearch.split(' ').filter(term => term.length > 0);
  console.log(`Termos de busca:`, searchTerms);

  let bestMatch = null;
  let bestScore = 0;

  for (const image of images) {
    const normalizedImage = normalizeString(image.name);
    console.log(`\nAnalisando imagem: ${image.name}`);
    console.log(`Nome normalizado: ${normalizedImage}`);

    const score = searchTerms.reduce((total, term) => {
      const hasTerm = normalizedImage.includes(term);
      console.log(`- Termo "${term}": ${hasTerm ? 'OK' : 'Não encontrado'}`);
      return hasTerm ? total + term.length : total;
    }, 0);

    console.log(`Pontuação: ${score}`);

    if (score > bestScore || (score === bestScore && image.name.length < (bestMatch?.name.length || Infinity))) {
      bestScore = score;
      bestMatch = image;
      console.log(`Nova melhor correspondência!`);
    }
  }

  if (bestMatch) {
    console.log(`\nMelhor correspondência encontrada:`);
    console.log(`Arquivo: ${bestMatch.path}`);
    console.log(`Nome: ${bestMatch.name}`);
    console.log(`Pontuação: ${bestScore}/${searchTerms.reduce((a, b) => a + b.length, 0)}`);
  } else {
    console.log('Nenhuma imagem correspondente encontrada');
  }

  return bestMatch;
}

async function handleModelNotFound(client, user, searchTerm) {
  console.log(`\n[Feedback] Modelo não encontrado: "${searchTerm}"`);
  const images = getAllImages(IMAGE_BASE_PATH);
  const normalizedSearch = normalizeString(searchTerm);
  const searchTerms = normalizedSearch.split(' ').filter(term => term.length > 0);

  const suggestions = images
    .map(img => ({
      name: img.name.replace(/[-_]/g, ' ').trim(),
      score: searchTerms.reduce((acc, term) => 
        normalizeString(img.name).includes(term) ? acc + term.length : acc, 0)
    }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map(item => `• ${item.name}`);

  let response = 'Não encontrei esse modelo exato. Verifique se o nome está correto.';
  
  if (suggestions.length > 0) {
    response += '\n\nTalvez você queira um desses:\n' + suggestions.join('\n');
    console.log(`Sugestões enviadas:`, suggestions);
  } else {
    console.log('Nenhuma sugestão disponível');
  }

  await client.sendText(user, response);
}

// Configuração do WhatsApp
let conversationState = {};

wppconnect.create({
  session: 'StarkWearSession',
  catchQR: (base64Qr, asciiQR) => {
    console.log('Leia o QR Code abaixo para autenticar:');
    console.log(asciiQR);
  },
  logQR: false,
  headless: true,
  browserArgs: ['--no-sandbox'],
  puppeteerOptions: {
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  },
  autoClose: false,
  statusFind: (statusSession, session) => {
    console.log('Status da sessão:', statusSession);
  }
}).then((client) => start(client)).catch((error) => console.error('Erro na inicialização:', error));

// Função principal
function start(client) {
  client.onMessage(async (message) => {
    if (message.from === 'status@broadcast') return;

    const msg = message.body ? message.body.trim() : '';
    const user = message.from;
    if (!msg) return;

    console.log(`\n[Nova mensagem] De: ${user}`);
    console.log(`Conteúdo: "${msg}"`);

    // Início da conversa
    if (msg.toLowerCase() === 'olá, vim pela stark wear') {
      conversationState[user] = { step: 'aguardando_modelo' };
      console.log(`Iniciando nova conversa com ${user}`);
      await client.sendText(user, 'Olá, tudo bem? Qual seria o modelo que deseja ver?');
      return;
    }

    const state = conversationState[user];
    if (!state) {
      console.log(`Mensagem de ${user} sem estado - ignorando`);
      return;
    }

    console.log(`Estado atual: ${state.step}`);

    // Etapa 1: Busca do modelo
    if (state.step === 'aguardando_modelo') {
      console.log(`\n[Processamento] Buscando modelo: "${msg}"`);
      const bestImage = findBestImageMatch(IMAGE_BASE_PATH, msg);
      
      if (!bestImage) {
        console.log(`Nenhuma imagem encontrada para "${msg}"`);
        await handleModelNotFound(client, user, msg);
        return;
      }

      console.log(`\n[Buscando informações do produto]`);
      const jsonFiles = findJsonForProduct(bestImage.name);
      let produto = null;
      let jsonPath = null;

      for (const file of jsonFiles) {
        produto = findProductInJson(file, bestImage.name);
        if (produto) {
          jsonPath = file;
          break;
        }
      }

      if (!produto) {
        console.log(`Nenhum produto encontrado para "${bestImage.name}"`);
        await client.sendText(user, 'Modelo encontrado, mas sem informações de tamanho disponíveis.');
        await client.sendImage(user, bestImage.path, path.basename(bestImage.path));
        delete conversationState[user];
        return;
      }

      conversationState[user] = {
        step: 'aguardando_confirmacao',
        imagePath: bestImage.path,
        produto,
        jsonPath
      };

      console.log(`Produto encontrado:`, {
        name: produto.product_name || produto.titulo,
        sizes: produto.sizes || produto.tamanhos
      });

      await client.sendImage(user, bestImage.path, path.basename(bestImage.path), 
        'Este é o modelo. Confirma com "SIM"?');
      return;
    }

    // Etapa 2: Confirmação do modelo
    if (state.step === 'aguardando_confirmacao' && msg.toLowerCase() === 'sim') {
      console.log(`\n[Confirmação] Usuário confirmou o modelo`);
      const tamanhosDisponiveis = state.produto.sizes || state.produto.tamanhos || [];
      const tamanhosNormalizados = tamanhosDisponiveis.map(t => normalizeString(t));

      console.log(`Tamanhos disponíveis:`, tamanhosDisponiveis);

      if (tamanhosDisponiveis.length > 0) {
        conversationState[user] = {
          step: 'aguardando_tamanho',
          produto: state.produto,
          tamanhosDisponiveis: tamanhosNormalizados,
          tentativasTamanho: 0
        };
        await client.sendText(user, `Tamanhos disponíveis: ${tamanhosDisponiveis.join(', ')}`);
        await client.sendText(user, `Por favor, informe o tamanho desejado.`);
      } else {
        console.error('Produto sem tamanhos:', state.produto);
        await client.sendText(user, 'Não encontrei tamanhos disponíveis para esse modelo.');
        delete conversationState[user];
      }
      return;
    }

    // Etapa 3: Validação do tamanho
    if (state.step === 'aguardando_tamanho') {
      const tamanhoInformado = normalizeString(msg);
      const tamanhoValido = state.tamanhosDisponiveis.includes(tamanhoInformado);

      console.log(`\n[Validação de tamanho] Tamanho informado: "${msg}"`);
      console.log(`Tamanho normalizado: "${tamanhoInformado}"`);
      console.log(`Tamanhos válidos:`, state.tamanhosDisponiveis);

      if (!tamanhoValido) {
        state.tentativasTamanho++;
        console.log(`Tamanho inválido - Tentativa ${state.tentativasTamanho}/3`);
        
        if (state.tentativasTamanho >= 3) {
          console.log(`Limite de tentativas atingido para ${user}`);
          await client.sendText(user, 'Número máximo de tentativas atingido. Por favor, inicie novamente.');
          delete conversationState[user];
          return;
        }

        await client.sendText(user, `Tamanho "${msg}" não disponível. Por favor, escolha entre: ${state.produto.sizes || state.produto.tamanhos}`);
        return;
      }

      console.log(`Tamanho válido - Finalizando pedido`);
      const nomeProduto = state.produto.product_name || state.produto.titulo;
      
      await client.sendText(
        user,
        `✅ *Pedido Registrado*\n\n` +
        `*Modelo:* ${nomeProduto}\n` +
        `*Tamanho:* ${msg.toUpperCase()}\n\n` +
        `Aguarde o contato do nosso vendedor para confirmar seu pedido!`
      );
      
      console.log(`Pedido registrado para ${user}:`, {
        modelo: nomeProduto,
        tamanho: msg,
        data: new Date().toISOString()
      });

      delete conversationState[user];
    }
  });
}