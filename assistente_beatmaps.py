import os
import json
import random
import librosa
from mutagen.mp3 import MP3

# --- CONFIGURAÇÕES ---
PASTA_AUDIO = os.path.join('static', 'audio')
PASTA_BEATMAPS = os.path.join('static', 'beatmaps')

DIFICULDADES_ANALISE = {
    "1": {"nome": "Fácil", "probabilidade": 0.35},
    "2": {"nome": "Médio", "probabilidade": 0.60},
    "3": {"nome": "Difícil", "probabilidade": 0.90}
}
DIFICULDADES_ALEATORIO = {
    "1": {"nome": "Fácil", "notas_por_segundo": 1.5},
    "2": {"nome": "Médio", "notas_por_segundo": 2.5},
    "3": {"nome": "Difícil", "notas_por_segundo": 4.0}
}

# --- FUNÇÕES DE GERAÇÃO (sem alterações) ---

def gerar_notas_aleatorias(duracao_segundos, dificuldade):
    notas_por_segundo = dificuldade["notas_por_segundo"]
    num_notas = int(duracao_segundos * notas_por_segundo)
    notes = []
    for _ in range(num_notas):
        notes.append({
            "time": round(random.uniform(1.5, duracao_segundos - 2.0), 3),
            "lane": random.randint(1, 4)
        })
    notes.sort(key=lambda x: x['time'])
    return notes

def gerar_notas_com_librosa(caminho_mp3, dificuldade):
    print(f"  Analisando '{os.path.basename(caminho_mp3)}' (isso pode demorar)...")
    y, sr = librosa.load(caminho_mp3)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames', backtrack=True)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    probabilidade = dificuldade["probabilidade"]
    notes = []
    for time_sec in onset_times:
        if random.random() < probabilidade:
            notes.append({
                "time": round(time_sec, 3),
                "lane": random.randint(1, 4)
            })
    print(f"  └─ Librosa detectou {len(onset_times)} batidas. Selecionando {len(notes)}.")
    return notes

# --- FUNÇÃO PRINCIPAL DO SCRIPT ---

def assistente_principal():
    """
    Função principal que escaneia, pede configurações uma vez e processa em lote.
    """
    print("--- Assistente de Beatmaps em Lote para Python Hero ---")

    if not os.path.isdir(PASTA_AUDIO) or not os.path.isdir(PASTA_BEATMAPS):
        print("ERRO: Pastas 'static/audio' e/ou 'static/beatmaps' não encontradas.")
        return

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
            audio_info = MP3(caminho_mp3)
            duracao_segundos = audio_info.info.length
            minutos, segundos = int(duracao_segundos // 60), int(duracao_segundos % 60)
            duracao_formatada = f"{minutos}:{segundos:02d}"
        except Exception as e:
            print(f"\nERRO ao ler '{nome_base_arquivo}.mp3'. Pulando. ({e})")
            continue

        # Gera as notas
        if modo == "1":
            notes = gerar_notas_aleatorias(duracao_segundos, dificuldade_selecionada)
        else: # modo == "2"
            try:
                notes = gerar_notas_com_librosa(caminho_mp3, dificuldade_selecionada)
            except Exception as e:
                print(f"\n  └─ ERRO FATAL ao analisar '{nome_base_arquivo}.mp3' com Librosa: {e}")
                continue

        # Extrai artista e nome
        if " - " in nome_base_arquivo:
            artista, nome_musica = [s.strip() for s in nome_base_arquivo.split(" - ", 1)]
        else:
            artista, nome_musica = "Artista Desconhecido", nome_base_arquivo.replace('_', ' ').title()

        # Monta e salva o JSON
        beatmap_completo = {
            "songName": nome_musica, "artist": artista, "duration": duracao_formatada,
            "bpm": 120, "notes": notes
        }
        
        caminho_json_saida = os.path.join(PASTA_BEATMAPS, f"{nome_base_arquivo}.json")
        with open(caminho_json_saida, 'w', encoding='utf-8') as f:
            json.dump(beatmap_completo, f, indent=4)
            
        print(f"✅ Beatmap para '{nome_base_arquivo}.mp3' criado com sucesso!")

    print("\n--- Processamento em lote finalizado! ---")

if __name__ == "__main__":
    assistente_principal()