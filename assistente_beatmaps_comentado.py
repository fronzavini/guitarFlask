# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# SEÇÃO 1: IMPORTAÇÕES
# Importamos as ferramentas necessárias para o script.
# -----------------------------------------------------------------------------
import os  # Para interagir com pastas e arquivos do sistema.
import json  # Para criar e salvar os arquivos de beatmap em formato JSON.
import random  # Para gerar números aleatórios (usado na criação das notas).
import librosa  # Biblioteca avançada para "ouvir" e analisar arquivos de áudio.
from mutagen.mp3 import MP3  # Biblioteca mais simples para ler metadados de MP3, como a duração.

# -----------------------------------------------------------------------------
# SEÇÃO 2: CONFIGURAÇÕES GLOBAIS
# Definimos constantes que podem ser facilmente ajustadas.
# -----------------------------------------------------------------------------

# Define os caminhos para as pastas de áudio e beatmaps, assumindo que o script está na raiz do projeto.
PASTA_AUDIO = os.path.join('static', 'audio')
PASTA_BEATMAPS = os.path.join('static', 'beatmaps')

# Dicionário que define a dificuldade para o modo "Análise de Batidas".
# A probabilidade determina a chance de uma batida detectada pelo Librosa virar uma nota no jogo.
DIFICULDADES_ANALISE = {
    "1": {"nome": "Fácil", "probabilidade": 0.35},
    "2": {"nome": "Médio", "probabilidade": 0.60},
    "3": {"nome": "Difícil", "probabilidade": 0.90}
}
# Dicionário que define a dificuldade para o modo "Aleatório".
# 'notas_por_segundo' determina a densidade de notas geradas aleatoriamente.
DIFICULDADES_ALEATORIO = {
    "1": {"nome": "Fácil", "notas_por_segundo": 1.5},
    "2": {"nome": "Médio", "notas_por_segundo": 2.5},
    "3": {"nome": "Difícil", "notas_por_segundo": 4.0}
}

# -----------------------------------------------------------------------------
# SEÇÃO 3: FUNÇÕES DE GERAÇÃO DE NOTAS
# Funções especializadas que criam a lista de notas para o beatmap.
# -----------------------------------------------------------------------------

def gerar_notas_aleatorias(duracao_segundos, dificuldade):
    """
    Gera uma lista de notas de forma puramente aleatória, baseada na duração da música
    e na densidade de notas definida pela dificuldade.
    """
    notas_por_segundo = dificuldade["notas_por_segundo"]
    num_notas = int(duracao_segundos * notas_por_segundo)
    notes = []
    for _ in range(num_notas):
        notes.append({
            "time": round(random.uniform(1.5, duracao_segundos - 2.0), 3),
            "lane": random.randint(1, 4)
        })
    notes.sort(key=lambda x: x['time'])  # Ordena as notas por tempo, essencial para o jogo.
    return notes

def gerar_notas_com_librosa(caminho_mp3, dificuldade):
    """
    Usa a biblioteca Librosa para analisar o áudio, detectar os inícios de sons (onsets)
    e criar notas baseadas nesses momentos, seguindo o ritmo real da música.
    """
    print(f"  Analisando '{os.path.basename(caminho_mp3)}' (isso pode demorar)...")
    y, sr = librosa.load(caminho_mp3)  # Carrega o áudio.
    # Detecta os "onsets", que são os pontos de início de notas ou batidas.
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames', backtrack=True)
    # Converte os frames detectados em segundos.
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    
    probabilidade = dificuldade["probabilidade"]
    notes = []
    # Filtra as batidas detectadas: nem todas viram notas, dependendo da dificuldade.
    for time_sec in onset_times:
        if random.random() < probabilidade:
            notes.append({
                "time": round(time_sec, 3),
                "lane": random.randint(1, 4)  # A pista ainda é aleatória.
            })
    print(f"  └─ Librosa detectou {len(onset_times)} batidas. Selecionando {len(notes)}.")
    return notes

# -----------------------------------------------------------------------------
# SEÇÃO 4: FUNÇÃO PRINCIPAL DO SCRIPT
# Orquestra todo o processo, desde a verificação dos arquivos até a chamada das funções de geração.
# -----------------------------------------------------------------------------

