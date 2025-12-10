---------Python based GUI setup---------


PLEASE READ STEPS IN ORDER BEFORE INSTALLING APPLICATIONS IF YOU ARE A FIRST TIME USER. SOME REQUIRE SPECIFIC INSTALL ORDERS. 

Prerequisites:

Grafana		- https://grafana.com/grafana/download
Prometheus 	- https://prometheus.io/download/#prometheus	- this comes with the GIT repo
PyCharm		- https://www.jetbrains.com/pycharm/download
Python 3.14+ and following modules (use pip install):
	- labjack-ljm
	- PyQt6
	- prometheus_client


How to get everything set up:

Install Python and PyCharm first. This will create your virtual environment. After it is successful, install all necessary libraries using pip install INSIDE OF YOUR VIRTUAL ENVIRIONMENT. 

Move "Prometheus" from "C:\Users\[YOUR USER]\Lander-Challenge\Ground Support Controls\GUI-Python to C:\" which should result in "C:\Prometheus\"

###Under C:\Users\[YOUR USER]\Lander-Challenge\Ground Support Controls\GUI-Python there should be a prometheus.yml file. Move it to the newly created C:\Prometheus\ folder.

Move all remaining files from "C:\Users\[YOUR USER]\Lander-Challenge\Ground Support Controls\GUI-Python" to your PyCharm environment, which will likely be "C:\Users\[YOUR USER]\PyCharmMiscProject\"

###Move the files extracted from the Prometheus .zip file to C:\Prometheus\

In command center open directory and run "prometheus.exe --config.file=prometheus.yml"

Press "allow" when prompted (this starts Prometheus, which is a translation layer between Grafana and Python)

In your chromium based browser, open a new tab and go to "http://localhost:9090/targets". It should bring up a Prometheus website now.

 

