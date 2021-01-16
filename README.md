# Slide digitalisation project

We have a lot of slides that have been sitting in the basement for a long time. We have now decided to digitise them. While we do own a reasonable scanner that can scan four slides in one go, it is rather slow (i.e. over a minute per slide) and manual. 
Inspired by a [c't article from 12/2015](https://www.heise.de/ct/ausgabe/2015-12-Diaprojektoren-zum-Digitalisierer-umbauen-2640304.html), we decided to photograph each slide as it was illuminated by our old projector. The [blog by PeschiMo](https://homemadediascanner.blogspot.com/) also documents a similar setup. The website by thomas on analogue photography also gives a [comprehensive introduction](https://analoge-fotografie.net/abfotografieren-negative-dias/).

We used:
 - Revue universal 600 AF
 - Pentax K-50, with a 50mm F1.8 Pentax prime with a macro ring
 
In contrast to the equipment used in the c't article, our projector does not have an inbuild timer for automatically advancing the slides, but a wired remote control. Hence we used a relay and a Raspberry Pi to automatically advance the slides, and also to control the DSLR using [gphoto2](http://www.gphoto.org/). 

This project contains the code to control the projector and the DSLR. You can:
 - Take a batch of pictures, automatically advancing the slides
 - Manually move the slide tray forward or backward
 - Set the shutter speed settings of the camera (required since the Pentax K-50 cannot determine shutterspeed itself when controlled via gphoto2. Annoying, but this is the only DSLR we had available).
 - Pictures are automatically downloaded from the camera to a location of your choice, a network share in our case. 
 
 A picture takes between 7-8 seconds including automatically advancing. Digitising a slide tray of 36 slides around 4 minutes 20 seconds. The quality is more than good enough, our slides from 1960-1990 lack in initial picture quality and craftsmanship anyway. 

![Screenshot of main UI, showing batch taking, setting of shutter speed](/img/mainscreen.png?raw=true "Screenshot of the app's main screen")

## Development notes

In order to facilitate development outside of the Raspberry Pi, the `GPIO` and `gphoto2` are mocked when unavailable. The Pipfile only tries to install them when on a linux system running on `armv7l`. `gphoto2` requires [compilation of the system libraries](https://maskaravivek.medium.com/how-to-control-and-capture-images-from-dslr-using-raspberry-pi-fdfa9d600ec1) before the python library can be installed.

We have now finished scanning our entire slide collection, so I don't expect this project to receive any further updates. But may it be helpful for someone else in future.