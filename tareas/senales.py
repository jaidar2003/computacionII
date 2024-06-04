import os
import signal

def enviar_senaL(pid, senal):
    try:
        os.kill(pid, senal)
        print(f'Se ha enviado a {senal}')
    except processLookupError:
        print(f'senal {senal.signals(senal).name} enviada al proceso con PID {pid}'
              )