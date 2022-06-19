from droneState import DroneState
import sys
import time
#Import all neccessary features to code.
import RPi.GPIO as GPIO
from time import sleep
from compass import Compass
from drone import Drone
from olympe.messages.ardrone3.Piloting import moveTo
from olympe.messages.ardrone3.PilotingState import moveToChanged, FlyingStateChanged
from olympe.enums.ardrone3.Piloting import MoveTo_Orientation_mode
from olympe.messages.ardrone3.GPSSettingsState import HomeChanged

# IP drone untuk koneksi
DRONE_IP = "192.168.42.1"
drone = Drone(DRONE_IP)
compass = Compass()

modeHome = False
switch = False

# hardcoded coordinate
# pointDestination = [-6.557045041042469,106.73229372868889]
# pointHome = [-6.556972833333994,106.73229416666666]

# this coordinate will be filled by coordinate.txt
pointDestination = []
pointHome = []
initDistance = -999.0
totalDistance = 0

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

home_latitude = 0.0
home_longitude = 0.0
home_altitude = 0.0

def controlSolenoid(action):
    GPIO.output(18, action)

def checkDroneBearing(locBearing):
    # fungsi mengecek bearing drone, bila sudah sesuai dengan titik tujuan maka akan keluar dari loop 
    while True:
        droneBearing = abs(compass.getDroneBearing())
        if abs(droneBearing-locBearing) >= 5:
            setDroneHeading(droneBearing, locBearing)
        else:
            break

def setDroneHeading(droneBearing, locBearing):
    # fungsi untuk memutar drone sehingga bearing sesuai dengan titik tujuan
    deltaBearing = locBearing - droneBearing
    drone.rotate(deltaBearing)

def switchDestination():
    #fungsi untuk mengubah tujuan menjadi titik home
    global pointDestination
    pointDestination[0] = pointHome[0]
    pointDestination[1] = pointHome[1]

def setPoint():
    global pointDestination, pointHome
    with open('/home/pi/ta/drone_map/coordinate.txt') as f:
        lines = f.read().split(' ')

        pointHome[0] = lines[0] # latitude1
        pointHome[1] = lines[1] # longitude1
        pointDestination[0] = lines[2] # latitude2
        pointDestination[1] = lines[3] # longitude2
    
    print('pointHome: ', pointHome)
    print('pointDestination: ', pointDestination)

#Buat RTH (Return to Home)
def move_to_gps(drone, latitude, longitude, altitude, heading, timeout=60):
    assert drone(moveTo(latitude=latitude,
                              longitude=longitude,
                              altitude=altitude,
                              orientation_mode=MoveTo_Orientation_mode.HEADING_DURING,
                              heading=heading)
                       >> moveToChanged(status='DONE', _timeout=timeout)
                       >> FlyingStateChanged(state="hovering", _timeout=10)).wait().success()

def main():
    setPoint()
    print(f"coordinate set: {pointHome}, {pointDestination}")
    drone.connectToDrone()
    print("Drone connected")
    while True:
        global initDistance
        global totalDistance
        global modeHome
        global switch
        if modeHome == True and switch == False:
            # mengecek apakah drone ada di mode kembali ke titik home dan apakah titik tujuan sudah ditukar,
            # bila belum maka value pointDestination akan diubah menjadi value pointHome
            switchDestination()
            switch = True
        try:
            if drone.state == DroneState.LAND:
                # mengecek bila drone sedang mendarat maka akan diperintahkan untuk takeoff
                drone.waitGPSFix()
                drone.takeoff()

                # set current position as home
                home_position = drone.get_state(HomeChanged)
                home_latitude = home_position['latitude']
                home_longitude = home_position['longitude']
                home_altitude = home_position['altitude']

                sleep(3)
                controlSolenoid(0)      #solenoid buka
                sleep(5)
                controlSolenoid(1)      #solenoid tutup
                # menambah ketinggian drone sebesar 5 meter, untuk lebih detail cek drone.py
                # drone.moveTo(0.0, -5.0)
                drone.moveTo(0.0, -3.0)
            else:
                distance, locBearing = drone.calculateDistance(pointDestination[0], pointDestination[1])
                while distance < 0.0: #ga nemu (posisi gps ga dapet)
                    # dilakukan pengecekan untuk GPS drone, bila gps tidak menangkap lokasi maka akan terjebak di
                    # loop ini sampai mendapatkan lokasi
                    distance, locBearing = drone.calculateDistance(pointDestination[0], pointDestination[1])
                    print(f"##### masih cari lokasi. current distance: {distance}. current bearing: {locBearing} #####")
                    time.sleep(2)

                if initDistance < 0:
                    # pada awal eksekusi initDistance akan diset -999 yang menandakan drone baru diperintahkan untuk
                    # terbang dan belum memiliki total jarak tempuh ke titik tujuan
                    initDistance = distance
                    # jarak total yang harus ditempuh drone untuk sampai ke titik tujuan, didapatkan sekali saat 
                    # drone pertama kali menghitung jarak titik drone dengan titik tujuan
                    totalDistance = distance
                if totalDistance > 10.0:
                    # untuk keamanan (supaya drone tidak menabrak pohon dsb, maka jarak tempuh drone dibatasi 
                    # maksimal 10 meter)
                    totalDistance = 10.0
                    distance = 10.0
                if distance > totalDistance and totalDistance >= 0:
                    # untuk menghindari drone tidak pernah turun karena hasil perhitungan gps tidak pernah sampai 0,
                    # maka totalDistance dijadikan acuan
                    distance = totalDistance
                if distance <= 0.5 or totalDistance <= 0.0:
                    # drone sampai di titik tujuan
                    drone.atDest = True
                if drone.atDest == True:
                    drone.moveTo(0.0, 3.0)  #turun 3 meter
                    sleep(3)
                    controlSolenoid(0)      #solenoid buka
                    sleep(5)
                    controlSolenoid(1)      #solenoid tutup
                    # drone.land()
                    # print("Landing...")
                    # drone berganti menjadi mode home dan diperintahkan untuk terbang ke titik asal
                    # if modeHome == True:
                    #     # ini landing beneran landing di titik awal
                    #     break
                    # else: 
                    #     # ini buat balik ke titik awal
                    #     initDistance = -999.0
                    #     totalDistance = 0.0
                    #     drone.atDest = False
                    #     modeHome = True
                    #     break
                    
                else:
                    checkDroneBearing(abs(locBearing))
                    drone.moveTo(distance, 0.0)
                    totalDistance = totalDistance - distance
        except KeyboardInterrupt:
            print("interrupt")
            sys.exit

if __name__ == "__main__":
    main()