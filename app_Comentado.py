# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# SEÇÃO 1: IMPORTAÇÕES
# Aqui, importamos todas as ferramentas (bibliotecas) que nosso servidor precisa para funcionar.
# -----------------------------------------------------------------------------
import os  # Usado para interagir com o sistema de arquivos (ex: encontrar pastas e arquivos).
import json  # Usado para ler e interpretar arquivos no formato JSON (nossos beatmaps).
from flask import Flask, render_template, request, jsonify  # O coração do nosso servidor web.
from flask_sqlalchemy import SQLAlchemy  # Uma extensão que facilita a comunicação com o banco de dados.

# -----------------------------------------------------------------------------
# SEÇÃO 2: CONFIGURAÇÃO INICIAL
# Preparamos o servidor Flask и o conectamos ao nosso banco de dados.
# -----------------------------------------------------------------------------

# Cria a aplicação Flask. '__name__' é uma variável especial que ajuda o Flask a se localizar.
app = Flask(__name__)

# Configuração do Banco de Dados SQLite.
basedir = os.path.abspath(os.path.dirname(__file__))  # Pega o caminho absoluto da pasta do projeto.
# Define o local do arquivo do banco de dados. Será um arquivo chamado 'scores.db' na pasta do projeto.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'scores.db')
# Desativa uma funcionalidade de notificação do SQLAlchemy que não usaremos e consome recursos.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cria o objeto de banco de dados, ligando o SQLAlchemy à nossa aplicação Flask.
db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# SEÇÃO 3: MODELO DO BANCO DE DADOS
# Definimos a "planta" ou a estrutura da nossa tabela de pontuações.
# -----------------------------------------------------------------------------

# A classe 'Score' representa a tabela 'score' no nosso banco de dados.
class Score(db.Model):
    # Define as colunas da tabela.
    id = db.Column(db.Integer, primary_key=True)  # Um identificador único para cada pontuação.
    player_name = db.Column(db.String(10), nullable=False)  # O nome do jogador, com no máximo 10 caracteres.
    score_value = db.Column(db.Integer, nullable=False)  # A pontuação, que deve ser um número inteiro.
    music_name = db.Column(db.String(50), nullable=False)  # O ID da música jogada (ex: 'rock1').

# -----------------------------------------------------------------------------
# SEÇÃO 4: ROTAS (ENDPOINTS)
# As rotas são as diferentes URLs que nosso servidor consegue responder.
# É aqui que a mágica acontece.
# -----------------------------------------------------------------------------

# Rota Principal: http://127.0.0.1:5000/
@app.route('/')
def index():
    """
    Esta é a página inicial. Sua única função é carregar e exibir o arquivo 'index.html',
    que contém toda a estrutura do nosso jogo.
    """
    return render_template('index.html')


# Rota da API para listar as músicas: http://127.0.0.1:5000/api/songs
@app.route('/api/songs')
def get_songs():
    """
    Esta rota funciona como uma API: ela não retorna uma página, mas sim dados brutos em JSON.
    O JavaScript do nosso jogo chama esta rota para saber quais músicas estão disponíveis.
    """
    song_list = []
    beatmaps_dir = os.path.join(app.static_folder, 'beatmaps')  # O caminho para a pasta /static/beatmaps
    try:
        # Itera sobre todos os arquivos na pasta de beatmaps.
        for filename in os.listdir(beatmaps_dir):
            if filename.endswith('.json'):  # Se o arquivo for um .json...
                song_id = filename.rsplit('.', 1)[0]  # Pega o nome do arquivo sem a extensão '.json'.
                filepath = os.path.join(beatmaps_dir, filename)
                # Abre o arquivo JSON para ler o nome da música e o artista.
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    song_list.append({
                        'id': song_id,
                        'name': data.get('songName', 'Nome Desconhecido'),
                        'artist': data.get('artist', 'Artista Desconhecido')
                    })
    except Exception as e:
        print(f"Erro ao ler os beatmaps: {e}")
        # Se der algum erro, retorna uma mensagem de erro em JSON.
        return jsonify({"error": "Não foi possível listar as músicas"}), 500
    
    # Se tudo deu certo, retorna a lista de músicas em formato JSON.
    return jsonify(song_list)


# Rota da API para buscar os 10 melhores scores: ex: http://127.0.0.1:5000/api/scores/rock1
@app.route('/api/scores/<music_id>')
def get_high_scores(music_id):
    """
    Outra rota de API que retorna os 10 melhores scores para uma música específica.
    O JavaScript chama esta rota quando o jogador seleciona uma música no menu.
    """
    # Consulta o banco de dados: filtra pela música, ordena pela pontuação (maior primeiro) e pega os 10 primeiros.
    scores = Score.query.filter_by(music_name=music_id).order_by(Score.score_value.desc()).limit(10).all()
    
    # Converte os resultados do banco de dados para um formato JSON simples.
    score_list = [
        {'rank': i + 1, 'player_name': s.player_name, 'score_value': s.score_value}
        for i, s in enumerate(scores)
    ]
    return jsonify(score_list)


# Rota da API para salvar uma nova pontuação: http://127.0.0.1:5000/submit-score
@app.route('/submit-score', methods=['POST'])
def submit_score():
    """
    Esta rota aceita apenas requisições do tipo POST, que é como se envia dados de um formulário.
    O JavaScript chama esta rota no final do jogo para salvar a pontuação do jogador.
    """
    data = request.get_json()  # Pega os dados (nome, score, música) enviados pelo JavaScript.
    
    # Validação básica dos dados recebidos.
    if not data or 'name' not in data or 'score' not in data or 'music' not in data:
        return jsonify({'status': 'error', 'message': 'Dados inválidos'}), 400

    # Cria uma nova entrada de Score com os dados recebidos.
    new_score = Score(player_name=data['name'], score_value=int(data['score']), music_name=data['music'])
    
    # Adiciona a nova pontuação à "sessão" do banco de dados.
    db.session.add(new_score)
    # Confirma e salva as mudanças no arquivo do banco de dados.
    db.session.commit()
    # Retorna uma mensagem de sucesso para o JavaScript.
    return jsonify({'status': 'success', 'message': 'Pontuação salva!', 'music': data['music']})


# Rota para a página de ranking completo: ex: http://127.0.0.1:5000/scores/rock1
@app.route('/scores/<music_name>')
def show_scores(music_name):
    """
    Esta rota carrega uma página HTML completa (`scores.html`) para exibir TODOS os scores
    de uma determinada música. Diferente da API, ela retorna uma página visual.
    """
    scores = Score.query.filter_by(music_name=music_name).order_by(Score.score_value.desc()).all()
    song_info = None
    json_path = os.path.join(app.static_folder, 'beatmaps', f"{music_name}.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f: song_info = json.load(f)
    except FileNotFoundError: pass
        
    return render_template('scores.html', scores=scores, music_name=music_name, song_info=song_info)

# -----------------------------------------------------------------------------
# SEÇÃO 5: INICIALIZAÇÃO DO SERVIDOR
# Este bloco de código só é executado quando rodamos 'python app.py' diretamente.
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    # 'with app.app_context()' garante que a aplicação Flask esteja pronta antes de mexer no banco.
    with app.app_context():
        # Verifica se o arquivo 'scores.db' e a tabela 'score' já existem. Se não, cria eles.
        db.create_all()
    # Inicia o servidor web do Flask. 'debug=True' ativa o modo de depuração,
    # que mostra erros detalhados no navegador e reinicia o servidor automaticamente
    # quando você salva uma alteração no código.
    app.run(debug=True)
