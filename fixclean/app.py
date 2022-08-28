import logging
from bluedot.btcomm import BluetoothServer
from signal import pause
import os
import sys
import subprocess
import socket
import time

host = '127.0.0.1'
port = 1233
isFirstGetLocation = True

logging.basicConfig(filename="bluetooth_server.log", level=logging.INFO)
logging.debug("Debug logging app.py...")

ClientSocket = socket.socket()
print('Waiting for connection')
logging.info("Waiting for connection")

def data_received(data):
    print(data)
    data = data.split(' ')

    if data[0] == 'save':
        with open('./coordinate.txt', 'w+') as f:
            f.writelines(data[1] + ' ' + data[2] +
                         ' ' + data[3] + ' ' + data[4])
        s.send("Save success!")

    if data[0] == 'getDroneLocation':
        print("Getting drone location....")
        logging.info("Getting drone location....")

        if isFirstGetLocation:
            isFirstGetLocation = False

            os.system("python3 navigationApp.py &")

            time.sleep(10)

            try:
                ClientSocket.connect((host, port))
                logging.info("[app][fly][angga] Connected to socket")
            except socket.error as e:
                print('ERROR')
                logging.critical("[app][fly][angga] Cannot connect to socket")
                sys.exit(1)

        while True:
            ClientSocket.send(str.encode('get_drone_location'))
            response = ClientSocket.recv(2048)
            response = response.decode('utf-8')
            response = response.split('|')
            if response[0] == 'position':
                logging.info(
                    f"<<<<< Got drone location: {response[1]},{response[2]} >>>>>")
                s.send(f"{response[1]},{response[2]}")
                break

    if data[0] == 'fly':
        if data[1] == 'clement':
            print("clement terbang")
            logging.warning("[app][fly][clement] Clement is flying...")

            os.system(f"python3 clement/main.py {data[2]}")
        elif data[1] == 'angga':
            print("angga terbang")
            
            while True:
                ClientSocket.send(str.encode('fly'))
                response = ClientSocket.recv(2048)
                response = response.decode('utf-8')
                if response[0] == 'fly':
                    break
                
        elif data[1] == 'rozak':
            print("rozak terbang")
            os.system("python3 rozak_s.py & sleep 7 & python3 rozak_c.py &")
            time.sleep(10)
            try:
                ClientSocket.connect((host, port))
            except socket.error as e:
                print('ERROR')
                print(str(e))
        elif data[1] == 'denta':
            print("denta terbang")
            os.system("python3 denta_s.py & sleep 7 & python3 denta_c.py &")
            try:
                ClientSocket.connect((host, port))
                print('connected')
            except socket.error as e:
                print('ERROR')
                print(str(e))
        elif data[1] == 'anfasa':
            print("anfasa terbang")
            logging.warning("[app][fly][anfasa] anfasa is flying...")
            os.system(f"python3 main.py")
            while True:
                FireLoc = ClientSocket.recv(2048)
                FireLoc = FireLoc.decode('utf-8')
                if (FireLoc == 1 or FireLoc == 2 or FireLoc == 3 or FireLoc == 4):
                    logging.info(
                        f"<<<<< Got fire location: {FireLoc} >>>>>")
                    while True:
                        s.send(f"{FireLoc}")
                        break
                    break

    if data[0] == 'landing':
        if data[1] == 'clement':
            print("clement landing")
            logging.warning("[app][fly][clement] Clement is landing...")
            while True:
                ClientSocket.send(str.encode('landing'))
                reply_data = ClientSocket.recv(2048)
                reply_data = reply_data.decode('utf-8')
                if reply_data != 'RTH':
                    continue
                elif reply_data == 'RTH':
                    # kill client, server, and socket
                    os.system('pkill -f clement/server.py')
                    os.system('pkill -f clement/main.py')
                    ClientSocket.close()

                    s.send("Landing success!")
                    logging.critical("[app][fly][clement] Landing success!")
                    break
            sys.exit()
        elif data[1] == 'angga':
            print("angga landing")
            logging.warning("[app][fly][angga] Angga is landing...")
            while True:
                ClientSocket.send(str.encode('landing'))
                reply_data = ClientSocket.recv(2048)
                reply_data = reply_data.decode('utf-8')
                if reply_data != 'RTH':
                    continue
                elif reply_data == 'RTH':
                    time.sleep(10)
                    os.system('pkill -f navigationApp.py')
                    ClientSocket.close()
                    s.send("Landing success!")
                    logging.critical("[app][fly][angga] Landing success!")
                    break
            sys.exit()
        elif data[1] == 'rozak':
            print("rozak terbang")
            while True:
                ClientSocket.send(str.encode('landing'))
                reply_data = ClientSocket.recv(2048)
                reply_data = reply_data.decode('utf-8')
                if reply_data != 'RTH':
                    continue
                elif reply_data == 'RTH':
                    os.system('pkill -f rozak_c.py')
                    ClientSocket.close()
                    sys.exit()
        elif data[1] == 'denta':
            print("denta return to home")
            while True:
                ClientSocket.send(str.encode('landing'))
                reply_data = ClientSocket.recv(2048)
                reply_data = reply_data.decode('utf-8')
                if reply_data != 'RTH':
                    continue
                elif reply_data == 'RTH':
                    os.system('pkill -f denta_c.py')
                    time.sleep(6)
                    ClientSocket.close()
                    sys.exit()
        elif data[1] == 'anfasa':
            print("anfasa terbang")
            logging.warning("[app][fly][anfasa] Anfasa is landing...")
            while True:
                ClientSocket.send(str.encode('landing'))
                reply_data = ClientSocket.recv(2048)
                reply_data = reply_data.decode('utf-8')
                if reply_data != 'RTH':
                    continue
                elif reply_data == 'RTH':
                    os.system('pkill -f server.py')
                    os.system('pkill -f main.py')
                    ClientSocket.close()

                    s.send("Landing success!")
                    logging.critical("[app][fly][Anfasas] Landing success!")
                    break
            sys.exit()


if __name__ == '__main__':
    s = BluetoothServer(data_received)
    pause()