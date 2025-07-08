# 🔐 Configuración de Conexión Segura SSL en Red Local (LAN)

Este README documenta paso a paso cómo configurar una conexión segura (SSL) entre un servidor y un cliente en una red local, usando certificados autofirmados.

---

## ✅ ¿Qué se logró?

Se estableció una conexión cifrada y verificada entre:

- Un **servidor** que corre en una **MacBook** (`192.168.100.131`)
- Un **cliente** que corre en una **máquina Linux** conectada por red local

Ambas máquinas se comunican a través de IPv4 con cifrado SSL sin errores.

---

## 🔧 1. Generación del certificado autofirmado (en MacBook)

### Paso 1. Crear el archivo `openssl-san.conf`

```ini
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = AR
ST = Mendoza
L = Ciudad
O = ComputacionII
OU = Sistema
CN = 192.168.100.131

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
IP.1 = 192.168.100.131
```

### Paso 2. Generar certificado y clave

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout llave.pem \
  -out certificado.pem \
  -config openssl-san.conf \
  -extensions v3_req
```

Esto crea:
- `certificado.pem`: certificado autofirmado
- `llave.pem`: clave privada del servidor

### Paso 3. Mover los archivos al proyecto

```bash
mv certificado.pem llave.pem final/certificados/
```

---

## 🖥️ 2. Configuración del Servidor (MacBook)

En el archivo `.env`:

```env
SERVER_HOST=192.168.100.131
SERVER_PORT=5000
CERT_PATH=/Users/juanmaaidar/PycharmProjects/computacionII/final/certificados/certificado.pem
KEY_PATH=/Users/juanmaaidar/PycharmProjects/computacionII/final/certificados/llave.pem
```

Ejecutar el servidor:

```bash
cd final/servidorArchivos
python main.py -m server
```

---

## 💻 3. Configuración del Cliente (Linux)

### Paso 1. Copiar el certificado desde la Mac

```bash
scp juanma@192.168.100.131:/Users/juanmaaidar/PycharmProjects/computacionII/final/certificados/certificado.pem /home/juanma/PycharmProjects/computacionII/final/certificados/
```

🔒 Solo se copia el certificado público (`certificado.pem`), no la clave privada.

### Paso 2. Verificar el .env en Linux:

```env
SERVER_HOST=192.168.100.131
SERVER_PORT=5000
CERT_PATH=/home/juanma/PycharmProjects/computacionII/final/certificados/certificado.pem
```

### Paso 3. Ejecutar el cliente:

```bash
cd final/servidorArchivos
python3 main.py -m cliente
```

---

## ✅ Resultado esperado

El cliente se conecta correctamente al servidor, mostrando:

```
🔒 Conectado a servidor con certificado:
   - Emitido para: 192.168.100.131
   - Emitido por: 192.168.100.131
   - Válido hasta: ...
```

Y sin errores de SSL ni advertencias de verificación.

---

## 📌 Explicación en palabras simples

Se generó un certificado en la MacBook que dice:
"Yo soy el servidor y tengo la IP 192.168.100.131".

El servidor usa ese certificado y su clave privada para cifrar la conexión.

El cliente en Linux recibe solo el certificado (no la clave) para comprobar que está hablando con el servidor correcto.

El cliente se conecta al servidor por la IP y valida el certificado. Si coincide, establece una conexión segura.

---

## 🧠 Notas adicionales

- No se debe compartir nunca la clave privada (`llave.pem`) fuera del servidor.
- Si cambia la IP del servidor, hay que generar un nuevo certificado.
- Se pueden incluir varias IPs en `openssl-san.conf` si se usa en redes diferentes.
- El certificado dura 1 año (365 días), luego hay que renovarlo.

---
