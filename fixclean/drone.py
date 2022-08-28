import olympe
from droneState import DroneState
from olympe.messages.ardrone3.PilotingSettings import MaxTilt
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing, moveTo
from olympe.messages.ardrone3.PilotingState import moveToChanged, FlyingStateChanged
from olympe.messages.ardrone3.GPSSettingsState import HomeChanged
from olympe.enums.ardrone3.Piloting import MoveTo_Orientation_mode
from olympe.messages.ardrone3.GPSSettingsState import GPSFixStateChanged
from olympe.messages.move import extended_move_by, extended_move_to

class Drone():
    state = DroneState.LAND
    atDest = False
    medsArrived = False

    home_latitude = 0.0
    home_longitude = 0.0
    home_altitude = 0.0

    dest_latitude = 0.0
    dest_longitude = 0.0
    dest_altitude = 0.0

    def __init__(self, ip):
        self.DRONE_IP = ip
        self.drone = olympe.Drone(self.DRONE_IP)
        
        with open('./coordinate.txt') as f:
            lines = f.read().split(' ')
            print(lines[0])
            
            self.dest_latitude = lines[2]
            self.dest_longitude = lines[3]
            
        print('coordinate destination latitude: ', self.dest_latitude)
        print('coordinate destination longitude: ', self.dest_longitude)

    def connectToDrone(self):
        self.drone.connect()

    def waitGPSFix(self):
        self.drone(GPSFixStateChanged(_policy = 'wait'))
    
    def takeoff(self):
        if self.state == DroneState.LAND:
            assert self.drone(
                TakeOff()
                >> FlyingStateChanged(state="hovering", _timeout=10)
            ).wait().success()
            self.state = DroneState.TAKEOFF
            
            home_position = self.drone.get_state(HomeChanged)
            self.home_latitude = home_position['latitude']
            self.home_longitude = home_position['longitude']
            self.home_altitude = home_position['altitude']
    
    def get_current_position(drone):
        while True:
            current_position = drone.get_state(HomeChanged)
            print('current_position = ' + str(current_position))
            if current_position['latitude'] != 500.0:
               break
        return f"position|{current_position['latitude']}|{current_position['longitude']}"

    def moveByVertical(self, dist, high, speedY):
        if self.state == DroneState.TAKEOFF:
            assert self.drone(
                extended_move_by(dist, 0, high, 0, 0, speedY, 0)
                >> FlyingStateChanged(state="hovering", _timeout=10)
            ).wait().success()    
    
    def moveToDest_speed(self, dest_latitude, dest_longitude, speedX, timeout=60):
        if self.state == DroneState.TAKEOFF:
            assert self.drone(
                extended_move_to(latitude = dest_latitude,
                                longitude = dest_longitude,
                                altitude = 2,
                                orientation_mode = MoveTo_Orientation_mode.TO_TARGET,
                                max_horizontal_speed = speedX,
                                max_vertical_speed = 0,
                                max_yaw_rotation_speed = 0)
                        >> moveToChanged(status='DONE', _timeout=timeout)
                        >> FlyingStateChanged(state="hovering", _timeout=10)).wait().success()

    def rth(self, heading=0, timeout=60):
        assert self.drone(moveTo(latitude=self.home_latitude,
                                longitude=self.home_longitude,
                                altitude=self.home_altitude,
                                orientation_mode=MoveTo_Orientation_mode.HEADING_DURING,
                                heading=heading)
                        >> moveToChanged(status='DONE', _timeout=timeout)
                        >> FlyingStateChanged(state="hovering", _timeout=10)).wait().success()

    def land(self):
        if self.state == DroneState.TAKEOFF:
            assert self.drone(
                Landing()
                >> FlyingStateChanged(state="landed", _timeout=10)
            ).wait().success()
            self.state = DroneState.LAND

    def disconnectFromDrone(self):
        self.drone.disconnect()
