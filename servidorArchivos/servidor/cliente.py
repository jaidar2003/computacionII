import socket
import ssl
import argparse
import os


def iniciar_cliente(host, port):
    """
    Inicia el cliente para conectarse al servidor de archivos

    Args:
        host (str): Dirección IP o nombre del servidor
        port (int): Puerto del servidor
    """
    # Crear contexto SSL para la conexión segura
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE  # En producción, debería verificarse el certificado del servidor

    try:
        with socket.create_connection((host, port)) as sock:
            with contexto.wrap_socket(sock, server_hostname=host) as conexion_ssl:
                try:
                    bienvenida = conexion_ssl.recv(1024).decode()
                    print("\n🌍 Servidor de Archivos Seguro")
                    print("────────────────────────────────────")
                    print(bienvenida)
                except ssl.SSLError:
                    print("\n⚠ Error al recibir datos del servidor.")
                    return

                while True:
                    print("\n🔹 Opciones:")
                    print("   [1] Iniciar sesión")
                    print("   [2] Registrarse")
                    print("   [3] Salir")

                    opcion = input("\n👉 Selecciona una opción (1/2/3): ").strip()

                    if opcion == "1":  # Iniciar sesión
                        usuario = input("\n👤 Usuario: ").strip()
                        # Send just the username without a prefix
                        conexion_ssl.sendall(f"{usuario}\n".encode())

                        password = input("🔒 Contraseña: ").strip()
                        conexion_ssl.sendall(f"{password}\n".encode())

                        # Recibir respuesta del servidor
                        respuesta = conexion_ssl.recv(1024).decode().strip()
                        print(f"\n{respuesta}")

                        # Simplificado: si contiene ✅ o "exitosa", continuar
                        if "✅" in respuesta or "exitosa" in respuesta.lower():
                            break  # Ir a la sesión
                        else:
                            continue  # Volver al menú principal

                    elif opcion == "2":  # Registrarse
                        nuevo_usuario = input("\n👤 Nuevo usuario: ").strip()
                        nueva_contraseña = input("🔒 Nueva contraseña: ").strip()

                        # Usar un comando explícito para registro
                        comando_registro = f"REGISTRAR {nuevo_usuario} {nueva_contraseña}\n"
                        conexion_ssl.sendall(comando_registro.encode())

                        # Recibir una sola respuesta del registro
                        respuesta = conexion_ssl.recv(1024).decode().strip()
                        print(f"\n{respuesta}")

                        # No intentar recibir mensajes adicionales

                    elif opcion == "3":  # Salir
                        print("\n👋 Saliendo del cliente...")
                        return

                    else:
                        print("\n⚠ Opción no válida. Intenta de nuevo.")

                print("\n✅ ¡Bienvenido! Ya puedes enviar comandos al servidor.")
                print("──────────────────────────────────────────")

                while True:
                    comando = input("\n💻 Ingresar comando ('SALIR' para desconectar): ").strip()
                    if comando.lower() == "salir":
                        print("\n🔌 Desconectando del servidor...")
                        conexion_ssl.sendall(b"SALIR\n")
                        break

                    conexion_ssl.sendall(f"{comando}\n".encode())
                    respuesta = conexion_ssl.recv(4096).decode().strip()
                    print(f"\n📄 Respuesta del servidor:\n{respuesta}")

    except (socket.error, ssl.SSLError) as e:
        print(f"\n❌ Error de conexión: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cliente para el Servidor de Archivos Seguro')
    parser.add_argument('-s', '--servidor', type=str, default='127.0.0.1',
                        help='Dirección IP o nombre del servidor (por defecto: 127.0.0.1)')
    parser.add_argument('-p', '--puerto', type=int, default=5050,
                        help='Puerto del servidor (por defecto: 5050)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mostrar información detallada')

    args = parser.parse_args()

    if args.verbose:
        print(f"Conectando a {args.servidor}:{args.puerto}...")

    iniciar_cliente(args.servidor, args.puerto)