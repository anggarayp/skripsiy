import py_qmc5883l
from time import sleep

class Compass:
    sensor = py_qmc5883l.QMC5883L()
    # matrix kalibrasi kompas
    sensor.calibration = [[1.0286847433172306, -0.04077398090389861, 426.817451958867], [-0.04077398090389861, 1.0579582498042726, -212.09840291381101], [0.0, 0.0, 1.0]]
    # untuk menyesuaikan posisi utara yang ditangkap kompas dengan posisi utara sebenarnya
    sensor.declination = -99

    def formula(self, x):
        # fungsi kalibrasi kompas agar hasil ukur lebih mendekati nilai sebenarnya
        y = 6e-6*x*x*x - 0.0041*x*x + 1.7187*x - 4.066
        return y % 360.0

    def getDroneBearing(self):
        bearing = self.sensor.get_bearing()
        return self.formula(bearing)
