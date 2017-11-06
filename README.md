# wacomProfile

This python script will allow you to control the modes of your Wacom Intuos Pro tablet
in linux by clicking the button in the middle of the touch wheel.

	usage: wacomProfile.py [-h] [-c /path/to/file.ini] [-p PROFILE] [-x] [-d]

	Handle Wacom Intuos Pro 5 ring function swapping. You know, for kids.

	optional arguments:
  	-h, --help            show this help message and exit
  	-c /path/to/file.ini  Configuration File. Default $HOME/.wacomWrap
  	-p PROFILE            Profile to execute.
 	-x                    Apply profile for current LED state and exit.
  	-d                    Debug - Crank up the output


Config File Format
------------------

Default location is $HOME/.wacomProfile

Configuration is in argparse/INI format.  The only required section is [defaults]
and the only required option is "device\_id".  This device\_id can be found by running
lsusb and copying the ID from the output there.  See the example config.cfg file.

You must also supply at least one stanza for each profile you want to create.


Profiles
--------

Profiles are defined in the config file in the section headers.  For example:

[krita:0]

This section header defines the actions that will be taken when '-p krita' is passed
in and the LED is in position 0 (upper-left corner).  LED Positions:

	0 - Upper-left
	1 - Upper-right
	2 - Lower-right
	3 - Lower-left
	
You don't have to define all LED positions.  Any positions left undefined are set to
the pad defaults, which are Button +4 and Button +5

Valid options in each section are "scroll\_up" and "scroll\_down".  Valid values for
these options are the same options you would use to define actions with xsetwacom:

	scroll_up = key +up
	scroll_down = key +down


Just Turrible
-------------
* Unpredictable results if using multiple tablets.  Do people even do that?
* Need to be able to define buttons, too.  Why not?  It's linux.