def assistente_principal():
    """
    Função principal que escaneia as pastas, pede as configurações uma única vez
    e processa todas as músicas faltantes em lote.
    """
    print("--- Assistente de Beatmaps em Lote para Python Hero ---")

    # Validação inicial para garantir que as pastas existem.
    if not os.path.isdir(PASTA_AUDIO) or not os.path.isdir(PASTA_BEATMAPS):
        print("ERRO: Pastas 'static/audio' e/ou 'static/beatmaps' não encontradas.")
        return

    # Compara os arquivos na pasta de áudio com os da pasta de beatmaps para encontrar o que falta.
    musicas_mp3 = {os.path.splitext(f)[0] for f in os.listdir(PASTA_AUDIO) if f.endswith('.mp3')}
    beatmaps_existentes = {os.path.splitext(f)[0] for f in os.listdir(PASTA_BEATMAPS) if f.endswith('.json')}
    musicas_faltando = list(musicas_mp3 - beatmaps_existentes)

    if not musicas_faltando:
        print("\nTodas as músicas na pasta 'audio' já possuem um beatmap. Tudo certo!")
        return

    print(f"\nEncontrei {len(musicas_faltando)} música(s) sem beatmap:")
    for nome in musicas_faltando: 
        print(f"  - {nome}.mp3")

    # --- PERGUNTA AS CONFIGURAÇÕES APENAS UMA VEZ ---
    print("\nPor favor, defina as configurações para gerar todos os beatmaps faltantes:")
    while True:
        modo = input("  Escolha o modo de geração: [1] Aleatório  [2] Análise de Batidas (Lento): ").strip()
        if modo in ["1", "2"]: break
        print("  ERRO: Opção inválida. Digite 1 ou 2.")

    dificuldades_atuais = DIFICULDADES_ALEATORIO if modo == "1" else DIFICULDADES_ANALISE
    print("  Escolha a dificuldade:")
    for key, value in dificuldades_atuais.items():
        print(f"    [{key}] - {value['nome']}")
    while True:
        escolha_dificuldade = input("  Digite o número da dificuldade: ").strip()
        if escolha_dificuldade in dificuldades_atuais:
            dificuldade_selecionada = dificuldades_atuais[escolha_dificuldade]
            break
        else: print("  ERRO: Opção inválida. Tente novamente.")
    
    print("\n--- INICIANDO PROCESSAMENTO EM LOTE ---")
    
    # --- PROCESSA TODAS AS MÚSICAS FALTANTES COM AS MESMAS CONFIGURAÇÕES ---
    for nome_base_arquivo in musicas_faltando:
        caminho_mp3 = os.path.join(PASTA_AUDIO, f"{nome_base_arquivo}.mp3")
        
        try:
            # Usa Mutagen para ler a duração e formatá-la.
            audio_info = MP3(caminho_mp3)
            duracao_segundos = audio_info.info.length
            minutos, segundos = int(duracao_segundos // 60), int(duracao_segundos % 60)
            duracao_formatada = f"{minutos}:{segundos:02d}"
        except Exception as e:
            print(f"\nERRO ao ler '{nome_base_arquivo}.mp3'. Pulando. ({e})")
            continue  # Pula para a próxima música em caso de erro.

        # Gera as notas usando a função do modo escolhido.
        if modo == "1":
            notes = gerar_notas_aleatorias(duracao_segundos, dificuldade_selecionada)
        else: # modo == "2"
            try:
                notes = gerar_notas_com_librosa(caminho_mp3, dificuldade_selecionada)
            except Exception as e:
                print(f"\n  └─ ERRO FATAL ao analisar '{nome_base_arquivo}.mp3' com Librosa: {e}")
                continue

        # Extrai artista e nome da música a partir do nome do arquivo.
        if " - " in nome_base_arquivo:
            artista, nome_musica = [s.strip() for s in nome_base_arquivo.split(" - ", 1)]
        else:
            artista, nome_musica = "Artista Desconhecido", nome_base_arquivo.replace('_', ' ').title()

        # Monta a estrutura final do dicionário que será salvo como JSON.
        beatmap_completo = {
            "songName": nome_musica, "artist": artista, "duration": duracao_formatada,
            "bpm": 120, "notes": notes
        }
        
        # Salva o arquivo JSON diretamente na pasta correta.
        caminho_json_saida = os.path.join(PASTA_BEATMAPS, f"{nome_base_arquivo}.json")
        with open(caminho_json_saida, 'w', encoding='utf-8') as f:
            json.dump(beatmap_completo, f, indent=4)
            
        print(f"✅ Beatmap para '{nome_base_arquivo}.mp3' criado com sucesso!")

    print("\n--- Processamento em lote finalizado! ---")

# -----------------------------------------------------------------------------
# SEÇÃO 5: INICIALIZAÇÃO DO SCRIPT
# Este bloco só é executado quando o arquivo é chamado diretamente (python assistente_beatmaps.py).
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    assistente_principal()
