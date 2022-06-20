from math import cos, sin, sqrt, pow, radians, tan, atan, atan2, degrees
from turtle import distance
import olympe
from droneState import DroneState
from olympe.messages.ardrone3.PilotingSettings import MaxTilt
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing, moveTo
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.ardrone3.GPSSettingsState import HomeChanged
from olympe.messages.ardrone3.PilotingState import PositionChanged
from olympe.messages.ardrone3.GPSSettingsState import GPSFixStateChanged

class Drone():
    state = DroneState.LAND
    r2 = 6371008.77141
    atDest = False
    # log untuk mencatat koordinat titik takeoff dan landing drone
    FILE = "/home/pi/code/drone/research/log/coordinate/coordinate.txt"
    
    def __init__(self, ip):
        self.DRONE_IP = ip
        self.drone = olympe.Drone(self.DRONE_IP)

    def write(self, text):
        # fungsi untuk mencatat log
        with open(self.FILE, 'a') as f:
            f.write(text)

    def connectToDrone(self):
        self.drone.connect()

    def setMaxTilt(self, tilt):
        self.drone(MaxTilt(1)).wait().success()

    def waitGPSFix(self):
        # fungsi untuk menunggu gps di drone siap untuk digunakan
        self.drone(GPSFixStateChanged(_policy = 'wait'))
    
    def getPosition(self):
        # fungsi untuk mendapatkan koordinat lokasi drone
        if self.state == DroneState.LAND:
            return self.drone.get_state(HomeChanged)
        elif self.state == DroneState.TAKEOFF:
            return self.drone.get_state(PositionChanged)

    def takeoff(self):
        if self.state == DroneState.LAND:
            assert self.drone(
                TakeOff()
                >> FlyingStateChanged(state="hovering", _timeout=10)
            ).wait().success()
            self.state = DroneState.TAKEOFF
            self.write("Takeoff...\n")

    def moveTo(self, dist, altitude):
        # fungsi untuk menggerakan drone, fungsi ini di sdk parrot bernama "moveBy" dan
        # memiliki 4 parameter, yaitu moveBy(maju_mundur, kanan_kiri, atas_bawah, memutar drone sebesar x derajat)
        if self.state == DroneState.TAKEOFF:
            assert self.drone(
                moveBy(dist, 0, altitude, 0)
                >> FlyingStateChanged(state="hovering", _timeout=10)
            ).wait().success()
    
    def rotate(self, deg):
        # fungsi memutar drone, sebenarnya fungsi yang digunakan sama persis dengan fungsi moveTo, namun 
        # saya bedakan supaya lebih mudah dipahami
        if self.state == DroneState.TAKEOFF:
            assert self.drone(
                moveBy(0, 0, 0, radians(deg))
                >> FlyingStateChanged(state="hovering", _timeout=10)
            ).wait().success()
    
    def land(self):
        if self.state == DroneState.TAKEOFF:
            assert self.drone(
                Landing()
                >> FlyingStateChanged(state="landed", _timeout=10)
            ).wait().success()
            self.state = DroneState.LAND
            self.write("Landing...\n")

    def disconnectFromDrone(self):
        self.drone.disconnect()

    #Buat RTH (Return to Home)
    def move_to_gps(drone, latitude, longitude, altitude, heading, timeout=60):
        assert drone(moveTo(latitude=latitude,
                                longitude=longitude,
                                altitude=altitude,
                                orientation_mode=MoveTo_Orientation_mode.HEADING_DURING,
                                heading=heading)
                        >> moveToChanged(status='DONE', _timeout=timeout)
                        >> FlyingStateChanged(state="hovering", _timeout=10)).wait().success()

    def vincenty_formula(self, latitude1, longitude1, latitude2, longitude2):
        #fungsi menghitung jarak drone dengan titik tujuan
        numerator = ( (cos(latitude2) * sin(longitude2-longitude1)) * (cos(latitude2) * sin(longitude2-longitude1)) ) + ( (cos(latitude1) * sin(latitude2) - sin(latitude1) * cos(latitude2) * cos(longitude2-longitude1)) * (cos(latitude1) * sin(latitude2) - sin(latitude1) * cos(latitude2) * cos(longitude2-longitude1)))
        denominator = sin(latitude1) * sin(latitude2) + cos(latitude1) * cos(latitude2) * cos(longitude2-longitude1)
        distance = self.r2 * atan(sqrt(numerator)/denominator)
        return distance

    def vincenty_inverse(self,coord1,coord2,maxIter=200,tol=10**-12):

        #--- CONSTANTS ------------------------------------+
        
        a=6378137.0                 # radius at equator in meters (WGS-84)
        f=1/298.257223563           # flattening of the ellipsoid (WGS-84)
        b=(1-f)*a

        phi_1,L_1,=coord1           # (lat=L_?,lon=phi_?) #latitute longitude; phi1=start[0] phi2=start[2]
        phi_2,L_2,=coord2                  

        u_1=atan((1-f)*tan(radians(phi_1)))
        u_2=atan((1-f)*tan(radians(phi_2)))

        L=radians(L_2-L_1)

        Lambda=L                    # set initial value of lambda to L

        sin_u1=sin(u_1)
        cos_u1=cos(u_1)
        sin_u2=sin(u_2)
        cos_u2=cos(u_2)

        #--- BEGIN ITERATIONS -----------------------------+
        self.iters=0
        for i in range(0,maxIter):
            self.iters+=1
            
            cos_lambda=cos(Lambda)
            sin_lambda=sin(Lambda)
            sin_sigma=sqrt((cos_u2*sin(Lambda))**2+(cos_u1*sin_u2-sin_u1*cos_u2*cos_lambda)**2)
            cos_sigma=sin_u1*sin_u2+cos_u1*cos_u2*cos_lambda
            sigma=atan2(sin_sigma,cos_sigma)
            sin_alpha=(cos_u1*cos_u2*sin_lambda)/sin_sigma
            cos_sq_alpha=1-sin_alpha**2
            cos2_sigma_m=cos_sigma-((2*sin_u1*sin_u2)/cos_sq_alpha)
            C=(f/16)*cos_sq_alpha*(4+f*(4-3*cos_sq_alpha))
            Lambda_prev=Lambda
            Lambda=L+(1-C)*f*sin_alpha*(sigma+C*sin_sigma*(cos2_sigma_m+C*cos_sigma*(-1+2*cos2_sigma_m**2)))

            # successful convergence
            diff=abs(Lambda_prev-Lambda)
            if diff<=tol:
                break
            
        u_sq=cos_sq_alpha*((a**2-b**2)/b**2)
        A=1+(u_sq/16384)*(4096+u_sq*(-768+u_sq*(320-175*u_sq)))
        B=(u_sq/1024)*(256+u_sq*(-128+u_sq*(74-47*u_sq)))
        delta_sig=B*sin_sigma*(cos2_sigma_m+0.25*B*(cos_sigma*(-1+2*cos2_sigma_m**2)-(1/6)*B*cos2_sigma_m*(-3+4*sin_sigma**2)*(-3+4*cos2_sigma_m**2)))

        return b*A*(sigma-delta_sig)                 # output distance in meters     
        #self.km=self.meters/1000                    # output distance in kilometers
        #self.mm=self.meters*1000                    # output distance in millimeters
        #self.miles=self.meters*0.000621371          # output distance in miles
        #self.n_miles=self.miles*(6080.20/5280)      # output distance in nautical miles
        #self.ft=self.miles*5280                     # output distance in feet
        #self.inches=self.feet*12                    # output distance in inches
        #self.yards=self.feet/3                      # output distance in yards
    
    def calculateBearing(self, init, dest):
        dL = dest[1] - init[1]
        x = cos(dest[0]) * sin(dL)
        y = cos(init[0]) * sin(dest[0]) - sin(init[0]) * cos(dest[0]) * cos(dL)
        return atan2(x,y)    
    
    def calculateDistance(self, latitude2, longitude2):
        start = []
        dest = [latitude2, longitude2]
        count = 0

        coordinate = self.getPosition()
        start.append(coordinate['latitude'])
        start.append(coordinate['longitude'])
        
        print(start)
       
        if start[0] != 500.0 and start[1] != 500.0: #nilai default anafi kalo ga nemu titik gps asal
            self.write("{},{}\n".format(start[0], start[1]))

        distance = self.vincenty_inverse(start, dest)
        bearing = self.calculateBearing(start, dest)
        normalizeBearing = (degrees(bearing) + 360) % 360
        return distance, normalizeBearing

if __name__ == "__main__":
    drone = Drone()
    distance = drone.vincenty_inverse([39.152501,-84.412977],[39.152505,-84.412946])
    print(distance)

    distance2 = drone.vincenty_formula(radians(39.152501), radians(-84.412977), radians(39.152505), radians(-84.412946))
    print(distance2)