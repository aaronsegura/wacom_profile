# wacomProfile

This python script will allow you to control the modes of your Wacom Intuos Pro tablet
touch ring in linux by clicking the button in the middle of the ring.

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

	[defaults]
	device_id = XXXX:XXXX


Profiles
--------

Profiles are defined in the config file in the section headers.  For example:

[krita:0]

This section header defines the actions that will be taken when '-p krita' is passed
in and the LED is in position 0 (upper-left corner).  

LED Positions:

	0 - Upper-left
	1 - Upper-right
	2 - Lower-right
	3 - Lower-left
	
Buttons:

	Button 2 - Upper top button
   	Button 3 - Middle top Button
   	Button 8 - Lower top Button

   	Button 1 - Wheel Button
   	
   	Button 9 -  Upper bottom button
   	Button 10 - Middle bottom button
   	Button 11 - Lower bottom button

 TouchRing Actions:

   	AbsWheelUp - Scroll Up
   	AbsWheelDown - Scroll Down

You don't have to define all LED positions.  No action will be taken if you select
a mode that isn't defined.

Valid options in each section are either buttons or touchring actions.  If you define
a blank action (eg, "button 1 = "), that item is reset to tablet defaults.

See the example config.cfg for a working example.

If no profile is provided on the command line with -p, the script will look for a
profile called "defaults".

Just Turrible
-------------
* Unpredictable results if using multiple tablets.  Do people even do that?
* USB Stuff is mostly untested in most situations.  It worked once for me, so it might work for you.  Submit a bug if not.
