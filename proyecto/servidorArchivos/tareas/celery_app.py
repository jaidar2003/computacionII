from celery import Celery

# Configuración de Celery
app = Celery('servidor_archivos',
             broker='redis://localhost:6379/0',  # Broker de mensajes (Redis)
             backend='redis://localhost:6379/1',  # Backend para resultados
             include=['tareas.tareas'])  # Módulos con tareas

# Configuración opcional
app.conf.update(
    result_expires=3600,  # Los resultados expiran después de 1 hora
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Argentina/Mendoza',
    enable_utc=True,
)

if __name__ == '__main__':
    app.start()