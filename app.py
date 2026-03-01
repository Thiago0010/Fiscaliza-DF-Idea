import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chave_secreta_fiscaliza_df_2026"

# ==========================================
# CONFIGURAÇÕES DE UPLOAD E PASTA ESTÁTICA
# ==========================================
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Garante que a pasta de fotos exista no seu computador
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# CONEXÃO E BANCO DE DADOS
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Criando a tabela com a coluna 'image' para suportar as fotos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            ra TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pendente',
            date TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Rodar a inicialização ao iniciar o app
init_db()

# ==========================================
# DADOS GLOBAIS (Categorias e RAs)
# ==========================================
CATEGORIAS = [
    {'nome': 'Buraco na rua', 'icone': '🕳️'},
    {'nome': 'Iluminação pública', 'icone': '💡'},
    {'nome': 'Lixo acumulado', 'icone': '♻️'},
    {'nome': 'Problema em praça', 'icone': '🌳'},
    {'nome': 'Transporte público', 'icone': '🚌'},
    {'nome': 'Segurança', 'icone': '🚔'},
    {'nome': 'Acidentes', 'icone': '⚠️'},
    {'nome': 'Melhorias', 'icone': '🏗️'}
]

REGIOES = [
    "Brasília", "Ceilândia", "Taguatinga", "Samambaia", "Guará", 
    "Águas Claras", "Sobradinho", "Planaltina", "Recanto das Emas", 
    "Santa Maria", "Gama", "São Sebastião", "Riacho Fundo"
]

# ==========================================
# ROTAS DO SISTEMA
# ==========================================

@app.route('/')
def index():
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    total = len(denuncias)
    resolvidos = len([d for d in denuncias if d['status'] == 'Resolvido'])
    conn.close()
    return render_template('index.html', denuncias=denuncias, total=total, resolvidos=resolvidos)

@app.route('/relatar')
def relatar():
    return render_template('relatar.html', categorias=CATEGORIAS, regioes=REGIOES)

@app.route('/enviar', methods=['POST'])
def enviar():
    if request.method == 'POST':
        categoria = request.form.get('category')
        ra = request.form.get('ra')
        description = request.form.get('description')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        data_atual = datetime.now().strftime("%d/%m/%Y")

        # Lógica de Upload da Imagem
        file = request.files.get('image')
        filename = None

        if file and file.filename != '' and allowed_file(file.filename):
            # Gera nome único usando timestamp para evitar duplicatas
            original_name = secure_filename(file.filename)
            filename = f"{int(time.time())}_{original_name}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Inserção no Banco de Dados (incluindo o campo image)
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO reports (category, ra, description, date, lat, lng, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (categoria, ra, description, data_atual, lat, lng, filename))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))

@app.route('/mapa')
def mapa_completo():
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('mapa.html', denuncias=denuncias)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

# ==========================================
# PAINEL ADMINISTRATIVO
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "admin123":
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            flash("Senha incorreta!", "error")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', denuncias=denuncias)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# Rota extra para deletar relatos no admin
@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM reports WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)