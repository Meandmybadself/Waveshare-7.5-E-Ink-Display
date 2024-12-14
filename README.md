# Planeframe

## Overview
This is a project to display closest aircraft data on an e-ink display.

## Hardware
- Raspberry Pi Zero W
- [Waveshare 7.5" e-ink display](https://www.waveshare.com/7.5inch-e-paper-hat.htm)

## Related
- [adsb.lol](https://adsb.lol) - The API used to get the closest aircraft data.
- [adsb.lol-api](https://github.com/adsb-lol/adsb.lol-api) - The API used to get the closest aircraft data.

## Setup

### System Update
```
sudo apt-get update
sudo apt-get full-upgrade -y
```

### System Dependencies

TODO: Determine if these all are needed.

```
sudo apt-get install -y \
    python3-pip \
    python3-setuptools \
    python3-dev \
    libtiff5-dev \
    libjpeg8-dev \
    libopenjp2-7-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    python3-rpi.gpio \
    swig

```

### Virtual Environment
```
python3 -m venv ~/venvs/planeframe
source ~/venvs/planeframe/bin/activate
pip install -r requirements.txt
```

### Promote
./promote.sh

### Run
./run.sh


## Research
* https://www.waveshare.com/wiki/Libraries_Installation_for_RPi#lgpio
* https://github.com/gpiozero/lg