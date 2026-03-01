import os
import sqlite3
import time
import random
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chave_mestra_fiscaliza_df_2026"

# ==========================================
# 1. CONFIGURAÇÕES (DIRETÓRIOS E FOTOS)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# ==========================================
# 2. BANCO DE DADOS (TABELAS)
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Tabela Principal
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            ra TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Aberto',
            date TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            image TEXT
        )
    ''')
    # Tabela de Histórico
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            status_anterior TEXT,
            status_novo TEXT,
            data_modificacao TEXT,
            FOREIGN KEY (report_id) REFERENCES reports (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. VARIÁVEIS GLOBAIS
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

REGIOES = ["Brasília", "Ceilândia", "Taguatinga", "Samambaia", "Guará", "Águas Claras", "Sobradinho", "Planaltina", "Gama", "Santa Maria"]

# ==========================================
# 4. ROTAS DO USUÁRIO
@app.route('/')
def index():
    conn = get_db_connection()
    
    # 1. Dados para os Filtros e Lista
    cat_filtro = request.args.get('categoria')
    ra_filtro = request.args.get('regiao')
    query = 'SELECT * FROM reports WHERE 1=1'
    params = []
    if cat_filtro:
        query += ' AND category = ?'; params.append(cat_filtro)
    if ra_filtro:
        query += ' AND ra = ?'; params.append(ra_filtro)
    denuncias = conn.execute(query + ' ORDER BY id DESC', params).fetchall()

    # 2. Total Geral
    total_geral = conn.execute('SELECT COUNT(*) FROM reports').fetchone()[0]

    # 3. Totais por Categoria (Lista para o Dashboard)
    total_por_categoria = conn.execute('''
        SELECT category, COUNT(*) as qtd FROM reports GROUP BY category ORDER BY qtd DESC
    ''').fetchall()

    # 4. Totais por Região (Lista para o Dashboard)
    total_por_regiao = conn.execute('''
        SELECT ra, COUNT(*) as qtd FROM reports GROUP BY ra ORDER BY qtd DESC
    ''').fetchall()

    # 5. Categoria mais reportada e Região com mais registros
    top_categoria = total_por_categoria[0] if total_por_categoria else {'category': 'N/A', 'qtd': 0}
    top_regiao = total_por_regiao[0] if total_por_regiao else {'ra': 'N/A', 'qtd': 0}

    # 6. Última atualização (Data do último registro ou mudança de status)
    ultima_at = conn.execute('''
        SELECT MAX(data_modificacao) FROM (
            SELECT date as data_modificacao FROM reports 
            UNION 
            SELECT data_modificacao FROM history
        )
    ''').fetchone()[0] or "Sem registros"

    conn.close()
    
    return render_template('index.html', 
                           denuncias=denuncias,
                           total_geral=total_geral,
                           total_por_categoria=total_por_categoria,
                           total_por_regiao=total_por_regiao,
                           top_categoria=top_categoria,
                           top_regiao=top_regiao,
                           ultima_at=ultima_at,
                           categorias=CATEGORIAS,
                           regioes=REGIOES,
                           cat_sel=cat_filtro,
                           ra_sel=ra_filtro)
@app.route('/mapa')
def mapa_completo():
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    historicos = conn.execute('SELECT * FROM history ORDER BY id ASC').fetchall()
    conn.close()
    return render_template('mapa.html', denuncias=denuncias, historicos=historicos)

@app.route('/relatar')
def relatar():
    n1, n2 = random.randint(1, 9), random.randint(1, 9)
    resultado = n1 + n2
    # Gera um token para validar a resposta sem usar session
    token = hashlib.sha256(f"{resultado}fiscaliza".encode()).hexdigest()
    return render_template('relatar.html', categorias=CATEGORIAS, regioes=REGIOES, n1=n1, n2=n2, token=token)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/enviar', methods=['POST'])
def enviar():
    # Validação Anti-Spam (Token + Honeypot)
    if request.form.get('website'): return redirect(url_for('index'))
    
    user_answer = request.form.get('spam_answer')
    token_recebido = request.form.get('spam_token')
    hash_verificacao = hashlib.sha256(f"{user_answer}fiscaliza".encode()).hexdigest()

    if hash_verificacao != token_recebido:
        flash("Erro: O resultado da soma está incorreto.", "error")
        return redirect(url_for('relatar'))

    # Coleta de Dados
    categoria = request.form.get('category')
    ra = request.form.get('ra')
    description = request.form.get('description')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    data_atual = datetime.now().strftime("%d/%m/%Y")

    # Upload de Imagem
    file = request.files.get('image')
    filename = ""
    if file and file.filename != '' and allowed_file(file.filename):
        filename = f"{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Salva no Banco
    conn = get_db_connection()
    conn.execute('INSERT INTO reports (category, ra, description, date, lat, lng, image) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (categoria, ra, description, data_atual, lat, lng, filename))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ==========================================
# 5. PAINEL ADMIN
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "admin123":
            session['admin'] = True
            return redirect(url_for('admin'))
        flash("Senha incorreta!", "error")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', denuncias=denuncias)

@app.route('/atualizar_status/<int:id>', methods=['POST'])
def atualizar_status(id):
    if not session.get('admin'): return redirect(url_for('login'))
    novo_status = request.form.get('status')
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    conn = get_db_connection()
    relato = conn.execute('SELECT status FROM reports WHERE id = ?', (id,)).fetchone()
    if relato and relato['status'] != novo_status:
        conn.execute('UPDATE reports SET status = ? WHERE id = ?', (novo_status, id))
        conn.execute('INSERT INTO history (report_id, status_anterior, status_novo, data_modificacao) VALUES (?, ?, ?, ?)',
                     (id, relato['status'], novo_status, data_hora))
        conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM reports WHERE id = ?', (id,))
    conn.execute('DELETE FROM history WHERE report_id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)