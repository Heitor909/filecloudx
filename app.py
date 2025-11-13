from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import os, sqlite3, time, uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'troque_essa_chave_em_producao')

BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/data/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, created_at INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (id TEXT PRIMARY KEY, filename TEXT, stored_name TEXT, owner INTEGER, size INTEGER, created_at INTEGER)''')
    conn.commit()
    conn.close()

init_db()

def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT id,username FROM users WHERE id=?',(uid,))
    r = c.fetchone(); conn.close()
    return r

@app.route('/')
def index():
    user = current_user()
    # show public files and user's files
    files = []
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT id,filename,owner,created_at FROM files ORDER BY created_at DESC LIMIT 100')
    files = c.fetchall(); conn.close()
    return render_template('index.html', user=user, files=files)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash('Preencha usuário e senha')
            return redirect(url_for('register'))
        pw_hash = generate_password_hash(password)
        conn = get_db(); c = conn.cursor()
        try:
            c.execute('INSERT INTO users(username,password,created_at) VALUES(?,?,?)',(username,pw_hash,int(time.time())))
            conn.commit()
            conn.close()
            flash('Conta criada! Faça login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Usuário já existe')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db(); c = conn.cursor()
        c.execute('SELECT id,password FROM users WHERE username=?',(username,))
        r = c.fetchone(); conn.close()
        if not r or not check_password_hash(r['password'], password):
            flash('Credenciais inválidas')
            return redirect(url_for('login'))
        session['user_id'] = r['id']
        session['username'] = username
        flash('Logado com sucesso')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta')
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        flash('Faça login para enviar arquivos')
        return redirect(url_for('login'))
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado')
        return redirect(url_for('index'))
    f = request.files['file']
    if f.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('index'))
    orig = f.filename
    ext = os.path.splitext(orig)[1]
    fid = uuid.uuid4().hex + ext
    stored = fid
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], stored)
    f.save(save_path)
    size = os.path.getsize(save_path)
    conn = get_db(); c = conn.cursor()
    c.execute('INSERT INTO files(id,filename,stored_name,owner,size,created_at) VALUES(?,?,?,?,?,?)',(fid,orig,stored,session['user_id'],size,int(time.time())))
    conn.commit(); conn.close()
    flash('Upload realizado')
    return redirect(url_for('my_files'))

@app.route('/my_files')
def my_files():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT id,filename,size,created_at FROM files WHERE owner=? ORDER BY created_at DESC',(session['user_id'],))
    files = c.fetchall(); conn.close()
    return render_template('my_files.html', files=files, user=current_user())

@app.route('/d/<fid>')
def download(fid):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT filename,stored_name FROM files WHERE id=?',(fid,))
    r = c.fetchone(); conn.close()
    if not r:
        return "Arquivo não encontrado", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], r['stored_name'], as_attachment=True, download_name=r['filename'])

# small helper for favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.png')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
