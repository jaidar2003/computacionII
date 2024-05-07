import os
import mmap

def main():
    
    pid = os.fork()
    mem_size = 64
    mem =mmap.mmap(-1, mem_size, mmap.MAP_ANONYMOUS | mmap.PROT_SHARED)
    mem.write(b'Hola soy el abuelo')

    if pid == 0:
        child(mem)
    else:
        os.waitpid(pid, 0)
    mem.close()

def child(mem):
    child_pid = os.getppid()
    pid = os.fork()
    if pid == 0:
        grandchild(mem)

def grandchild(mem):
    mem.seek(0)
    print('Hola soy el nieto', mem.read(64))

if __name__ == '__main__':
    main()