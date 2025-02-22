from baseDatos.models import get_db_connection

def registrar_log(usuario_id, accion, archivo=None):
    """Registra una acción en los logs."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (usuario_id, accion, archivo)
                VALUES (?, ?, ?)
            """, (usuario_id, accion, archivo))
            conn.commit()
    except Exception as e:
        print(f"❌ Error al registrar log: {e}")

def listar_logs():
    """Lista todos los logs."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM logs")
            logs = cursor.fetchall()
        return logs
    except Exception as e:
        print(f"❌ Error al listar logs: {e}")
        return []
