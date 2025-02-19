import socket
import ssl

HOST = '127.0.0.1'
PORT = 5000


def iniciar_cliente():
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((HOST, PORT)) as sock:
            with contexto.wrap_socket(sock, server_hostname=HOST) as conexion_ssl:
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

                    if opcion == "1":
                        usuario = input("\n👤 Usuario: ").strip()
                        conexion_ssl.sendall(f"{usuario}\n".encode())  # Asegurar formato correcto

                        password = input("🔒 Contraseña: ").strip()
                        conexion_ssl.sendall(f"{password}\n".encode())  # Asegurar formato correcto

                        respuesta = conexion_ssl.recv(1024).decode().strip()
                        print(f"\n📝 {respuesta}")

                        if "Autenticación exitosa" in respuesta:
                            break  # Sale del bucle y pasa a enviar comandos

                    elif opcion == "2":
                        nuevo_usuario = input("\n👤 Nuevo usuario: ").strip()
                        nueva_contraseña = input("🔒 Nueva contraseña: ").strip()

                        comando_registro = f"REGISTRAR {nuevo_usuario} {nueva_contraseña}\n"
                        conexion_ssl.sendall(comando_registro.encode())

                        respuesta = conexion_ssl.recv(1024).decode().strip()
                        print(f"\n✅ {respuesta}")

                    elif opcion == "3":
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
    iniciar_cliente()
