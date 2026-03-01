import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "fiscaliza_df_secret_key"

# --- CONFIGURAÇÕES ---
DATABASE = 'database.db'

CATEGORIAS = [
    {"id": "buraco", "nome": "Buraco na Via", "icone": "🕳️"},
    {"id": "iluminacao", "nome": "Iluminação Pública", "icone": "💡"},
    {"id": "lixo", "nome": "Lixo Acumulado", "icone": "🗑️"},
    {"id": "praca", "nome": "Problema em Praça", "icone": "🌳"},
    {"id": "transporte", "nome": "Transporte Público", "icone": "🚌"},
    {"id": "seguranca", "nome": "Segurança", "icone": "🚔"},
    {"id": "acidentes", "nome": "Acidentes", "icone": "⚠️"},
    {"id": "melhorias", "nome": "Sugestão de Melhoria", "icone": "✨"}
]

REGIOES_ADMINISTRATIVAS = ["Brasília", "Ceilândia", "Taguatinga", "Samambaia", "Guará", "Águas Claras", "Gama", "Sobradinho", "Planaltina"]

# --- FUNÇÕES DE BANCO ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            ra TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Aberto',
            date TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Inicializa o banco ao rodar o script
init_db()

# --- ROTAS ---

@app.route('/')
def index():
    conn = get_db_connection()
    # Pega todos os registros
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    
    # Estatísticas
    total = conn.execute('SELECT COUNT(*) FROM reports').fetchone()[0]
    resolvidos = conn.execute('SELECT COUNT(*) FROM reports WHERE status = "Resolvido"').fetchone()[0]
    
    conn.close()
    return render_template('index.html', denuncias=denuncias, total=total, resolvidos=resolvidos)

@app.route('/relatar')
def relatar():
    return render_template('relatar.html', categorias=CATEGORIAS, regioes=REGIOES_ADMINISTRATIVAS)

@app.route('/enviar', methods=['POST'])
def enviar():
    categoria = request.form.get('category')
    ra = request.form.get('ra')
    description = request.form.get('description')
    lat = request.form.get('lat')
    lng = request.form.get('lng')

    if not categoria or not ra or not description:
        flash("Erro: Preencha todos os campos!", "erro")
        return redirect(url_for('relatar'))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO reports (category, ra, description, date, lat, lng)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (categoria, ra, description, datetime.now().strftime("%d/%m/%Y"), lat, lng))
    
    conn.commit()
    conn.close()
    
    flash("Relato registrado com sucesso!", "sucesso")
    return redirect(url_for('index'))


from flask import session # Adicione 'session' nos imports lá no topo

# --- NOVA ROTA: LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "admin123": # Mude sua senha aqui
            session['admin'] = True
            return redirect(url_for('admin'))
        flash("Senha incorreta!", "erro")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# --- NOVA ROTA: PAINEL ADMIN ---
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', denuncias=denuncias)

# --- AÇÃO: MUDAR STATUS ---
@app.route('/resolver/<int:id>')
def resolver(id):
    if not session.get('admin'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('UPDATE reports SET status = "Resolvido" WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Status atualizado para Resolvido!", "sucesso")
    return redirect(url_for('admin'))

# --- AÇÃO: EXCLUIR ---
@app.route('/excluir/<int:id>')
def excluir(id):
    if not session.get('admin'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM reports WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Relato removido com sucesso.", "sucesso")
    return redirect(url_for('admin'))

@app.route('/mapa')
def mapa_completo():
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('mapa.html', denuncias=denuncias)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

if __name__ == '__main__':
    app.run(debug=True)