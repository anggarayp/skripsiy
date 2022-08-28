
# from droneState import DroneState
import sys
import time
import socket
import RPi.GPIO as GPIO
from _thread import *
from time import sleep
from drone import Drone
 
DRONE_IP = "192.168.42.1"
drone = Drone(DRONE_IP)
 
HOST = '127.0.0.1'
PORT = 1233
CLIENT_SOCKET = socket.socket()
 
pointDestination = [0.0, 0.0]
pointHome = [0.0, 0.0]
 
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
 
def controlMagnet(action):
    GPIO.output(18, action)
 
def setPoint():
   global pointDestination, pointHome
   with open('./coordinate.txt') as f:
       lines = f.read().split(' ')
       print(lines[0])
        
       pointHome[0] = lines[0]
       pointHome[1] = lines[1]
       pointDestination[0] = lines[2]
       pointDestination[1] = lines[3]
     
   print('pointHome: ', pointHome)
   print('pointDestination: ', pointDestination)
 
def client_handler(connection, drone):
    data = connection.recv(2048)
    message = data.decode('utf-8')
     
    if message == 'get_drone_location':
        reply = drone.get_current_position(drone)
        connection.sendall(reply.encode('utf-8'))
         
    if message == 'fly':
        reply = "fly"
        connection.sendall(reply.encode('utf-8'))
        main()
    if message == 'landing':
        reply = "RTH"
        connection.sendall(reply.encode('utf-8'))
        drone.rth()
        drone.land()
 
def accept_connections(ServerSocket):
    Client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    Client.send(str.encode('Connected'))
    start_new_thread(client_handler, (Client, drone, ))
 
def start_server(HOST, PORT):
    ServerSocket = socket.socket()
    try:
        ServerSocket.bind((HOST, PORT))
    except socket.error as e:
        print(str(e))
    print(f'Server is listing on the port {PORT}...')
    ServerSocket.listen()
 
    while True:
        accept_connections(ServerSocket)
 
def main():
    print(f"coordinate set: {pointHome}, {pointDestination}")
    print(pointHome[0], pointHome[1])
    drone.connectToDrone()
    print("Drone connected")
    setPoint()
    while True:
        try:
            if drone.state == DroneState.LAND:
                drone.waitGPSFix()
                drone.takeoff()
 
                sleep(3)
                controlMagnet(0)
                sleep(5)
                controlMagnet(1)
                 
                drone.moveByVertical(0.0, -1.0, 1.0)
 
            else:
                if not drone.atDest:
                    drone.moveToDest_speed(pointDestination[0], pointDestination[1], 1.0)
                    drone.atDest = True
                 
                else:
                    drone.moveByVertical(0.0, 1.0, 0.4)
                    sleep(3)
                    controlMagnet(0)
                    sleep(5)
                    drone.medsArrived = True
 
                if drone.atDest ==  True and drone.medsArrived == True:
                    drone.moveByVertical(0.0, -1.0, 1.0)
                    drone.rth()
                    drone.land()
                    print("Going Back Home Landing...")
                    drone.disconnectFromDrone()
                    sys.exit()
            sleep(3)
        except KeyboardInterrupt:
            print("interrupt")
            drone.land()
            drone.disconnectFromDrone()
            sys.exit()
        finally:
            break
 
if __name__ == "__main__":
    main()
    start_server(HOST, PORT)
