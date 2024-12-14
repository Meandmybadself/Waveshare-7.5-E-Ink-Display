#!/bin/bash

rsync -avz . planeframe:/home/jeffery/planeframe --exclude .git --exclude __pycache__ --exclude .DS_Store
# ssh planeframe 'cd /home/jeffery/planeframe && git pull && sudo systemctl restart planeframe'
