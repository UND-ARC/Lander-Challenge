---------Python based GUI setup---------


PLEASE READ STEPS IN ORDER BEFORE INSTALLING APPLICATIONS IF YOU ARE A FIRST TIME USER. SOME REQUIRE SPECIFIC INSTALL ORDERS. 

Prerequisites:

PyCharm		- https://www.jetbrains.com/pycharm/download
Python 3.14+ and following modules:
	- labjack-ljm
	- PyQt6
	- prometheus_client
	- DearPyGui (and its prerequisites)

It is easiest to run the application THROUGH PYCHARM


How to get everything set up:

1. run the "preset_editor.py" and create your preset using the software
2. connect all labjack hardware prior to running the program
3. run "main.py"
4. within the application select the preset you made in step 1
5. run the preset
6. once complete press "kill + create csv" to grate the csv log. There will be additional log files that saved on device. The bin can be ignored, but the 2 csv files created will contain all information from the last run.



