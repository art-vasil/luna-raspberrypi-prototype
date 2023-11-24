# Luna-RaspberryPi-Prototype
Luna prototype IoT module based on Raspberry Pi

The project is to check if the bike is on road or sidewalk while driving, and if it is on sidewalk, the frame, the 
inference and GPS result at that time are sent to AWS IoT using MQTT.
The environment to run the deep learning mask-rcnn model for road segmentation is OpenVino and IoT device is Raspberry Pi
4B, which is powered by 5V rechargeable battery. If battery level is low to support RPi, all the processes are automatically
stopped and RPi is shut down. 

## Structure

- src

    The main source code for road segmentation, battery management, MQTT, Sense Hat.

- utils

    * Mask RCNN model for OpenVino
    * The source code for management of folders and files of the application
    
- app

    The main execution file
    
- config

    The configuration file for MQTT and Segmentation

- pi_installation

    The file to install the environment of the project
    
- requirements

    All the dependencies for the project
    
- settings

    Several constant settings

## Installation

- Environment

    Raspbian OS, python 3.7
    
- Dependency Installation

    Please run the following commands in the terminal.
    ```
        sudo apt-get update
        sudo apt-get install -y git
        git clone https://github.com/Luna-Scooters/Luna-RaspberryPi-Prototype
        cd Luna-RaspberryPi-Prototype
        bash pi_installation.sh 
    ```
    * Please add the following command line into /home/pi/.bashrc.
    ```
        vi /home/pi/.bashrc        
    ```
    ```
        source /opt/intel/openvino/bin/setupvars.sh
    ```

- Hardware Configuration of Battery Usage
    
    Please configure the hardware for battery management as below.
    ![Image](../main/hardware/battery_management.png?raw=true)

## Execution

- Please set some configurations for MQTT and road segmentation in config.cfg file.

- Please run the following command in the terminal.

    ```
        python3 app.py
    ```
