from flask import Flask, render_template, request, send_from_directory
import os

app = Flask(__name__)

# Caminho completo para evitar problemas no Railway
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# Garante que a pasta exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if "file" not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files["file"]
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)
    
    return "OK"

@app.route('/d/<path:filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    # Config necessário para Railway
    app.run(host="0.0.0.0", port=5000)
