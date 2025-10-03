// O 'DOMContentLoaded' é um evento que garante que todo o nosso código JavaScript
// só será executado depois que a página HTML inteira for carregada. Isso evita
// erros de tentar manipular elementos que ainda não existem.
document.addEventListener('DOMContentLoaded', () => {

    // --- SEÇÃO 1: VARIÁVEIS DE ELEMENTOS DO DOM ---
    // Aqui, criamos "atalhos" para todos os elementos HTML com os quais vamos interagir.
    // Fazer isso no início deixa o código mais organizado e rápido.
    const gameTrack = document.getElementById('game-track'), 
          scoreDisplay = document.getElementById('score-display'),
          comboDisplay = document.getElementById('combo-display'), 
          streakMeter = document.getElementById('streak-meter'),
          startScreen = document.getElementById('start-screen'), 
          loadingText = document.getElementById('loading-text'),
          menuLayout = document.getElementById('menu-layout'), 
          songSelectionContainer = document.getElementById('song-selection'),
          songListContainer = document.getElementById('song-list-container'), 
          highScorePanel = document.getElementById('high-score-panel'),
          highScoreSongTitle = document.getElementById('high-score-song-title'), 
          highScoreList = document.getElementById('high-score-list'),
          actionButtons = document.getElementById('action-buttons'), 
          startButton = document.getElementById('start-button'),
          backButton = document.getElementById('back-button'), 
          endGameModal = document.getElementById('end-game-modal'),
          finalScoreDisplay = document.getElementById('final-score'), 
          scoreForm = document.getElementById('score-form'),
          playerNameInput = document.getElementById('player-name'), 
          fretMap = { 
              'a': document.getElementById('fret-1'), 
              's': document.getElementById('fret-2'), 
              'd': document.getElementById('fret-3'), 
              'f': document.getElementById('fret-4') 
          };

    // --- SEÇÃO 2: VARIÁVEIS DE ESTADO DO JOGO ---
    // Estas variáveis guardam as informações que mudam durante o jogo.
    const audioPlayer = new Audio(); // O objeto que vai tocar a música.
    const audioContext = new (window.AudioContext || window.webkitAudioContext)(); // O "motor" de áudio do navegador, essencial para compatibilidade.
    let songData;       // Guarda os dados do .json da música (nome, artista, notas).
    let notesToSpawn;   // Uma cópia da lista de notas que ainda precisam aparecer.
    let gameStartTime;  // O momento exato em que a música começou a tocar.
    let score = 0, combo = 0; // Pontuação e combo do jogador.
    let selectedSongId = null; // O ID da música escolhida no menu (ex: 'rock1').

    // --- SEÇÃO 3: CONSTANTES DE JOGABILIDADE ---
    // Parâmetros que podemos ajustar para mudar a dificuldade e a sensação do jogo.
    const NOTE_FALL_DURATION = 4.0;   // Tempo (em segundos) que uma nota leva para cair.
    const PERFECT_WINDOW = 0.08;      // Janela de tempo para um acerto "Perfeito" (80ms).
    const GOOD_WINDOW = 0.15;         // Janela de tempo para um acerto "Bom" (150ms).

    // --- SEÇÃO 4: LÓGICA DO MENU ---

    /**
     * Função principal que inicia o menu. Ela pede ao servidor a lista de músicas
     * e constrói a interface de seleção.
     */
    async function initializeMenu() {
        startScreen.style.display = 'flex';
        resetToMainMenu(); // Reseta a tela para o estado inicial.
        try {
            // Pede a lista de músicas para a nossa API em Python.
            const response = await fetch('/api/songs');
            if (!response.ok) throw new Error('Falha ao buscar lista de músicas');
            const songs = await response.json();
            
            loadingText.style.display = 'none'; // Esconde o texto "Carregando...".
            songListContainer.innerHTML = '';   // Limpa a lista para o caso de estarmos voltando de uma partida.

            // Para cada música recebida da API, cria um botão no menu.
            songs.forEach(song => {
                const songButton = document.createElement('button');
                songButton.className = 'song-item';
                songButton.textContent = `${song.name} - ${song.artist}`;
                songButton.dataset.songId = song.id;

                // Adiciona um evento de clique para cada botão de música.
                songButton.addEventListener('click', () => {
                    document.querySelectorAll('.song-item.selected').forEach(btn => btn.classList.remove('selected'));
                    songButton.classList.add('selected');
                    selectedSongId = song.id;
                    actionButtons.style.display = 'flex'; // Mostra os botões "Iniciar" e "Voltar".
                    displayHighScores(song.id, song.name); // Busca e exibe os high scores para esta música.
                });
                songListContainer.appendChild(songButton);
            });
            menuLayout.style.display = 'flex'; // Mostra o layout do menu.
        } catch (error) {
            console.error("Erro ao inicializar menu:", error);
            loadingText.textContent = "Erro ao carregar menu.";
        }
    }

    /**
     * Reseta a interface do menu para o estado inicial.
     */
    function resetToMainMenu() {
        selectedSongId = null;
        document.querySelectorAll('.song-item.selected').forEach(btn => btn.classList.remove('selected'));
        actionButtons.style.display = 'none';
        highScorePanel.style.display = 'none';
        menuLayout.style.display = 'none';
        loadingText.style.display = 'block';
        loadingText.textContent = "Carregando músicas...";
        playerNameInput.value = '';
    }

    /**
     * Busca e exibe os 10 melhores scores para a música selecionada.
     * @param {string} songId - O ID da música (ex: 'rock1').
     * @param {string} songName - O nome completo da música para exibir no título.
     */
    async function displayHighScores(songId, songName) {
        highScoreSongTitle.textContent = songName;
        highScoreList.innerHTML = '<li>Carregando...</li>';
        highScorePanel.style.display = 'block';
        try {
            // Pede os scores para a nossa API em Python.
            const response = await fetch(`/api/scores/${songId}`);
            const scores = await response.json();
            highScoreList.innerHTML = '';
            if (scores.length === 0) {
                highScoreList.innerHTML = '<li>Nenhum recorde ainda. Seja o primeiro!</li>';
            } else {
                // Cria um item de lista (<li>) para cada score.
                scores.forEach(score => {
                    const li = document.createElement('li');
                    li.innerHTML = `<span>#${score.rank}</span> <span class="player-name">${score.player_name}</span> <span class="player-score">${score.score_value}</span>`;
                    highScoreList.appendChild(li);
                });
            }
        } catch (error) {
            console.error("Erro ao buscar high scores:", error);
            highScoreList.innerHTML = '<li>Não foi possível carregar os scores.</li>';
        }
    }

    // --- SEÇÃO 5: LÓGICA PRINCIPAL DO JOGO ---

    /**
     * Carrega os arquivos (.json e .mp3) da música selecionada e, se conseguir, chama startGame.
     */
    async function loadAndStartSong() {
        if (!selectedSongId) return;
        menuLayout.style.display = 'none';
        actionButtons.style.display = 'none';
        loadingText.textContent = `Carregando ${selectedSongId}...`;
        loadingText.style.display = 'block';
        try {
            // Carrega o beatmap e o áudio em paralelo para ser mais rápido.
            const [beatmapResponse, audioBlob] = await Promise.all([
                fetch(`/static/beatmaps/${selectedSongId}.json`),
                fetch(`/static/audio/${selectedSongId}.mp3`).then(res => res.blob())
            ]);
            if (!beatmapResponse.ok) throw new Error('Falha ao carregar o mapa de batidas');
            songData = await beatmapResponse.json();
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayer.src = audioUrl;
            console.log("Música carregada:", songData.songName);
            await startGame(); // Se tudo deu certo, inicia o jogo.
        } catch (error) {
            console.error("Erro ao carregar a música:", error);
            alert(`Não foi possível carregar a música ${selectedSongId}.`);
            initializeMenu(); // Em caso de erro, volta ao menu.
        }
    }

    /**
     * Prepara o estado do jogo para uma nova partida e dá o play na música.
     */
    async function startGame() {
        if (audioContext.state === 'suspended') await audioContext.resume();
        score = 0; combo = 0;
        updateScore('reset'); // Reseta a pontuação e o combo na tela.
        notesToSpawn = [...songData.notes].sort((a, b) => a.time - b.time); // Prepara a lista de notas.
        document.querySelectorAll('.note').forEach(n => n.remove()); // Limpa notas de uma partida anterior.
        startScreen.style.display = 'none'; // Esconde o menu.
        await audioPlayer.play();
        gameStartTime = Date.now();
        requestAnimationFrame(gameLoop); // Inicia o "coração" do jogo.
    }
    
    /**
     * O "coração" do jogo. Esta função é executada a cada frame de animação do navegador.
     * É responsável por tudo que acontece em tempo real.
     */
    function gameLoop() {
        // Primeiro, verifica se a música terminou. Esta é a condição de parada mais importante.
        if (audioPlayer.ended) {
            endGame(score);
            return; // Para o loop permanentemente.
        }
        // Se a música não terminou, mas está pausada, para o loop temporariamente.
        if (audioPlayer.paused) {
            return;
        }
        
        // Se a música está tocando, executa a lógica do jogo.
        const elapsedTime = (Date.now() - gameStartTime) / 1.0; // Tempo em segundos desde o início da música.
        // Cria notas que estão prestes a entrar na tela.
        while (notesToSpawn.length > 0 && notesToSpawn[0].time <= elapsedTime + NOTE_FALL_DURATION) {
            const noteData = notesToSpawn.shift();
            spawnNote(noteData);
        }
        // Move todas as notas que já estão na tela.
        document.querySelectorAll('.note').forEach(noteEl => {
            const timeToHit = parseFloat(noteEl.dataset.time);
            const spawnTime = timeToHit - NOTE_FALL_DURATION;
            const progress = (elapsedTime - spawnTime) / NOTE_FALL_DURATION;
            noteEl.style.top = `${progress * 100}%`;
            // Se a nota passou do ponto de acerto, remove e quebra o combo.
            if (progress > 1.1) {
                noteEl.remove();
                updateCombo(false); // 'false' indica que foi um erro, não um acerto.
            }
        });
        
        // Pede ao navegador para chamar a função gameLoop novamente no próximo frame.
        requestAnimationFrame(gameLoop);
    }

    /**
     * Cria o elemento <div> de uma nota e o adiciona na pista.
     * @param {object} noteData - Contém o tempo e a pista da nota.
     */
    function spawnNote(noteData) {
        const noteEl = document.createElement('div');
        noteEl.classList.add('note', `color-${noteData.lane}`);
        noteEl.dataset.time = noteData.time; // Guarda o tempo de acerto no próprio elemento.
        gameTrack.appendChild(noteEl);
    }
    
    /**
     * Chamada quando uma tecla é pressionada para verificar se acertou uma nota.
     * @param {number} lane - A pista (1 a 4) que foi pressionada.
     */
    function checkHit(lane) {
        const elapsedTime = (Date.now() - gameStartTime) / 1000;
        const targetNotes = document.querySelectorAll(`.note.color-${lane}`);
        let hitNote = null;
        // Procura por uma nota na pista correta que esteja dentro da janela de acerto.
        for (const note of targetNotes) {
            const diff = Math.abs(elapsedTime - parseFloat(note.dataset.time));
            if (diff <= GOOD_WINDOW) { hitNote = note; break; }
        }
        // Se uma nota foi encontrada...
        if (hitNote) {
            const diff = Math.abs(elapsedTime - parseFloat(hitNote.dataset.time));
            if (diff <= PERFECT_WINDOW) {
                updateScore('perfect');
                showHitFeedback('PERFEITO!');
            } else {
                updateScore('good');
                showHitFeedback('BOM!');
            }
            hitNote.remove(); // Remove a nota acertada.
        }
    }

    /**
     * Atualiza a pontuação do jogador.
     * @param {string} rank - O tipo de acerto ('perfect', 'good', ou 'reset').
     */
    function updateScore(rank) {
        if (rank === 'reset') {
            score = 0;
            updateCombo('reset');
        } else {
            updateCombo(true); // 'true' indica que foi um acerto.
            let points = (rank === 'perfect') ? 100 : 50;
            score += points * Math.max(1, combo); // A pontuação é multiplicada pelo combo.
        }
        scoreDisplay.textContent = score;
    }

    /**
     * Atualiza o combo do jogador e o texto de feedback na tela.
     * @param {boolean|string} hit - 'true' se acertou, 'false' se errou, 'reset' para zerar.
     */
    function updateCombo(hit) {
        if (hit === 'reset' || !hit) { combo = 0; } 
        else { combo++; }
        
        if (combo < 10) { streakMeter.textContent = "OK"; streakMeter.style.color = "#e5e5e5"; }
        else if (combo < 20) { streakMeter.textContent = "LEGAL!"; streakMeter.style.color = "#3b82f6"; }
        else { streakMeter.textContent = "EM CHAMAS!"; streakMeter.style.color = "#ef4444"; }
        comboDisplay.textContent = `X${combo}`;
    }

    /**
     * Mostra o texto de feedback "PERFEITO!" ou "BOM!" na tela.
     * @param {string} text - O texto a ser exibido.
     */
    function showHitFeedback(text) {
        const feedbackEl = document.createElement('div');
        feedbackEl.className = 'hit-feedback';
        feedbackEl.textContent = text;
        gameTrack.appendChild(feedbackEl);
        // Remove o texto da tela após a animação para não poluir o HTML.
        setTimeout(() => feedbackEl.remove(), 600);
    }
    
    /**
     * Chamada no final da música para mostrar o modal de pontuação.
     * @param {number} finalScore - A pontuação final.
     */
    function endGame(finalScore) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        finalScoreDisplay.textContent = finalScore;
        endGameModal.style.display = 'flex';
        playerNameInput.focus();
    }

    // --- SEÇÃO 6: EVENT LISTENERS ---
    // Configura todas as interações do usuário: cliques de mouse e pressionamento de teclas.

    // Clique no botão "Iniciar Jogo".
    startButton.addEventListener('click', loadAndStartSong);

    // Clique no botão "Trocar de Música".
    backButton.addEventListener('click', () => {
        selectedSongId = null;
        document.querySelectorAll('.song-item.selected').forEach(btn => btn.classList.remove('selected'));
        actionButtons.style.display = 'none';
        highScorePanel.style.display = 'none';
        highScoreSongTitle.textContent = 'Selecione uma música';
        highScoreList.innerHTML = '';
    });

    // Envio do formulário de pontuação no final do jogo.
    scoreForm.addEventListener('submit', (event) => {
        event.preventDefault();
        let playerName = playerNameInput.value.trim();
        if (playerName === '') { playerName = 'Jogador'; } // Nome padrão se estiver vazio.
        
        const finalScore = finalScoreDisplay.textContent;
        const musicId = selectedSongId; 
        const submitButton = scoreForm.querySelector('button');
        submitButton.textContent = "Salvando...";
        submitButton.disabled = true;

        // Envia os dados para a API em Python.
        fetch('/submit-score', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: playerName, score: finalScore, music: musicId }) })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                endGameModal.style.display = 'none';
                submitButton.textContent = "Salvar Pontuação";
                submitButton.disabled = false;
                initializeMenu(); // Volta para o menu principal.
            } else {
                alert('Erro ao salvar pontuação.');
                submitButton.textContent = "Salvar Pontuação";
                submitButton.disabled = false;
            }
        }).catch(error => {
            console.error("Erro na requisição:", error);
            alert("Não foi possível conectar ao servidor.");
            submitButton.textContent = "Salvar Pontuação";
            submitButton.disabled = false;
        });
    });

    // Pressionamento de uma tecla do "instrumento".
    window.addEventListener('keydown', (event) => {
        const key = event.key.toLowerCase();
        const fret = fretMap[key];
        if (fret && !event.repeat) { // '!event.repeat' impede que segurar a tecla conte como múltiplos acertos.
            fret.classList.add('active');
            const laneNumber = parseInt(fret.id.split('-')[1]);
            checkHit(laneNumber);
        }
    });

    // Soltar uma tecla do "instrumento".
    window.addEventListener('keyup', (event) => {
        const key = event.key.toLowerCase();
        const fret = fretMap[key];
        if (fret) { fret.classList.remove('active'); }
    });

    // --- SEÇÃO 7: INICIALIZAÇÃO ---
    // A primeira função a ser chamada quando o script começa, dando início a tudo.
    initializeMenu();
});