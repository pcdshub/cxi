import os, time, subprocess
from telnetlib import Telnet

def cycle():
    p = subprocess.Popen('power ioc-cxi-det2 cycle', shell=True, stdout=subprocess.PIPE)
    for line in p.stdout:
        print(line.decode(), end='')
    p.wait()

def flash(watch=False):
    if watch:
        p = subprocess.Popen('console ioc-cxi-det2', shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)

    with Telnet('digi-cxi-20',2114) as t:
        t.write(b'gevInit\ry\r')
        t.write(b'set -t'+time.strftime('%m%d%y%H%M%S').encode()+b'\r')
        t.write(b'tftpGet -c172.21.68.156 -s172.21.32.40 -frtems-4.9.4-p1.beatnik.netboot.flashimg.bin -g172.21.68.1 -r2 -v\r')
        t.write(b'gevEdit mot-script-boot\rnetShut\rbmw -af4000000 -bf40fffff -c04000000\rgo -a04000000\r\ry\r')
        t.write(b'reset\r')

    if watch:
        starttime = time.time()
        while time.time()-starttime < 120:
            for line in p.stdout:
                print(line.decode(), end='')

        os.killpg(os.getpgid(p.pid), signal.SIGTERM)

def main():
   cycle()
   time.sleep(10)
   flash()

if __name__ == '__main__':
    main()

