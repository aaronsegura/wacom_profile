#!/usr/bin/env python

import argparse
import re
import syslog
import subprocess
import time
import os

from ConfigParser import ConfigParser

def parseArgs():
    parser = argparse.ArgumentParser(
                    description='Handle Wacom Intuos Pro 5 ring '
                                'function swapping.  You know, for kids.')

    parser.add_argument("-c", 
                            dest="configFile",
                            help="Configuration File.  Default $HOME/.wacomWrap",
                            metavar="/path/to/file.ini",
                            default="%s/%s" % (os.environ["HOME"], "/.wacomWrap"),
                            type=str)

    parser.add_argument("-p",
                            dest="profile",
                            type=str,
                            help="Profile to execute.",
                            default="defaults")
   
   
    parser.add_argument("-x",
                            dest="exit",
                            action="store_true",
                            help="Apply profile for current LED state and exit.")

    parser.add_argument("-d",
                            dest="debug",
                            action="store_true",
                            help="Debug - Crank up the output")

    return parser.parse_args()

def parseConfig(args):

    if not os.path.isfile(args.configFile):
        raise RuntimeError("No such config file: %s" % args.configFile)

    config = ConfigParser()
    config.read(args.configFile)

    if not config.has_section('defaults'):
        raise RuntimeError("Missing [defaults] section in config file.")

    if not config.has_option('defaults','device_id'):
        raise RuntimeError("Missing device_id in [defaults] section.")

    hasConfig = False

    for item in [0,1,2,3]:
        if config.has_section('%s:%s' % (args.profile, item)):
            hasConfig = True

    if not hasConfig:
        raise RuntimeError("No valid configuration found for profile \"%s\"" % args.profile)

    return config

def getProfile(profile, configFile):

    profileConfig = { str(x):{} for x in [0,1,2,3] }

    for mode in profileConfig:
        section = '%s:%s' % (profile, mode)
        if configFile.has_section(section):
            if configFile.has_option(section, 'scroll_up'):
                profileConfig[mode]['up'] = configFile.get(section, 'scroll_up')
            if configFile.has_option(section, 'scroll_down'):
                profileConfig[mode]['down'] = configFile.get(section, 'scroll_down')

    return profileConfig

def findUSBBus(deviceID):
    cmd = "lsusb -d %s" % deviceID

    output = subprocess.check_output(cmd.split(" "))

    match = re.match('Bus ([0-9]+)', output)

    ret = False

    if match:
        ret = int(match.group(1))

    return ret

def findLEDPath(usbBus):
    sysPath = "/sys/bus/usb/devices/usb%s/" % usbBus

    cmd = "find %s -name status_led0_select" % sysPath

    output = subprocess.check_output(cmd.split(" ")).strip()

    if not output:
        raise RuntimeError("Unable to find status_led0_select file for usb device.")
            
    return output

def findTabletName():
    
    cmd = "xsetwacom --list devices"

    output = subprocess.check_output(cmd.split(" "))

    ret = ""
    for line in output.split("\n"):
        match = re.match("^([A-Za-z0-9 ]+)\t.*type: PAD", line)
        if match:
            ret = match.group(1)

    if not ret:
        raise RuntimeError("Unable to find tablet PAD Device in xsetwacom --list devices")

    return ret.strip()

def currentLEDState(ledPath):
    try:
        with open(ledPath, "r") as fp:
            return fp.read().strip()
    except IOError:
        raise RuntimeError("LED Status file went away.")

def monitorLED(ledPath, oldMode, debug=False):
    currentMode = currentLEDState(ledPath)

    while oldMode == currentMode:    
        time.sleep(0.25)
        currentMode = currentLEDState(ledPath)

    if args.debug:
        print "Changed mode %s -> %s" % (oldMode, currentMode)

    return currentMode

def updateTablet(tabletName, mode, profileConfig, debug=False):

    cmd = ["xsetwacom", "--set", tabletName, "AbsWheelUp"]

    if "up" in profileConfig[mode]:
        cmd.append(profileConfig[mode]["up"])

    if args.debug:
        print "Running: %s" % " ".join(cmd)

    output = subprocess.check_output(cmd)

    if args.debug:
        print "Output: %s" % output

    cmd = ["xsetwacom", "--set", tabletName, "AbsWheelDown"]

    if "down" in profileConfig[mode]:
        cmd.append(profileConfig[mode]["down"])

    if args.debug:
        print "Running: %s" % " ".join(cmd)

    output = subprocess.check_output(cmd)

    if args.debug:
        print "Output: %s" % output

def main(args):

    configFile = parseConfig(args)

    profileConfig = getProfile(args.profile, configFile)
    
    USBDevice = findUSBBus(configFile.get('defaults','device_id'))
    ledPath = findLEDPath(USBDevice)
    tabletName = findTabletName()

    mode = None

    if args.exit:
        print "Setting modes for profile %s, LED %s" % (args.profile, currentLEDState(ledPath))

        updateTablet(tabletName, currentLEDState(ledPath), profileConfig)
    else:
        while True:
            mode = monitorLED(ledPath, mode, debug=args.debug)
            updateTablet(tabletName, mode, profileConfig, debug=args.debug)


if __name__ == '__main__':

    args = parseArgs()

    try:
        main(args)
    except KeyboardInterrupt:
        print "Caught CTRL-C" 
    except RuntimeError, e:
        print "Error: %s " % e
