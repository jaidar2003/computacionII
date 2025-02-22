from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

DB_PATH = "/home/juanma/PycharmProjects/computacionII/proyecto/servidorArchivos/baseDatos/servidor_archivos.db"

# Función para obtener todos los usuarios
def obtener_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, permisos FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return [{"id": u[0], "username": u[1], "permisos": u[2]} for u in usuarios]

# Endpoint para listar usuarios
@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    return jsonify(obtener_usuarios())

# Endpoint para agregar un nuevo usuario
@app.route('/usuarios', methods=['POST'])
def agregar_usuario():
    datos = request.json
    username = datos.get("username")
    password = datos.get("password")
    permisos = datos.get("permisos", "lectura")

    if not username or not password:
        return jsonify({"error": "Faltan datos"}), 400

    password_hash = sqlite3.connect(DB_PATH).execute("SELECT hex(randomblob(16))").fetchone()[0]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, password, permisos) VALUES (?, ?, ?)",
                       (username, password_hash, permisos))
        conn.commit()
        conn.close()
        return jsonify({"mensaje": f"Usuario '{username}' agregado con éxito"}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "El usuario ya existe"}), 400

# Ejecutar la API
if __name__ == '__main__':
    app.run(debug=True, port=5001)
