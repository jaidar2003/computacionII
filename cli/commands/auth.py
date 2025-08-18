import os
import json
import requests
from cli.utils.config import API_URL, SESSION_FILE
from cli.utils.session import save_session, load_session, clear_session

def login(username, password):
    """Iniciar sesión en el servidor"""
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            # Guardar la sesión (token, cookies, etc.)
            save_session({
                "user": username,
                "role": data.get("role", "usuario"),
                "token": data.get("token"),
                "cookies": dict(response.cookies)
            })
            print(f"✅ Sesión iniciada como {username} ({data.get('role', 'usuario')})")
        else:
            print(f"❌ Error al iniciar sesión: {response.json().get('error', 'Error desconocido')}")
    
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")

def register(username, password):
    """Registrar un nuevo usuario"""
    try:
        response = requests.post(f"{API_URL}/auth/register", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 201:
            print(f"✅ Usuario {username} registrado correctamente")
        else:
            print(f"❌ Error al registrar usuario: {response.json().get('error', 'Error desconocido')}")
    
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")

def logout():
    """Cerrar sesión"""
    session = load_session()
    if not session:
        print("❌ No hay sesión activa")
        return
    
    try:
        # Opcional: notificar al servidor sobre el cierre de sesión
        requests.post(f"{API_URL}/auth/logout", 
                     cookies=session.get("cookies", {}),
                     headers={"Authorization": f"Bearer {session.get('token', '')}"})
    except:
        pass  # Ignorar errores al cerrar sesión en el servidor
    
    # Limpiar la sesión local
    clear_session()
    print("✅ Sesión cerrada correctamente")