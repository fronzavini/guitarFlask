import os
import json
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'scores.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(10), nullable=False)
    score_value = db.Column(db.Integer, nullable=False)
    music_name = db.Column(db.String(50), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/songs')
def get_songs():
    song_list = []
    beatmaps_dir = os.path.join(app.static_folder, 'beatmaps')
    try:
        for filename in os.listdir(beatmaps_dir):
            if filename.endswith('.json'):
                song_id = filename.rsplit('.', 1)[0]
                filepath = os.path.join(beatmaps_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    song_list.append({
                        'id': song_id,
                        'name': data.get('songName', 'Nome Desconhecido'),
                        'artist': data.get('artist', 'Artista Desconhecido')
                    })
    except Exception as e:
        print(f"Erro ao ler os beatmaps: {e}")
        return jsonify({"error": "Não foi possível listar as músicas"}), 500
    return jsonify(song_list)

@app.route('/api/scores/<music_id>')
def get_high_scores(music_id):
    scores = Score.query.filter_by(music_name=music_id).order_by(Score.score_value.desc()).limit(10).all()
    score_list = [
        {'rank': i + 1, 'player_name': s.player_name, 'score_value': s.score_value}
        for i, s in enumerate(scores)
    ]
    return jsonify(score_list)

@app.route('/submit-score', methods=['POST'])
def submit_score():
    data = request.get_json()
    if not data or 'name' not in data or 'score' not in data or 'music' not in data:
        return jsonify({'status': 'error', 'message': 'Dados inválidos'}), 400
    new_score = Score(player_name=data['name'], score_value=int(data['score']), music_name=data['music'])
    db.session.add(new_score)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Pontuação salva!', 'music': data['music']})

@app.route('/scores/<music_name>')
def show_scores(music_name):
    scores = Score.query.filter_by(music_name=music_name).order_by(Score.score_value.desc()).all()
    song_info = None
    json_path = os.path.join(app.static_folder, 'beatmaps', f"{music_name}.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f: song_info = json.load(f)
    except FileNotFoundError: pass
    return render_template('scores.html', scores=scores, music_name=music_name, song_info=song_info)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)