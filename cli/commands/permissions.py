import requests
from cli.utils.config import API_URL
from cli.utils.session import load_session, check_auth

@check_auth
def request_permission(permission_type):
    """Solicitar cambio de permisos"""
    session = load_session()
    
    try:
        response = requests.post(f"{API_URL}/permissions/request", 
                               json={"permissionType": permission_type},
                               cookies=session.get("cookies", {}),
                               headers={"Authorization": f"Bearer {session.get('token', '')}"})
        
        if response.status_code == 200:
            print(f"✅ Solicitud de permisos enviada correctamente")
        else:
            print(f"❌ Error al solicitar permisos: {response.json().get('error', 'Error desconocido')}")
    
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")

@check_auth
def view_requests():
    """Ver solicitudes de permisos"""
    session = load_session()
    
    try:
        response = requests.get(f"{API_URL}/permissions/requests", 
                              cookies=session.get("cookies", {}),
                              headers={"Authorization": f"Bearer {session.get('token', '')}"})
        
        if response.status_code == 200:
            requests_data = response.json().get("requests", [])
            if not requests_data:
                print("No hay solicitudes de permisos")
                return
            
            is_admin = session.get("role") == "admin"
            
            if is_admin:
                print("\n{:<5} {:<15} {:<10} {:<20}".format("ID", "Usuario", "Permiso", "Fecha"))
            else:
                print("\n{:<5} {:<10} {:<10} {:<20}".format("ID", "Permiso", "Estado", "Fecha"))
            
            print("-" * 60)
            
            for req in requests_data:
                if is_admin:
                    print("{:<5} {:<15} {:<10} {:<20}".format(
                        req.get("id", ""), 
                        req.get("username", ""), 
                        req.get("permission", ""), 
                        req.get("date", "")
                    ))
                else:
                    print("{:<5} {:<10} {:<10} {:<20}".format(
                        req.get("id", ""), 
                        req.get("permission", ""), 
                        req.get("status", ""), 
                        req.get("date", "")
                    ))
        else:
            print(f"❌ Error al ver solicitudes: {response.json().get('error', 'Error desconocido')}")
    
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")

@check_auth
def approve_request(request_id, decision):
    """Aprobar o rechazar una solicitud de permisos (solo admin)"""
    session = load_session()
    
    if session.get("role") != "admin":
        print("❌ Solo los administradores pueden aprobar solicitudes")
        return
    
    try:
        response = requests.post(f"{API_URL}/permissions/approve", 
                               json={"requestId": request_id, "decision": decision},
                               cookies=session.get("cookies", {}),
                               headers={"Authorization": f"Bearer {session.get('token', '')}"})
        
        if response.status_code == 200:
            print(f"✅ Solicitud {request_id} {decision}da correctamente")
        else:
            print(f"❌ Error al procesar solicitud: {response.json().get('error', 'Error desconocido')}")
    
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")

@check_auth
def list_users():
    """Listar usuarios del sistema (solo admin)"""
    session = load_session()
    
    if session.get("role") != "admin":
        print("❌ Solo los administradores pueden listar usuarios")
        return
    
    try:
        response = requests.get(f"{API_URL}/users", 
                              cookies=session.get("cookies", {}),
                              headers={"Authorization": f"Bearer {session.get('token', '')}"})
        
        if response.status_code == 200:
            users = response.json().get("users", [])
            if not users:
                print("No hay usuarios registrados")
                return
            
            print("\n{:<5} {:<20} {:<10}".format("ID", "Usuario", "Permiso"))
            print("-" * 40)
            for user in users:
                print("{:<5} {:<20} {:<10}".format(
                    user.get("id", ""), 
                    user.get("username", ""), 
                    user.get("permission", "")
                ))
        else:
            print(f"❌ Error al listar usuarios: {response.json().get('error', 'Error desconocido')}")
    
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")