import os
import sqlite3
import time
import random
import hashlib
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chave_mestra_fiscaliza_df_2026"

# ==========================================
# 1. CONFIGURAÇÕES DE DIRETÓRIO
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Acesso restrito. Por favor, faça login.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# ==========================================
# 2. BANCO DE DADOS (3 TABELAS)
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Tabela 1: Relatos
    conn.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, ra TEXT NOT NULL, 
        description TEXT NOT NULL, status TEXT DEFAULT 'Aberto', date TEXT NOT NULL, 
        lat REAL NOT NULL, lng REAL NOT NULL, image TEXT)''')
    
    # Tabela 2: Histórico de Auditoria
    conn.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL,
        status_anterior TEXT, status_novo TEXT, data_modificacao TEXT)''')
    
    # Tabela 3: Chat/Comentários
    conn.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL,
        user_name TEXT NOT NULL, message TEXT NOT NULL, timestamp TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. LISTAS GLOBAIS
# ==========================================
CATEGORIAS = [
    {'nome': 'Buraco na rua', 'icone': '🕳️'}, {'nome': 'Iluminação pública', 'icone': '💡'},
    {'nome': 'Lixo acumulado', 'icone': '♻️'}, {'nome': 'Problema em praça', 'icone': '🌳'},
    {'nome': 'Transporte público', 'icone': '🚌'}, {'nome': 'Segurança', 'icone': '🚔'},
    {'nome': 'Acidentes', 'icone': '⚠️'}, {'nome': 'Melhorias', 'icone': '🏗️'}
]

REGIOES = ["Brasília", "Ceilândia", "Taguatinga", "Samambaia", "Guará", "Águas Claras", "Sobradinho", "Planaltina", "Gama", "Santa Maria"]

# ==========================================
# 4. ROTAS PÚBLICAS E CIDADÃO
# ==========================================


@app.route('/')
def index():
    cat_filtro = request.args.get('categoria')
    ra_filtro = request.args.get('regiao')
    
    conn = get_db_connection()
    
    # 1. Cálculos para o novo Dashboard Profissional
    total_geral = conn.execute('SELECT COUNT(*) FROM reports').fetchone()[0]
    resolvidos = conn.execute('SELECT COUNT(*) FROM reports WHERE status = "Resolvido"').fetchone()[0]
    taxa_resolucao = round((resolvidos / total_geral * 100), 1) if total_geral > 0 else 0
    
    # Dados para o Gráfico de Radar (Top 5 categorias)
    cats_radar = conn.execute('SELECT category, COUNT(*) as qtd FROM reports GROUP BY category LIMIT 5').fetchall()

    # 2. Busca com Filtros para a Lista
    query = 'SELECT * FROM reports WHERE 1=1'
    params = []
    if cat_filtro:
        query += ' AND category = ?'
        params.append(cat_filtro)
    if ra_filtro:
        query += ' AND ra = ?'
        params.append(ra_filtro)
        
    denuncias = conn.execute(query + ' ORDER BY id DESC', params).fetchall()

    # 3. Estatísticas Adicionais
    total_por_categoria = conn.execute('SELECT category, COUNT(*) as qtd FROM reports GROUP BY category ORDER BY qtd DESC').fetchall()
    total_por_regiao = conn.execute('SELECT ra, COUNT(*) as qtd FROM reports GROUP BY ra ORDER BY qtd DESC').fetchall()
    
    top_categoria = total_por_categoria[0] if total_por_categoria else {'category': 'Nenhum', 'qtd': 0}
    top_regiao = total_por_regiao[0] if total_por_regiao else {'ra': 'Nenhuma', 'qtd': 0}
    
    ultima_at = conn.execute('''
        SELECT MAX(data) FROM (
            SELECT date as data FROM reports 
            UNION SELECT data_modificacao FROM history
            UNION SELECT timestamp FROM comments
        )
    ''').fetchone()[0] or "Aguardando registros"

    conn.close()
    
    # ENVIANDO TUDO CORRETAMENTE PARA O HTML
    return render_template('index.html', 
                           denuncias=denuncias, 
                           total_geral=total_geral, 
                           total_resolvidos=resolvidos,
                           taxa=taxa_resolucao,
                           cats=cats_radar,
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
    rows = conn.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    
    denuncias = []
    for r in rows:
        d = dict(r)
        d['comentarios'] = [dict(c) for c in conn.execute('SELECT * FROM comments WHERE report_id = ? ORDER BY id ASC', (r['id'],)).fetchall()]
        denuncias.append(d)
        
    conn.close()
    return render_template('mapa.html', denuncias=denuncias, categorias=CATEGORIAS)

@app.route('/comentar_publico/<int:id>', methods=['POST'])
def comentar_publico(id):
    msg = request.form.get('message')
    if msg:
        conn = get_db_connection()
        conn.execute('INSERT INTO comments (report_id, user_name, message, timestamp) VALUES (?,?,?,?)',
                     (id, "Cidadão", msg, datetime.now().strftime("%d/%m %H:%M")))
        conn.commit()
        conn.close()
    return redirect(url_for('mapa_completo'))

@app.route('/relatar')
def relatar():
    n1, n2 = random.randint(1, 9), random.randint(1, 9)
    token = hashlib.sha256(f"{n1+n2}fiscaliza".encode()).hexdigest()
    return render_template('relatar.html', categorias=CATEGORIAS, regioes=REGIOES, n1=n1, n2=n2, token=token)

@app.route('/enviar', methods=['POST'])
def enviar():
    # Honeypot: Se preenchido, é bot
    if request.form.get('website'): 
        return redirect(url_for('index'))
    
    # Desafio Anti-Spam
    user_ans = request.form.get('spam_answer')
    token_recebido = request.form.get('spam_token')
    if not user_ans or hashlib.sha256(f"{user_ans}fiscaliza".encode()).hexdigest() != token_recebido:
        flash("Erro: Falha na verificação de segurança.", "error")
        return redirect(url_for('relatar'))

    # Imagem
    file = request.files.get('image')
    filename = ""
    if file and file.filename != '' and allowed_file(file.filename):
        filename = f"{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''INSERT INTO reports (category, ra, description, date, lat, lng, image) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (request.form.get('category'), request.form.get('ra'), request.form.get('description'), 
                 datetime.now().strftime("%d/%m/%Y"), float(request.form.get('lat')), float(request.form.get('lng')), filename))
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    flash("Sua solicitação foi enviada com sucesso!", "success")
    return redirect(url_for('index'))

