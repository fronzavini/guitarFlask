from flask import Flask,render_template,request,redirect,url_for,session,flash
from werzeug.security import generate_password_hash,check_password_hash
import mysql.connector

app = Flask (__name__)

app.secrect_key = "01"

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'pg2'
}


app.secret_key = 'asidhasoidha98sdashd98asd'


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome=request.form['nome']
        username=request.form['username']
        email = request.form['email']

        senha = generate_password_hash(request.form['senha'])

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuario WHERE username_usuario = %s OR email_usuario = %s", (username, email))
        if cursor.fetchone():
            flash("Nome de usuário ou email já cadastrado.", "erro")
            return redirect(url_for('cadastro'))
        
        cursor.execute("""INSERT INTO usuario (nome_usuario, username_usuario, password_usuario, email_usuario ) = VALUES ("%s,%s,%s,%s,%s)""", (nome,username,senha,email,True))

        conn.commit()
        cursor.close() 
        conn.close()

        flash("Cadastro realizado com sucesso! você já pode fazer login.", "sucesso")
        return redirect(url_for('login'))
    
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuario WHERE username_usuario = %s", (username,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario and check_password_hash(usuario['password_usuario'], senha):
            if not usuario['conta_ativa']:  # Verifica se o usuário está ativo
                flash("Conta desativada. Entre em contato com o suporte.", "erro")
                return redirect(url_for('login'))
            session['usuario_id'] = usuario['cod_usuario']
            session['username'] = usuario['nome_usuario']
            flash("Login realizado com sucesso!", "sucesso")
            return redirect(url_for('dashboard'))
        else:
            flash("Nome de usuário ou senha incorretos.", "erro")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        flash("Por favor, faça login para acessar o dashboard.", "erro")
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session['username'])