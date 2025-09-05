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

        cursor.execute("SELECT * FROM usuario WHERE username usuario = %S OR email usuario")