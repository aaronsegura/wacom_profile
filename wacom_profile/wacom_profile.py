"""Map Wacom Intuos Pro tablet buttons."""

import argparse
import re
import subprocess
import time
import os

from configparser import ConfigParser
from typing import Dict, AnyStr


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Handle Wacom Intuos Pro 5 mode function swapping.  You know, for kids.')

    parser.add_argument(
        "-c",
        dest="config_file",
        help="Configuration File.  Default $HOME/.wacomProfile",
        metavar="/path/to/file.ini",
        default=f"{os.environ.get('HOME')}/.wacomProfile",
        type=str)

    parser.add_argument(
        "-p",
        dest="profile",
        type=str,
        help="Profile to execute.",
        default="defaults")

    parser.add_argument(
        "-x",
        dest="exit",
        action="store_true",
        help="Apply profile for current LED state and exit.")

    parser.add_argument(
        "-d",
        dest="debug",
        action="store_true",
        help="Debug - Crank up the output")

    return parser.parse_args()


def parse_config(config_file: AnyStr, profile: AnyStr) -> ConfigParser:
    """Parse user-supplied config file.

    Args
    ----
        config_file (AnyStr): File path

        profile (AnyStr): User-selected profile

    Raises
    ------
        RuntimeError: If no file or file missing profile section

    Returns
    -------
        ConfigParser: Config namespace.

    """
    if not os.path.isfile(config_file):
        raise RuntimeError(f"No such config file: {config_file}")

    config = ConfigParser()
    config.read(config_file)

    if not config.has_section('defaults'):
        raise RuntimeError("Missing [defaults] section in config file.")

    if not config.has_option('defaults', 'device_id'):
        raise RuntimeError("Missing device_id in [defaults] section.")

    has_config = False

    for item in [0, 1, 2, 3]:
        if config.has_section('%s:%s' % (profile, item)):
            has_config = True

    if not has_config:
        raise RuntimeError(f"No valid configuration found for profile \"{profile}\"")

    return config


def get_profile(profile: AnyStr, config: ConfigParser, debug: bool = False) -> Dict:
    """Return user-defined profile configuration.

    Args
    ----
        profile (AnyStr): Profile name

        config (ConfigParser): config object returned from parse_config()

    Returns
    -------
        dict: Profile configuration

    """
    profile_config = {str(x): {} for x in [0, 1, 2, 3]}

    for mode in profile_config:
        section = f'{profile}:{mode}'

        if config.has_section(section):
            options = config.options(section)
            for opt in options:
                profile_config[mode][opt] = config.get(section, opt)

    return profile_config


def get_usb_bus(device_id, debug: bool = False) -> int:
    """Get USB bus for user device.

    Args
    ----
        device_id (AnyStr): The device identifier
        debug (bool): Print debug information

    Returns
    -------
        int: USB bus ID

    """
    cmd = ["lsusb", "-d", device_id]
    output = subprocess.check_output(cmd)
    match = re.match(br'Bus ([0-9]+)', output)

    ret = False
    if match:
        ret = int(match.group(1))

    if debug:
        print(f"Found device on USB Bus{ret}")

    return ret


def get_led_path(usb_bus: int, debug: bool = False) -> AnyStr:
    """Get path to LED status file.

    Args
    ----
        usb_bus (int): The USB Bus ID
        debug (bool): Print debug information

    Raises
    ------
        RuntimeError: No LED status file exists

    Returns
    -------
        str: Path to LED status file.

    """
    sys_path = f"/sys/bus/usb/devices/usb{usb_bus}/"
    cmd = ["find", sys_path, "-name", "status_led0_select"]
    output = subprocess.check_output(cmd).strip()

    if not output:
        raise RuntimeError("Unable to find status_led0_select file for usb device.")

    if debug:
        print(f"Found LED status file at {output.decode('utf-8')}")

    return output


def get_tablet_name(debug: bool = False) -> AnyStr:
    """Get tablet name from xsetwacom so we can use it later.

    Args
    ----
        debug (bool, optional): Print debug information. Defaults to False.

    Raises
    ------
        RuntimeError: When unable to find device name

    Returns
    -------
        AnyStr: Tablet name

    """
    cmd = ["xsetwacom", "--list", "devices"]
    output = subprocess.check_output(cmd)

    for line in output.split(b"\n"):
        match = re.match(br"^([A-Za-z0-9\(\) ]+)\t.*\ttype: PAD", line)
        if match:
            ret = match.group(1).strip().decode('utf-8')
            if debug:
                print(f"Found tablet PAD device named \"{ret}\"")
            return ret

    raise RuntimeError("Unable to find tablet PAD device in `xsetwacom --list devices`")


def get_led_state(led_path: AnyStr) -> AnyStr:
    """Get current LED state.

    Args
    ----
        led_path (AnyStr): Path to LED status file.

    Raises
    ------
        RuntimeError: File doesn't exist

    Returns
    -------
        AnyStr: Current LED state

    """
    try:
        with open(led_path, "r") as fp:
            return fp.read().strip()
    except IOError:
        raise RuntimeError("LED Status file went away.")


def monitor_led(led_path: AnyStr, mode: AnyStr, debug=False) -> AnyStr:
    """Periodically check LED status file to determine when it changes.

    Args
    ----
        led_path (AnyStr): Path to LED status file.

        mode (AnyStr): Current LED status

        debug (bool, optional): Print debug information. Defaults to False.

    Returns
    -------
        AnyStr: New state of LED.

    """
    current_mode = get_led_state(led_path)

    while mode == current_mode:
        time.sleep(0.25)
        current_mode = get_led_state(led_path)

    if debug:
        print(f"Changed mode {mode} -> {current_mode}")

    return current_mode


def update_tablet(tablet_name: AnyStr, actions: Dict[str, str], debug=False) -> None:
    """Send new configuration to tablet.

    Args
    ----
        tablet_name (AnyStr): Tablet name as seen by xsetwacom.

        actions (Dict[str, str]): New actions to set.

        debug (bool, optional): Print debug information.. Defaults to False.

    Returns
    -------
        None

    """
    for action in actions:
        cmd = ["xsetwacom", "--set", tablet_name]

        if " " in action:
            cmd.extend(action.split(" "))
        else:
            cmd.append(action)

        if " " in actions[action]:
            cmd.extend(actions[action].split(" "))
        else:
            if actions[action]:
                cmd.append(actions[action])

        if debug:
            print(f"Running: {' '.join(cmd)}")

        output = subprocess.check_output(cmd)

        if debug and output:
            print(f"Output: {output.decode('utf-8')}")


def main() -> None:
    """Gather configuration and perform main program loop."""
    try:
        args = parse_args()
        config = parse_config(args.config_file, args.profile)
        profile = get_profile(args.profile, config)
        usb_device = get_usb_bus(config.get('defaults', 'device_id'), debug=args.debug)
        led_path = get_led_path(usb_device, debug=args.debug)
        tablet_name = get_tablet_name(debug=args.debug)

        mode = None

        while True:
            mode = monitor_led(led_path, mode, debug=args.debug)
            update_tablet(tablet_name, profile[mode], debug=args.debug)
    except KeyboardInterrupt:
        print("\nCaught Interrupt.  Exiting.")
    except RuntimeError as e:
        print(e)
