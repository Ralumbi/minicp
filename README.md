# MiniCP - Raspberry PI
MiniCP focusses on having a robust control panel for the raspberry pi using a 480x320 touch display.
As the UIs need too much modification in order to work properly in such a small screen.

The main initial setup is to offer a wifi router setup with the use of an second, but external usb wifi adapter. 

## Setup
* Raspberry PI 5B 8GB
* MHS-3.5inch Display
* PHREEZE Dual Band USB Adapter

#### Software
* Raspberry PI OS LITE 64-bit
    * xserver-xorg
    * xinit
    * matchbox-window-manager
        * xterm
        * MiniCP

### Features
* Overview
    * Connected wlan
    * Connected Bluetooth

* Wifi
    * Connect to wifi network

* Router
    * Setup an Access Point

* Bluetooth
    * Connect to Bluetooth device
        * You got to go back to minicp via the top left corner

* USB
    * Mount usb device
        * (work in progress)
