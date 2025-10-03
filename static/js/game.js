document.addEventListener('DOMContentLoaded', () => {
    // --- VARIÁVEIS DE ELEMENTOS DO DOM ---
    const gameTrack = document.getElementById('game-track'), scoreDisplay = document.getElementById('score-display'),
    comboDisplay = document.getElementById('combo-display'), streakMeter = document.getElementById('streak-meter'),
    startScreen = document.getElementById('start-screen'), loadingText = document.getElementById('loading-text'),
    menuLayout = document.getElementById('menu-layout'), songSelectionContainer = document.getElementById('song-selection'),
    songListContainer = document.getElementById('song-list-container'), highScorePanel = document.getElementById('high-score-panel'),
    highScoreSongTitle = document.getElementById('high-score-song-title'), highScoreList = document.getElementById('high-score-list'),
    actionButtons = document.getElementById('action-buttons'), startButton = document.getElementById('start-button'),
    backButton = document.getElementById('back-button'), endGameModal = document.getElementById('end-game-modal'),
    finalScoreDisplay = document.getElementById('final-score'), scoreForm = document.getElementById('score-form'),
    playerNameInput = document.getElementById('player-name'), 
    pauseScreen = document.getElementById('pause-screen'),
    quitButton = document.getElementById('quit-button'),
    fretMap = { 'a': document.getElementById('fret-1'), 's': document.getElementById('fret-2'), 'd': document.getElementById('fret-3'), 'f': document.getElementById('fret-4') };

    // --- VARIÁVEIS DE ESTADO DO JOGO ---
    const audioPlayer = new Audio(), audioContext = new (window.AudioContext || window.webkitAudioContext)();
    let songData, notesToSpawn, gameStartTime, score = 0, combo = 0, selectedSongId = null;
    let isPaused = false;

    // --- CONSTANTES ---
    const NOTE_FALL_DURATION = 4.0, PERFECT_WINDOW = 0.08, GOOD_WINDOW = 0.15;
    const NOTE_HIT_POSITION_Y = 95;

    // --- LÓGICA DO MENU ---
    async function initializeMenu() {
        startScreen.style.display = 'flex';
        resetToMainMenu();
        try {
            const response = await fetch('/api/songs');
            if (!response.ok) throw new Error('Falha ao buscar lista de músicas');
            const songs = await response.json();
            loadingText.style.display = 'none';
            songListContainer.innerHTML = '';
            songs.forEach(song => {
                const songButton = document.createElement('button');
                songButton.className = 'song-item';
                songButton.textContent = `${song.name} - ${song.artist}`;
                songButton.dataset.songId = song.id;
                songButton.addEventListener('click', () => {
                    document.querySelectorAll('.song-item.selected').forEach(btn => btn.classList.remove('selected'));
                    songButton.classList.add('selected');
                    selectedSongId = song.id;
                    actionButtons.style.display = 'flex';
                    displayHighScores(song.id, song.name);
                });
                songListContainer.appendChild(songButton);
            });
            menuLayout.style.display = 'flex';
        } catch (error) {
            console.error("Erro ao inicializar menu:", error);
            loadingText.textContent = "Erro ao carregar menu.";
        }
    }

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

    async function displayHighScores(songId, songName) {
        highScoreSongTitle.textContent = songName;
        highScoreList.innerHTML = '<li>Carregando...</li>';
        highScorePanel.style.display = 'block';
        try {
            const response = await fetch(`/api/scores/${songId}`);
            const scores = await response.json();
            highScoreList.innerHTML = '';
            if (scores.length === 0) {
                highScoreList.innerHTML = '<li>Nenhum recorde ainda. Seja o primeiro!</li>';
            } else {
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

    // --- LÓGICA DO JOGO ---
    async function loadAndStartSong() {
        if (!selectedSongId) return;
        menuLayout.style.display = 'none';
        actionButtons.style.display = 'none';
        loadingText.textContent = `Carregando ${selectedSongId}...`;
        loadingText.style.display = 'block';
        try {
            const [beatmapResponse, audioBlob] = await Promise.all([
                fetch(`/static/beatmaps/${selectedSongId}.json`),
                fetch(`/static/audio/${selectedSongId}.mp3`).then(res => res.blob())
            ]);
            if (!beatmapResponse.ok) throw new Error('Falha ao carregar o mapa de batidas');
            songData = await beatmapResponse.json();
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayer.src = audioUrl;
            console.log("Música carregada:", songData.songName);
            await startGame();
        } catch (error) {
            console.error("Erro ao carregar a música:", error);
            alert(`Não foi possível carregar a música ${selectedSongId}.`);
            initializeMenu();
        }
    }

    async function startGame() {
        if (audioContext.state === 'suspended') await audioContext.resume();
        score = 0; combo = 0; isPaused = false;
        updateScore('reset');
        notesToSpawn = [...songData.notes].sort((a, b) => a.time - b.time);
        document.querySelectorAll('.note').forEach(n => n.remove());
        startScreen.style.display = 'none';
        await audioPlayer.play();
        gameStartTime = Date.now();
        requestAnimationFrame(gameLoop);
    }
    
    function togglePause() {
        if (!gameStartTime || audioPlayer.ended) return;
        isPaused = !isPaused;
        if (isPaused) {
            audioPlayer.pause();
            pauseScreen.style.display = 'flex';
        } else {
            audioPlayer.play();
            pauseScreen.style.display = 'none';
            requestAnimationFrame(gameLoop);
        }
    }

    function gameLoop() {
        if (isPaused) return;
        if (audioPlayer.ended) {
            endGame(score);
            return;
        }
        
        const elapsedTime = (Date.now() - gameStartTime) / 1000;
        while (notesToSpawn.length > 0 && notesToSpawn[0].time <= elapsedTime + NOTE_FALL_DURATION) {
            const noteData = notesToSpawn.shift();
            spawnNote(noteData);
        }
        document.querySelectorAll('.note').forEach(noteEl => {
            const timeToHit = parseFloat(noteEl.dataset.time);
            const spawnTime = timeToHit - NOTE_FALL_DURATION;
            const progress = (elapsedTime - spawnTime) / NOTE_FALL_DURATION;
            const currentY = progress * NOTE_HIT_POSITION_Y;
            noteEl.style.top = `${currentY}%`;
            if (progress > 1.1) {
                noteEl.remove();
                updateCombo(false);
            }
        });
        requestAnimationFrame(gameLoop);
    }

    function spawnNote(noteData) {
        const noteEl = document.createElement('div');
        noteEl.classList.add('note', `color-${noteData.lane}`);
        noteEl.dataset.time = noteData.time;
        gameTrack.appendChild(noteEl);
    }
    
    function checkHit(lane) {
        const elapsedTime = (Date.now() - gameStartTime) / 1000;
        const targetNotes = document.querySelectorAll(`.note.color-${lane}`);
        let hitNote = null;
        for (const note of targetNotes) {
            const diff = Math.abs(elapsedTime - parseFloat(note.dataset.time));
            if (diff <= GOOD_WINDOW) { hitNote = note; break; }
        }
        if (hitNote) {
            const diff = Math.abs(elapsedTime - parseFloat(hitNote.dataset.time));
            if (diff <= PERFECT_WINDOW) {
                updateScore('perfect');
                showHitFeedback('PERFEITO!', lane);
            } else {
                updateScore('good');
                showHitFeedback('BOM!', lane);
            }
            hitNote.remove();
            return true;
        }
        return false;
    }

    function updateScore(rank) {
        if (rank === 'reset') {
            score = 0;
            updateCombo('reset');
        } else {
            updateCombo(true);
            let points = (rank === 'perfect') ? 100 : 50;
            score += points * Math.max(1, combo);
        }
        scoreDisplay.textContent = score;
    }

    function updateCombo(hit) {
        if (hit === 'reset' || !hit) { combo = 0; } 
        else { combo++; }
        if (combo < 10) { streakMeter.textContent = "OK"; streakMeter.style.color = "#e5e5e5"; }
        else if (combo < 20) { streakMeter.textContent = "LEGAL!"; streakMeter.style.color = "#3b82f6"; }
        else { streakMeter.textContent = "EM CHAMAS!"; streakMeter.style.color = "#ef4444"; }
        comboDisplay.textContent = `X${combo}`;
    }

    function showHitFeedback(text, lane) {
        const feedbackEl = document.createElement('div');
        feedbackEl.className = 'hit-feedback';
        feedbackEl.textContent = text;
        gameTrack.appendChild(feedbackEl);
        setTimeout(() => feedbackEl.remove(), 600);
    }
    
    function endGame(finalScore) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        gameStartTime = null;
        finalScoreDisplay.textContent = finalScore;
        endGameModal.style.display = 'flex';
        playerNameInput.focus();
    }

    // --- EVENT LISTENERS ---
    startButton.addEventListener('click', loadAndStartSong);
    backButton.addEventListener('click', () => {
        selectedSongId = null;
        document.querySelectorAll('.song-item.selected').forEach(btn => btn.classList.remove('selected'));
        actionButtons.style.display = 'none';
        highScorePanel.style.display = 'none';
        highScoreSongTitle.textContent = 'Selecione uma música';
        highScoreList.innerHTML = '';
    });
    scoreForm.addEventListener('submit', (event) => {
        event.preventDefault();
        let playerName = playerNameInput.value.trim();
        if (playerName === '') { playerName = 'Jogador'; }
        const finalScore = finalScoreDisplay.textContent;
        const musicId = selectedSongId; 
        const submitButton = scoreForm.querySelector('button');
        submitButton.textContent = "Salvando...";
        submitButton.disabled = true;
        fetch('/submit-score', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: playerName, score: finalScore, music: musicId }) })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                endGameModal.style.display = 'none';
                submitButton.textContent = "Salvar Pontuação";
                submitButton.disabled = false;
                initializeMenu();
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
    quitButton.addEventListener('click', () => {
        if (!gameStartTime || audioPlayer.ended) return; // Não faz nada se o jogo não começou
        if (confirm("Tem certeza que deseja sair? Sua pontuação não será salva.")) {
            audioPlayer.pause();
            audioPlayer.currentTime = 0;
            isPaused = false;
            gameStartTime = null;
            document.querySelectorAll('.note').forEach(n => n.remove());
            initializeMenu();
        }
    });
    window.addEventListener('keydown', (event) => {
        if (event.code === 'Space') {
            event.preventDefault();
            togglePause();
            return;
        }
        const key = event.key.toLowerCase();
        const fret = fretMap[key];
        if (fret && !event.repeat && gameStartTime && !isPaused) {
            fret.classList.add('active');
            const laneNumber = parseInt(fret.id.split('-')[1]);
            const wasHit = checkHit(laneNumber);
            if (!wasHit) {
                updateCombo(false);
            }
        }
    });
    window.addEventListener('keyup', (event) => {
        const key = event.key.toLowerCase();
        const fret = fretMap[key];
        if (fret) { fret.classList.remove('active'); }
    });

    // --- INICIALIZAÇÃO ---
    initializeMenu();
});