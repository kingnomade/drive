from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import os
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chave_supersecreta_123"  # Troque por algo seguro!

# Usuários válidos
USUARIOS = {
    "luyan": "luian123"
}

ROOT_DIR = os.path.abspath("uploads")

def caminho_seguro(subpath):
    destino = os.path.abspath(os.path.join(ROOT_DIR, subpath))
    if not destino.startswith(ROOT_DIR):
        raise Exception("Acesso negado.")
    return destino

@app.before_request
def verificar_login():
    if request.endpoint not in ('login', 'fazer_login', 'static') and 'usuario' not in session:
        return redirect(url_for('login'))

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def fazer_login():
    usuario = request.form.get("usuario")
    senha = request.form.get("senha")
    if USUARIOS.get(usuario) == senha:
        session["usuario"] = usuario
        return redirect(url_for("index"))
    return render_template("login.html", erro="Usuário ou senha inválidos")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", defaults={"subpath": ""})
@app.route("/<path:subpath>")
def index(subpath):
    pasta_atual = caminho_seguro(subpath)
    arquivos = []
    pastas_disponiveis = []

    for nome in os.listdir(ROOT_DIR):
        caminho = os.path.join(ROOT_DIR, nome)
        if os.path.isdir(caminho):
            pastas_disponiveis.append(nome)

    if os.path.exists(pasta_atual):
        for nome in os.listdir(pasta_atual):
            caminho = os.path.join(pasta_atual, nome)
            arquivos.append({
                "nome": nome,
                "eh_pasta": os.path.isdir(caminho)
            })

    return render_template("index.html", arquivos=arquivos, pasta=subpath, pastas=pastas_disponiveis)

@app.route("/uploads/<path:filepath>")
def baixar_arquivo(filepath):
    return send_from_directory(ROOT_DIR, filepath)

@app.route("/ver/<path:filepath>")
def ver_arquivo(filepath):
    full_path = caminho_seguro(filepath)
    if full_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        return f'<img src="/uploads/{filepath}" style="max-width:100%;">'
    elif os.path.isdir(full_path):
        return f"<pre>📁 {filepath}</pre>"
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f"<pre>{f.read()}</pre>"
    except:
        return redirect(url_for('baixar_arquivo', filepath=filepath))

@app.route("/delete/<path:filepath>", methods=["DELETE"])
def deletar(filepath):
    caminho = caminho_seguro(filepath)
    try:
        if os.path.isdir(caminho):
            shutil.rmtree(caminho)
        else:
            os.remove(caminho)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400

@app.route("/upload", methods=["POST"])
def upload():
    pasta = request.form.get("pasta", "")
    arquivo = request.files["file"]
    if arquivo and arquivo.filename:
        destino = caminho_seguro(pasta)
        os.makedirs(destino, exist_ok=True)
        nome = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(destino, nome))
    return redirect(url_for("index", subpath=pasta))

@app.route("/move", methods=["POST"])
def mover():
    origem = caminho_seguro(request.form["from"])
    destino_rel = request.form["to"]
    destino = caminho_seguro(destino_rel)
    try:
        nome = os.path.basename(origem)
        destino_final = os.path.join(destino, nome)
        shutil.move(origem, destino_final)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400

if __name__ == "__main__":
    os.makedirs(ROOT_DIR, exist_ok=True)
    app.run(debug=True)
