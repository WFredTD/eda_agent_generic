// Arquivo: script.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Referências aos elementos do DOM ---
    const sidebar = document.getElementById('sidebar');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const menuIcon = document.getElementById('menu-icon');
    const closeIcon = document.getElementById('close-icon');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const fileDropArea = document.getElementById('file-drop-area');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    const newChatBtn = document.getElementById('new-chat-btn');

    let uploadedFile = null;
    let isApiConnected = true; // Flag para controlar conexão da API

    // --- Lógica da Barra Lateral Retrátil ---
    const toggleSidebar = () => {
        sidebar.classList.toggle('collapsed');
        
        if (sidebar.classList.contains('collapsed')) {
            toggleSidebarBtn.title = "Abrir Menu";
            menuIcon.style.display = 'block';
            closeIcon.style.display = 'none';
        } else {
            toggleSidebarBtn.title = "Fechar Menu";
            menuIcon.style.display = 'none';
            closeIcon.style.display = 'block';
        }
    };

    toggleSidebarBtn.addEventListener('click', toggleSidebar);

    // Inicializar a sidebar como fechada em telas pequenas
    if (window.innerWidth <= 768) {
        sidebar.classList.add('collapsed');
    }

    // --- Lógica do botão "Novo Chat" ---
    newChatBtn.addEventListener('click', () => {
        // Limpar mensagens
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h1>Olá! Sou seu assistente de análise de dados.</h1>
                <p>Carregue um arquivo CSV e me faça uma pergunta para começar. Posso te ajudar a explorar os dados, gerar gráficos e tirar conclusões.</p>
            </div>
        `;
        
        // Limpar arquivo
        uploadedFile = null;
        fileNameDisplay.textContent = 'Arraste e solte seu arquivo CSV ou ZIP aqui, ou clique para selecionar.';
        fileNameDisplay.classList.remove('file-selected');
        
        // Limpar input
        userInput.value = '';
        
        console.log('Novo chat iniciado');
    });

    // --- Lógica de Drag and Drop e Seleção de Arquivo ---
    fileDropArea.addEventListener('click', () => fileInput.click());
    
    fileDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileDropArea.classList.add('highlight');
    });
    
    fileDropArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        fileDropArea.classList.remove('highlight');
    });
    
    fileDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileDropArea.classList.remove('highlight');
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFile(file);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    });

    const handleFile = (file) => {
        // Verificar se é CSV ou ZIP
        const validTypes = ['text/csv', 'application/zip', 'application/x-zip-compressed'];
        const validExtensions = ['.csv', '.zip'];
        
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        const isValidType = validTypes.includes(file.type) || validExtensions.includes(fileExtension);
        
        if (!isValidType) {
            alert('Por favor, selecione apenas arquivos CSV ou ZIP.');
            return;
        }
        
        uploadedFile = file;
        fileNameDisplay.textContent = `✅ Arquivo selecionado: ${file.name}`;
        fileNameDisplay.classList.add('file-selected');
        console.log('Arquivo carregado:', file.name);
    };

    // --- Lógica de Envio do Formulário e Interação com a API ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = userInput.value.trim();

        if (!question) {
            return;
        }

        if (!uploadedFile) {
            alert("Por favor, selecione um arquivo CSV ou ZIP.");
            return;
        }

        // Adiciona a mensagem do usuário na interface
        addMessageToChat(question, 'user');
        userInput.value = '';

        // Adiciona mensagem de carregamento
        const loadingId = addLoadingMessage();

        // Cria o formulário para enviar o arquivo e a pergunta
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('question', question);

        try {
            console.log('Enviando requisição para API...');
            
            // Chama a API com o arquivo e a pergunta
            const response = await fetch('/chat/', {
                method: 'POST',
                body: formData,
            });

            // Remove mensagem de carregamento
            removeLoadingMessage(loadingId);

            if (!response.ok) {
                let errorMessage = 'Erro desconhecido';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorData.detail || `Erro ${response.status}`;
                } catch {
                    errorMessage = `Erro ${response.status}: ${response.statusText}`;
                }
                
                addMessageToChat(`❌ Erro: ${errorMessage}`, 'agent');
                console.error('Erro na API:', errorMessage);
                return;
            }

            const data = await response.json();
            console.log('Resposta da API recebida:', data);
            
            // Verifica se há erro na resposta
            if (data.error) {
                addMessageToChat(`❌ Erro: ${data.error}`, 'agent');
                return;
            }
            
            // Verifica se a resposta contém uma imagem
            if (data.image_url) {
                addMessageToChat(data.response || "Análise concluída com gráfico!", 'agent', data.image_url);
                console.log('📊 Gráfico recebido:', data.image_url);
            } else {
                // Adiciona a resposta do agente na interface (apenas texto)
                addMessageToChat(data.response || "Análise concluída.", 'agent');
            }

            console.log('Resposta processada com sucesso');

        } catch (error) {
            removeLoadingMessage(loadingId);
            console.error('Erro na comunicação com a API:', error);
            
            let errorMessage = 'Ocorreu um erro ao processar sua solicitação.';
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '🔌 Erro de conexão: Verifique se a API está rodando em http://localhost:8000';
                isApiConnected = false;
            }
            
            addMessageToChat(errorMessage, 'agent');
        }
    });
    
    // Envio da mensagem com a tecla 'Enter'
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Função para adicionar mensagens ao chat
    const addMessageToChat = (text, sender, imageUrl = null) => {
        // Remove mensagem de boas-vindas se existir
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageBox = document.createElement('div');
        messageBox.classList.add('message-box', sender);

        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.textContent = sender === 'user' ? 'Você' : 'AI';

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        // Se há uma imagem, trata de forma especial
        if (imageUrl) {
            const textElement = document.createElement('div');
            textElement.textContent = text;
            messageContent.appendChild(textElement);
            
            const chartContainer = document.createElement('div');
            chartContainer.classList.add('chart-container');
            
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = 'Gráfico gerado';
            img.style.cursor = 'pointer';
            img.title = 'Clique para ver em tela cheia';
            
            // Adiciona evento de clique para abrir modal
            img.addEventListener('click', () => openImageModal(imageUrl));
            
            // Adiciona indicador de carregamento
            const loadingDiv = document.createElement('div');
            loadingDiv.classList.add('image-loading');
            loadingDiv.innerHTML = `
                <div class="loading-spinner"></div>
                <span>Carregando gráfico...</span>
            `;
            
            chartContainer.appendChild(loadingDiv);
            chartContainer.appendChild(img);
            
            // Remove loading quando a imagem carrega
            img.onload = () => {
                loadingDiv.style.display = 'none';
                img.style.display = 'block';
            };
            
            // Trata erro de carregamento
            img.onerror = () => {
                loadingDiv.innerHTML = '❌ Erro ao carregar gráfico';
                loadingDiv.style.background = 'rgba(255, 0, 0, 0.1)';
            };
            
            img.style.display = 'none'; // Inicialmente escondido
            messageContent.appendChild(chartContainer);
        } else {
            messageContent.textContent = text;
        }
        
        messageBox.appendChild(avatar);
        messageBox.appendChild(messageContent);
        chatMessages.appendChild(messageBox);
        
        // Mantém o scroll no final do chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Função para abrir modal de imagem
    const openImageModal = (imageUrl) => {
        const modal = document.getElementById('image-modal');
        const modalImg = document.getElementById('modal-image');
        
        modal.classList.add('active');
        modalImg.src = imageUrl;
        
        // Adiciona classe ao body para prevenir scroll
        document.body.style.overflow = 'hidden';
    };

    // Função para fechar modal de imagem
    const closeImageModal = () => {
        const modal = document.getElementById('image-modal');
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    };

    // Event listeners para o modal
    document.getElementById('modal-close').addEventListener('click', closeImageModal);
    document.getElementById('image-modal').addEventListener('click', (e) => {
        if (e.target.id === 'image-modal') {
            closeImageModal();
        }
    });

    // Fecha modal com ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeImageModal();
        }
    });

    // Função para adicionar mensagem de carregamento
    const addLoadingMessage = () => {
        const messageBox = document.createElement('div');
        messageBox.classList.add('message-box', 'agent');
        const loadingId = 'loading-' + Date.now();
        messageBox.id = loadingId;

        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.textContent = 'AI';

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        messageContent.innerHTML = '⏳ Analisando seus dados...';
        
        messageBox.appendChild(avatar);
        messageBox.appendChild(messageContent);
        chatMessages.appendChild(messageBox);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return loadingId;
    };

    // Função para remover mensagem de carregamento
    const removeLoadingMessage = (loadingId) => {
        const loadingMessage = document.getElementById(loadingId);
        if (loadingMessage) {
            loadingMessage.remove();
        }
    };

    // --- Lógica para o seletor de tema (Dark/Light) ---
    const themeSwitch = document.getElementById('theme-switch');

    // Verifica a preferência do usuário e aplica o tema ao carregar
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'light') {
        document.body.classList.add('light-theme');
        themeSwitch.checked = true;
    }

    // Adiciona o evento de clique para alternar o tema
    themeSwitch.addEventListener('change', () => {
        if (themeSwitch.checked) {
            document.body.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
            console.log('Tema alterado para: claro');
        } else {
            document.body.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
            console.log('Tema alterado para: escuro');
        }
    });

    // --- Função para testar conexão da API ---
    const testApiConnection = async () => {
        try {
            const response = await fetch('http://localhost:8000/', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
            });
            
            if (response.ok) {
                console.log('✅ API conectada com sucesso');
                isApiConnected = true;
                return true;
            } else {
                console.warn('⚠️ API respondeu com status:', response.status);
                isApiConnected = false;
                return false;
            }
        } catch (error) {
            console.error('❌ Erro ao conectar com a API:', error);
            isApiConnected = false;
            return false;
        }
    };

    // --- Gerenciamento de redimensionamento da janela ---
    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
            menuIcon.style.display = 'block';
            closeIcon.style.display = 'none';
        } else {
            // Em telas grandes, pode manter o estado atual
        }
    });

    // --- Inicialização ---
    console.log('🚀 Chat carregado com sucesso');
    
    // Testa a conexão da API na inicialização
    testApiConnection().then(connected => {
        if (!connected) {
            console.warn('⚠️ API não está acessível. Verifique se o servidor FastAPI está rodando em http://localhost:8000');
        }
    });

    // Log de debug para verificar elementos
    console.log('Elementos carregados:', {
        sidebar: !!sidebar,
        toggleBtn: !!toggleSidebarBtn,
        chatForm: !!chatForm,
        fileDropArea: !!fileDropArea,
        themeSwitch: !!themeSwitch
    });
});