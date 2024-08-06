import os
import time
r, w = os.pipe()
pid = os.fork()

if pid > 0:
    print(os.getpid())
    print("Padre escribe")
    time.sleep(5)
    os.write(w, "Hola hijo".encode())
    os.wait()
    print("Padre lee: " + os.read(r, 100).decode())
    os.close(r)
    os.close(w)
    exit()

else:
    print(os.getpid())
    print("Hijo lee: " + os.read(r, 100).decode())
    print("Hijo escribe")
    os.write(w, "Chau papa".encode())
    os.close(r)
    os.close(w)
    exit()
