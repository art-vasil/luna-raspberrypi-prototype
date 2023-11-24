#!/bin/bash

sudo curl -o GPG-PUB-KEY-INTEL-SW-PRODUCTS-2020.PUB https://apt.repos.intel.com/openvino/2020/GPG-PUB-KEY-INTEL-OPENVINO-2020
sudo apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS-2020.PUB
sudo su -c "echo 'deb https://apt.repos.intel.com/openvino/2020 all main' > /etc/apt/sources.list.d/intel-openvino-2020.list"
sudo apt-get update
sudo apt-get install -y --no-install-recommends intel-openvino-dev-ubuntu18-2020.1.023 ocl-icd-opencl-dev
cd /opt/intel/openvino/install_dependencies
sudo -E ./install_openvino_dependencies.sh
cd /opt/intel/openvino/deployment_tools/model_optimizer/install_prerequisites
sudo ./install_prerequisites.sh

sudo apt-get update
sudo apt-get install build-essential python3-dev python3-smbus python3-pip
python3 -m pip install -r requirements.txt
