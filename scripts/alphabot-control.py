#!/usr/bin/python

import picamera
from pkg_resources import resource_filename
import os
import sys
import threading

from bottle import (
    get,
    post,
    request,
    response,
    route,
    run,
    static_file,
    template,
)

parent_dir = os.path.split(os.path.dirname(__file__))[-1]
if dir == 'scripts':
    sys.path.append(os.path.join(parent_dir, '..'))

from alphabot_control_lib.utils.mjpeg import HTTPMJPEGStream
from alphabot_control_lib.waveshare.AlphaBot import AlphaBot
from alphabot_control_lib.waveshare.PCA9685 import PCA9685

Ab = AlphaBot()
pwm = PCA9685(0x40)
pwm.setPWMFreq(50)

#Set the Horizontal servo parameters
HPulse = 1500  #Sets the initial Pulse
HStep = 0      #Sets the initial step length
pwm.setServoPulse(0,HPulse)

#Set the vertical servo parameters
VPulse = 1500  #Sets the initial Pulse
VStep = 0      #Sets the initial step length
pwm.setServoPulse(1,VPulse)

data_path = resource_filename('alphabot_control_lib', 'data')


@get('/')
def index():
    return template(os.path.join(data_path, 'index.html'))


@route('/<filename>')
def server_static(filename):
    return static_file(filename, root=data_path)


@route('/fonts/<filename>')
def server_fonts(filename):
    return static_file(filename, root=os.path.join(data_path, 'fonts'))



@route('/cam.mjpeg')
def mjpeg():
    try:
        boundary = '--jpgboundary'
        response.set_header('Content-type', 'multipart/x-mixed-replace; boundary=' + boundary)

        camera = picamera.PiCamera(resolution=(320, 240), framerate=20)
        return HTTPMJPEGStream(camera, content_type_header=False, boundary=boundary)

    except Exception as e:
        print(e)


@post("/cmd")
def cmd():
    global HStep, VStep
    code = request.body.read().decode()
    speed = request.POST.get('speed')
    print(code)
    if (speed != None):
        Ab.setPWMA(float(speed))
        Ab.setPWMB(float(speed))
        print(speed)
    if code == "stop":
        HStep = 0
        VStep = 0
        Ab.stop()
    elif code == "forward":
        Ab.forward()
    elif code == "backward":
        Ab.backward()
    elif code == "turnleft":
        Ab.left()
    elif code == "turnright":
        Ab.right()
    elif code == "up":
        VStep = -5
    elif code == "down":
        VStep = 5
    elif code == "left":
        HStep = 5
    elif code == "right":
        HStep = -5
    return "OK"


def timerfunc():
    global HPulse, VPulse, HStep, VStep, pwm

    if (HStep != 0):
        HPulse += HStep
        if (HPulse >= 2500):
            HPulse = 2500
        if (HPulse <= 500):
            HPulse = 500
        # set channel 2, the Horizontal servo
        pwm.setServoPulse(0, HPulse)

    if (VStep != 0):
        VPulse += VStep
        if (VPulse >= 2500):
            VPulse = 2500
        if (VPulse <= 500):
            VPulse = 500
        # set channel 3, the vertical servo
        pwm.setServoPulse(1, VPulse)

    global t  # Notice: use global variable!
    t = threading.Timer(0.02, timerfunc)
    t.start()


t = threading.Timer(0.02, timerfunc)
t.setDaemon(True)
t.start()


def main():
    run(server='paste', host='alphabot.local', port=8080)

if __name__ == "__main__":
    main()