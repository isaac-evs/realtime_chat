#!/bin/bash

# Install required system packages
apt-get update
apt-get install -y \
    python3.11-venv \
    python3-pip \
    python3-dev \
    build-essential

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
