#!/bin/bash

# Install required system packages
apt-get update && apt-get install -y python3-venv python3-pip

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
