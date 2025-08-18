    document.addEventListener('DOMContentLoaded', () => {
        let produtos = [];
        let carrinho = [];
        let filtros = { tipo: 'all', valor: 'Todos', tamanhos: [], pesquisa: '' };

        const WHATSAPP_NUMBER = '5551990106279';
        const dataPath = 'data/';
        
        const produtosGrid = document.getElementById('produtos-grid');
        const contadorProdutosEl = document.getElementById('contador-produtos');
        
        const btnCarrinhoDesktop = document.getElementById('btn-carrinho');
        const carrinhoSidebar = document.getElementById('carrinho-sidebar');
        const fecharCarrinho = document.getElementById('fechar-carrinho');
        const carrinhoItensEl = document.getElementById('carrinho-itens');
        const carrinhoVazioEl = document.getElementById('carrinho-vazio');
        const contadorCarrinhoEl = document.getElementById('contador-carrinho');
        const btnFinalizarCompra = document.getElementById('btn-finalizar-compra');
        
        const btnMobileFiltros = document.getElementById('btn-mobile-filtros');
        const btnMobileCarrinho = document.getElementById('btn-mobile-carrinho');
        const mobileContadorCarrinhoEl = document.getElementById('mobile-contador-carrinho');
        const filtrosMobilePanel = document.getElementById('filtros-mobile-panel');
        const fecharFiltros = document.getElementById('fechar-filtros');
        
        const overlay = document.getElementById('overlay');
        const toastContainer = document.getElementById('toast-container');
        const zoomModal = document.getElementById('zoom-modal');
        const zoomModalImg = zoomModal.querySelector('img');
        const zoomModalClose = zoomModal.querySelector('.zoom-modal-close');

        const showToast = (message) => {
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = message;
            toastContainer.appendChild(toast);
            setTimeout(() => { toast.remove(); }, 3000);
        };

        const toggleCarrinho = () => {
            const isOpen = carrinhoSidebar.classList.toggle('aberto');
            overlay.classList.toggle('ativo', isOpen || filtrosMobilePanel.classList.contains('aberto'));
        };

        const toggleFiltros = () => {
            const isOpen = filtrosMobilePanel.classList.toggle('aberto');
            overlay.classList.toggle('ativo', isOpen || carrinhoSidebar.classList.contains('aberto'));
        };

        const openZoomModal = (src) => {
            zoomModalImg.src = src;
            zoomModal.classList.add('visible');
        };

        const closeZoomModal = () => {
            zoomModal.classList.remove('visible');
        };

        const adicionarAoCarrinho = (produtoId, tamanho) => {
            const produto = produtos.find(p => p.url_produto === produtoId);
            if (!produto) return;
            const carrinhoItemId = `${produtoId}-${tamanho}`;
            if (carrinho.some(item => item.id === carrinhoItemId)) {
                showToast('Este item já está no seu carrinho!');
                return;
            }
            carrinho.push({ id: carrinhoItemId, produtoId, titulo: produto.titulo, tamanho, imagem: produto.imagens[0] || '', preco: produto.preco });
            renderizarCarrinho();
            showToast(`"${produto.titulo}" adicionado ao carrinho!`);
        };

        const removerDoCarrinho = (carrinhoItemId) => {
            carrinho = carrinho.filter(item => item.id !== carrinhoItemId);
            renderizarCarrinho();
        };

      const renderizarCarrinho = () => {
            const btnLimparCarrinho = document.getElementById('btn-limpar-carrinho');

            carrinhoItensEl.innerHTML = '';
            carrinhoVazioEl.style.display = carrinho.length === 0 ? 'block' : 'none';
            
            // Mostra ou esconde os botões do footer
            if (carrinho.length > 0) {
                btnFinalizarCompra.style.display = 'block';
                btnLimparCarrinho.style.display = 'block';

                carrinho.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'carrinho-item';
                    itemDiv.innerHTML = `<img src="${item.imagem}" alt="${item.titulo}"><div class="carrinho-item-info"><h4>${item.titulo}</h4><p>Tamanho: ${item.tamanho}</p></div><button class="carrinho-remover-item" data-id="${item.id}">&times;</button>`;
                    carrinhoItensEl.appendChild(itemDiv);
                });
            } else {
                btnFinalizarCompra.style.display = 'none';
                btnLimparCarrinho.style.display = 'none';
            }

            contadorCarrinhoEl.textContent = carrinho.length;
            mobileContadorCarrinhoEl.textContent = carrinho.length;
            atualizarLinkWhatsApp();
            carrinhoItensEl.querySelectorAll('.carrinho-remover-item').forEach(button => button.addEventListener('click', (e) => removerDoCarrinho(e.target.dataset.id)));
        };

        // Nova função para limpar o carrinho
        const limparCarrinho = () => {
            // Em vez de 'confirm()', agora chamamos nossa função customizada
            showConfirmModal('Tem certeza que deseja remover todos os itens do carrinho?', () => {
                carrinho = []; // Esvazia o array
                renderizarCarrinho(); // Atualiza a interface
                showToast('Carrinho esvaziado com sucesso!');
            });
        };

        // Adicione esta nova função de controle da modal em algum lugar perto das outras funções de UI
        const showConfirmModal = (message, onConfirm) => {
            const confirmModal = document.getElementById('confirm-modal');
            const confirmText = document.getElementById('confirm-modal-text');
            const btnOk = document.getElementById('confirm-btn-ok');
            const btnCancel = document.getElementById('confirm-btn-cancel');

            confirmText.textContent = message;
            confirmModal.classList.add('visible');

            // Criamos uma função 'handler' para poder removê-la depois
            const handleOkClick = () => {
                onConfirm(); // Executa a ação de confirmação
                close();
            };
            
            const close = () => {
                confirmModal.classList.remove('visible');
                // IMPORTANTE: Removemos os listeners para evitar múltiplos cliques
                btnOk.removeEventListener('click', handleOkClick);
                btnCancel.removeEventListener('click', close);
            };

            btnOk.addEventListener('click', handleOkClick);
            btnCancel.addEventListener('click', close);
        };

        // Adiciona o listener de evento ao novo botão
        document.getElementById('btn-limpar-carrinho').addEventListener('click', limparCarrinho);

        const atualizarLinkWhatsApp = () => {
            btnFinalizarCompra.style.display = carrinho.length === 0 ? 'none' : 'block';
            if (carrinho.length === 0) return;
            let mensagem = "Olá, gostaria de fazer um pedido com os seguintes itens:\n\n";
            let total = 0;
            carrinho.forEach(item => {
                const precoItem = item.preco ? ` (${new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.preco)})` : '';
                mensagem += `- *${item.titulo}*${precoItem}\n  Tamanho: ${item.tamanho}\n`;
                if (item.preco) total += item.preco;
            });
            mensagem += `\n*Total estimado: ${new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(total)}*`;
            mensagem += "\n\nObrigado!";
            btnFinalizarCompra.href = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(mensagem)}`;
        };
        
        const renderizarProdutos = (showLoading = true) => {
            if (showLoading) {
                renderizarSkeletons();
            }

            setTimeout(() => {
                const produtosFiltrados = produtos.filter(p => {
                    const matchPesquisa = filtros.pesquisa === '' || p.titulo.toLowerCase().includes(filtros.pesquisa);
                    const matchTamanho = filtros.tamanhos.length === 0 || (p.tamanhos && p.tamanhos.some(t => filtros.tamanhos.includes(t)));
                    if (!matchPesquisa || !matchTamanho) return false;
                    if (filtros.tipo === 'all') return true;
                    if (filtros.tipo === 'group') {
                        if (Array.isArray(filtros.valor)) { return filtros.valor.includes(p.categoria); }
                        return p.categoria.startsWith(filtros.valor);
                    }
                    if (filtros.tipo === 'exact') return p.categoria === filtros.valor;
                    return true;
                });

                produtosGrid.innerHTML = '';
                contadorProdutosEl.textContent = `${produtosFiltrados.length} produtos encontrados`;

                if (produtosFiltrados.length === 0) {
                    produtosGrid.innerHTML = '<p>Nenhum produto encontrado com os filtros selecionados.</p>';
                } else {
                    produtosFiltrados.forEach(produto => {
                        const card = document.createElement('div');
                        card.className = 'produto-card';
                        card.dataset.id = produto.url_produto;
                        const precoFormatado = produto.preco ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(produto.preco) : '';
                        const hasSizes = produto.tamanhos && produto.tamanhos.length > 0;
                        let actionsHTML = '';
                        if (hasSizes) {
                            const tamanhosOptions = produto.tamanhos.map(t => `<option value="${t}">${t}</option>`).join('');
                            actionsHTML = `<select class="produto-tamanho-select"><option value="">Selecione o tamanho</option>${tamanhosOptions}</select><button class="btn-adicionar-carrinho">Adicionar</button>`;
                        } else {
                            actionsHTML = `<button class="btn-adicionar-carrinho">Adicionar ao Carrinho</button>`;
                        }
                        card.innerHTML = `<img src="${produto.imagens[0] || ''}" alt="${produto.titulo}" class="produto-imagem" loading="lazy">
                        <div class="produto-info"><h3 class="produto-titulo">${produto.titulo}</h3>${precoFormatado ? `<div class="produto-preco">${precoFormatado}</div>` : ''}<div class="produto-actions">${actionsHTML}</div></div>`;
                        produtosGrid.appendChild(card);
                    });
                }
                
                adicionarListenersAosCards();
            }, 200);
        };
        
        const renderizarSkeletons = () => {
            produtosGrid.innerHTML = '';
            const skeletonCount = 9;
            for (let i = 0; i < skeletonCount; i++) {
                const skeleton = document.createElement('div');
                skeleton.className = 'skeleton-card';
                skeleton.innerHTML = `
                    <div class="skeleton-img"></div>
                    <div style="padding: 20px;">
                        <div class="skeleton-text" style="width: 80%;"></div>
                        <div class="skeleton-text" style="width: 40%;"></div>
                        <div class="skeleton-text" style="width: 100%; height: 40px; margin-top: 20px;"></div>
                    </div>
                `;
                produtosGrid.appendChild(skeleton);
            }
        };

        const adicionarListenersAosCards = () => {
            produtosGrid.querySelectorAll('.btn-adicionar-carrinho').forEach(button => {
                button.addEventListener('click', (e) => {
                    const card = e.target.closest('.produto-card');
                    const produtoId = card.dataset.id;
                    const selectTamanho = card.querySelector('.produto-tamanho-select');
                    let tamanhoSelecionado = 'Único';
                    if (selectTamanho) {
                        if (!selectTamanho.value) { showToast('Por favor, selecione um tamanho.'); return; }
                        tamanhoSelecionado = selectTamanho.value;
                    }
                    adicionarAoCarrinho(produtoId, tamanhoSelecionado);
                });
            });
            produtosGrid.querySelectorAll('.produto-imagem').forEach(img => {
                img.addEventListener('click', (e) => { openZoomModal(e.target.src); });
            });
        };

        const limparFiltros = () => {
            filtros = { tipo: 'all', valor: 'Todos', tamanhos: [], pesquisa: '' };
            document.querySelectorAll('.barra-pesquisa input').forEach(input => input.value = '');
            popularFiltros(); 
            renderizarProdutos();
            showToast('Filtros limpos!');
        };

        const popularFiltros = () => {
            const categoriasUnicas = [...new Set(produtos.map(p => p.categoria))].filter(Boolean);
            const filterStructure = {
                'Bermudas': { prefix: 'Bermuda', subcategories: [] }, 'Calças': { prefix: 'Calça', subcategories: [] },
                'Camisetas': { prefix: 'Camiseta', subcategories: [] }, 'Jaquetas': { prefix: 'Jaqueta', subcategories: [] },
                'Inverno': { isComplex: true, subcategories: [] }
            };
            const topLevelCategories = { 'Bonés': 'Boné' };
            const invernoCats = ['Moletom com Capuz', 'Moletom sem Capuz', 'Suéter'];

            categoriasUnicas.forEach(cat => {
                if (invernoCats.includes(cat)) { filterStructure.Inverno.subcategories.push(cat); } 
                else if (cat.startsWith(filterStructure.Jaquetas.prefix)) { filterStructure.Jaquetas.subcategories.push(cat); } 
                else if (cat.startsWith(filterStructure.Bermudas.prefix)) { filterStructure.Bermudas.subcategories.push(cat); } 
                else if (cat.startsWith(filterStructure.Calças.prefix)) { filterStructure.Calças.subcategories.push(cat); } 
                else if (cat.startsWith(filterStructure.Camisetas.prefix)) { filterStructure.Camisetas.subcategories.push(cat); }
            });

            let filtrosCategoriasHTML = `<button class="filtro-btn ativo" data-filter-type="all" data-filter-value="Todos">Todos</button>`;
            for (const groupName in filterStructure) {
                const group = filterStructure[groupName];
                if (group.subcategories.length > 0) {
                    const subItemsHTML = group.subcategories.sort().map(sub => {
                        let displayName = sub.replace(group.prefix || '', '').trim();
                        if (group.isComplex || groupName === 'Jaquetas') displayName = sub;
                        return `<button class="filtro-btn subcategoria" data-filter-type="exact" data-filter-value="${sub}">${displayName}</button>`;
                    }).join('');
                    const groupValue = group.isComplex ? JSON.stringify(group.subcategories) : group.prefix;
                    filtrosCategoriasHTML += `<details class="filtro-group"><summary class="filtro-group-summary" data-filter-type="group" data-filter-value='${groupValue}'>${groupName}</summary><div class="subcategory-list">${subItemsHTML}</div></details>`;
                }
            }
            for (const name in topLevelCategories) {
                if (categoriasUnicas.includes(topLevelCategories[name])) {
                     filtrosCategoriasHTML += `<button class="filtro-btn" data-filter-type="exact" data-filter-value="${topLevelCategories[name]}">${name}</button>`;
                }
            }
            const btnLimparHTML = `<button class="filtro-btn btn-limpar-filtros">Limpar Filtros</button>`;

            const desktopPanel = document.querySelector('.filtros-sidebar');
            desktopPanel.innerHTML = `<h2>Filtros</h2><div class="barra-pesquisa"><input type="text" id="pesquisa-desktop" placeholder="Pesquisar produto..."></div><div class="filtro"><h3>Categorias</h3><div id="lista-categorias-desktop"></div></div><div class="filtro"><h3>Tamanhos</h3><div id="lista-tamanhos-desktop"></div></div>`;
            document.getElementById('lista-categorias-desktop').innerHTML = filtrosCategoriasHTML + btnLimparHTML;

            const mobilePanel = document.querySelector('.filtros-mobile-panel .panel-body');
            mobilePanel.innerHTML = `<div class="barra-pesquisa"><input type="text" id="pesquisa-mobile" placeholder="Pesquisar produto..."></div><div class="filtro"><h3>Categorias</h3><div id="lista-categorias-mobile"></div></div><div class="filtro"><h3>Tamanhos</h3><div id="lista-tamanhos-mobile"></div></div>`;
            document.getElementById('lista-categorias-mobile').innerHTML = filtrosCategoriasHTML + btnLimparHTML;
            
            document.querySelectorAll('.btn-limpar-filtros').forEach(btn => btn.addEventListener('click', limparFiltros));
            document.querySelectorAll('button[data-filter-type], summary[data-filter-type]').forEach(item => {
                item.addEventListener('click', (e) => {
                    const currentTarget = e.currentTarget;
                    if (currentTarget.tagName !== 'SUMMARY') { e.preventDefault(); }
                    document.querySelectorAll('.ativo').forEach(el => el.classList.remove('ativo'));
                    currentTarget.classList.add('ativo');
                    filtros.tipo = currentTarget.dataset.filterType;
                    let value = currentTarget.dataset.filterValue;
                    try { filtros.valor = JSON.parse(value); } catch { filtros.valor = value; }
                    renderizarProdutos();
                    if (filtrosMobilePanel.classList.contains('aberto')) { toggleFiltros(); }
                });
            });
            
            const tamanhos = [...new Set(produtos.flatMap(p => p.tamanhos || []))].sort();
            const tamanhosHTML = tamanhos.map(t => `<button class="filtro-btn filtro-btn-tamanho" data-tamanho="${t}">${t}</button>`).join('');
            document.getElementById('lista-tamanhos-desktop').innerHTML = tamanhosHTML;
            document.getElementById('lista-tamanhos-mobile').innerHTML = tamanhosHTML;

            document.querySelectorAll('[data-tamanho]').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.currentTarget.classList.toggle('ativo');
                    const tamanho = e.currentTarget.dataset.tamanho;
                    filtros.tamanhos = e.currentTarget.classList.contains('ativo') ? [...filtros.tamanhos, tamanho] : filtros.tamanhos.filter(t => t !== tamanho);
                    renderizarProdutos();
                });
            });
            
            const pesquisaDesktop = document.getElementById('pesquisa-desktop');
            const pesquisaMobile = document.getElementById('pesquisa-mobile');
            const syncPesquisa = (e) => {
                const valor = e.target.value;
                pesquisaDesktop.value = valor;
                pesquisaMobile.value = valor;
                filtros.pesquisa = valor.toLowerCase();
                renderizarProdutos(false);
            };
            pesquisaDesktop.addEventListener('input', syncPesquisa);
            pesquisaMobile.addEventListener('input', syncPesquisa);
        };

        const carregarTodosProdutos = async () => {
            renderizarSkeletons();
            const jsonFiles = [
                'bermudas_berm-jeans.json', 'bermudas_berm-linho.json', 'bermudas_berm-moletom.json',
                'bermudas_berm-sarja.json', 'bermudas_mauricinho-linho.json', 'bonés.json',
                'calcas_jean.json', 'calcas_sarja.json', 'camisa-social.json','camisetas_cotton-egipcio.json',
                'camisetas_algodao-egipcio.json', 'camisetas_importacao.json', 'camisetas_manga-longa.json',
                'camisetas_naciona.json', 'camisetas_overs.json', 'camisetas_pi.json', 'camisetas_seda-pi.json',
                'gola-polo_premium.json', 'camisetas_tamanhos-especiais.json', '_inverno_jaquetas-bobojaco.json',
                'inverno_calca-moletom.json', 'inverno_casaco-de-moletom_moletom-com-capuz.json',
                'inverno_casaco-de-moletom_moletom-sem-capuz.json', 'inverno_sueter.json'
            ];
            const priceMap = {
                'bermudas_berm-jeans': 100.00, 'bermudas_berm-linho': 69.00, 'bermudas_berm-moletom': 69.00,
                'bermudas_berm-sarja': 95.00, 'bermudas_mauricinho-linho': 85.00, 'bonés': 60.00,
                'calcas_jean': 120.00, 'calcas_sarja': 120.00, 'camisa-social': 150.00, 'camisetas_cotton-egipcio': 85.00,
                'camisetas_algodao-egipcio': 120.00, 'camisetas_importacao': 120.00, 'camisetas_manga-longa': 85.00,
                'camisetas_naciona': 75.00, 'camisetas_overs': 95.00, 'camisetas_pi': 85.00,
                'camisetas_seda-pi': 85.00, 'gola-polo_premium': 120.00, 'camisetas_tamanhos-especiais': 100.00,
                'inverno_calca-moletom': 89.00,
                'inverno_casaco-de-moletom_moletom-com-capuz': 210.00, 'inverno_casaco-de-moletom_moletom-sem-capuz': 160.00,
                'inverno_sueter': 189.90,
                'Jaqueta Puffer': 310.00, 'Jaqueta Impermeável': 230.00, 'Jaqueta Social': 265.00, 'Jaqueta Outras': 200.00
            };
            const getCategoryName = (filename) => {
                const key = filename.replace('.json', '');
                const categoryMap = {
                    'bermudas_berm-jeans': 'Bermuda Jeans', 'bermudas_berm-linho': 'Bermuda Linho', 'bermudas_berm-moletom': 'Bermuda Moletom', 'bermudas_berm-sarja': 'Bermuda Sarja', 'bermudas_mauricinho-linho': 'Bermuda Mauricinho Linho', 'bonés': 'Boné',
                    'calcas_jean': 'Calça Jeans', 'calcas_sarja': 'Calça Sarja',
                    'camisa-social': 'Camisa Social', 'camisetas_cotton-egipcio': 'Camiseta Algodão Egípcio',
                    'camisetas_algodao-egipcio': 'Camiseta Algodão Egípcio', 'camisetas_importacao': 'Camiseta Importada', 'camisetas_manga-longa': 'Camiseta Manga Longa', 'camisetas_naciona': 'Camiseta Nacional', 'camisetas_overs': 'Camiseta Oversized', 'camisetas_pi': 'Camiseta Pima', 'camisetas_seda-pi': 'Camiseta Seda Pima', 'gola-polo_premium': 'Camiseta Gola Polo', 'camisetas_tamanhos-especiais': 'Camiseta Plus Size',
                    'inverno_calca-moletom': 'Calça Moletom', 'inverno_casaco-de-moletom_moletom-com-capuz': 'Moletom com Capuz', 'inverno_casaco-de-moletom_moletom-sem-capuz': 'Moletom sem Capuz', 'inverno_sueter': 'Suéter'
                };
                return categoryMap[key] || key.replace(/[-_]/g, ' ');
            };
            const loadJSON = async (file) => {
                try {
                    const response = await fetch(dataPath + file);
                    if (!response.ok) { return []; }
                    return await response.json();
                } catch (error) { return []; }
            };

            const promessas = jsonFiles.map(async file => {
                const data = await loadJSON(file);
                if (!Array.isArray(data)) return [];
                if (file === '_inverno_jaquetas-bobojaco.json') {
                    return data.map(produto => {
                        const titulo = produto.titulo.toUpperCase();
                        let categoria;
                        if (titulo.includes('IMPERMEAVEL')) { categoria = 'Jaqueta Impermeável'; } 
                        else if (titulo.includes('PELUCIADA') || titulo.includes('PUFFER')) { categoria = 'Jaqueta Puffer'; } 
                        else if (titulo.includes('SOCIAL')) { categoria = 'Jaqueta Social'; } 
                        else if (titulo.includes('NEOPRENE')) { categoria = 'Jaqueta Outras'; } 
                        else { categoria = 'Jaqueta Puffer'; }
                        const preco = priceMap[categoria];
                        return { ...produto, categoria, preco };
                    });
                }
                const fileKey = file.replace('.json', '');
                const categoria = getCategoryName(file);
                const preco = priceMap[fileKey];
                return data.map(p => ({ ...p, categoria, preco }));
            });
            produtos = (await Promise.all(promessas)).flat();
            
            popularFiltros();
            renderizarProdutos(false);
            renderizarCarrinho();
        };

        // Event Listeners
        btnCarrinhoDesktop.addEventListener('click', toggleCarrinho);
        fecharCarrinho.addEventListener('click', toggleCarrinho);
        btnMobileFiltros.addEventListener('click', toggleFiltros);
        fecharFiltros.addEventListener('click', toggleFiltros);
        btnMobileCarrinho.addEventListener('click', toggleCarrinho);
        overlay.addEventListener('click', () => {
            if (carrinhoSidebar.classList.contains('aberto')) toggleCarrinho();
            if (filtrosMobilePanel.classList.contains('aberto')) toggleFiltros();
        });
        zoomModalClose.addEventListener('click', closeZoomModal);
        zoomModal.addEventListener('click', (e) => {
            if (e.target === zoomModal) { closeZoomModal(); }
        });
        
        carregarTodosProdutos();
    });