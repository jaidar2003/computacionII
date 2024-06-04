import os
import time

pipe = 'home/user/documents/mi_fifo'

def lector():
    pipe_lectura = open(file=pipe, mode='r')

    while True:
        contador_leido = pipe_lectura.readline()[:-1]
        print("lector obtiene: " + contador_leido)

def escritor():
    pipe_lectura = os.open(path=pipe, flags=os.O_WRONLY)
    contador = 0

    while True:
        os.write(pipe_escritura, b"Numero %d"%contador)
        contador = contador + 1
        time.sleep(1)

pid = os.fork()
if pid > 0:
    lector()
else:
    escritor()