# ==========================================
# 5. ROTAS DE ADMINISTRAÇÃO E GESTÃO
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('password')
        if email == "admin@df.gov.br" and senha == "admin2026":
            session.permanent = True
            session['admin_logged_in'] = True
            session['admin_email'] = email
            return redirect(url_for('admin'))
        else:
            flash("E-mail ou senha incorretos.", "error")
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    filtro_status = request.args.get('status')
    filtro_cat = request.args.get('categoria')
    aberto_id = request.args.get('detalhes')
    
    conn = get_db_connection()
    query = 'SELECT * FROM reports WHERE 1=1'
    params = []
    
    if filtro_status:
        query += ' AND status = ?'
        params.append(filtro_status)
    if filtro_cat:
        query += ' AND category = ?'
        params.append(filtro_cat)
        
    rows = conn.execute(query + ' ORDER BY id DESC', params).fetchall()
    
    denuncias = []
    for r in rows:
        d = dict(r)
        d['comentarios'] = conn.execute('SELECT * FROM comments WHERE report_id = ? ORDER BY id ASC', (r['id'],)).fetchall()
        denuncias.append(d)
        
    conn.close()
    return render_template('admin.html', denuncias=denuncias, categorias=CATEGORIAS, 
                           status_sel=filtro_status, cat_sel=filtro_cat, aberto_id=aberto_id)

@app.route('/atualizar_status/<int:id>', methods=['POST'])
@login_required
def atualizar_status(id):
    novo_status = request.form.get('status')
    conn = get_db_connection()
    relato = conn.execute('SELECT status FROM reports WHERE id = ?', (id,)).fetchone()
    
    if relato and relato['status'] != novo_status:
        conn.execute('UPDATE reports SET status = ? WHERE id = ?', (novo_status, id))
        conn.execute('''INSERT INTO history (report_id, status_anterior, status_novo, data_modificacao) 
                        VALUES (?, ?, ?, ?)''',
                     (id, relato['status'], novo_status, datetime.now().strftime("%d/%m %H:%M")))
        conn.commit()
    conn.close()
    return redirect(url_for('admin', detalhes=id))

@app.route('/admin/comentar/<int:id>', methods=['POST'])
@login_required
def admin_comentar(id):
    msg = request.form.get('message')
    if msg:
        conn = get_db_connection()
        conn.execute('INSERT INTO comments (report_id, user_name, message, timestamp) VALUES (?,?,?,?)',
                     (id, "Governo (Admin)", msg, datetime.now().strftime("%d/%m %H:%M")))
        conn.commit()
        conn.close()
    return redirect(url_for('admin', detalhes=id))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    conn = get_db_connection()
    # Remove as referências em cascata para evitar lixo no banco
    conn.execute('DELETE FROM history WHERE report_id = ?', (id,))
    conn.execute('DELETE FROM comments WHERE report_id = ?', (id,))
    conn.execute('DELETE FROM reports WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Registro removido do sistema.", "info")
    return redirect(url_for('admin'))

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.errorhandler(404)
def page_not_found(e):
    # Note que passamos o código 404 explicitamente após o render_template
    return render_template('404.html'), 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


import pandas as pd
from flask import send_file
import io

@app.route('/admin/exportar/csv')
@login_required
def exportar_csv():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM reports", conn)
    conn.close()
    
    # Criar um buffer na memória para o arquivo
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return send_file(output, 
                     mimetype='text/csv', 
                     as_attachment=True, 
                     download_name=f'relatorio_fiscaliza_df_{datetime.now().strftime("%Y%m%d")}.csv')

@app.route('/admin/relatorio')
@login_required
def gerar_relatorio():
    conn = get_db_connection()
    # Dados para o resumo executivo
    total = conn.execute('SELECT COUNT(*) FROM reports').fetchone()[0]
    resolvidos = conn.execute('SELECT COUNT(*) FROM reports WHERE status = "Resolvido"').fetchone()[0]
    pendentes = total - resolvidos
    
    # Dados para os gráficos (Categorias e RAs)
    cats = conn.execute('SELECT category, COUNT(*) as qtd FROM reports GROUP BY category').fetchall()
    ras = conn.execute('SELECT ra, COUNT(*) as qtd FROM reports GROUP BY ra').fetchall()
    
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    conn.close()
    return render_template('relatorio.html', total=total, resolvidos=resolvidos, 
                           pendentes=pendentes, cats=cats, ras=ras, data=data_geracao)


if __name__ == '__main__':
    app.run(debug=True)