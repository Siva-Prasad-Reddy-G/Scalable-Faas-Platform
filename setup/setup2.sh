#! /usr/bin/bash

# Step 4: Install containerd runtime (all nodes)

# 4a) Install all required dependencies
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates

# 4b) Enable docker repository:

sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmour -o /etc/apt/trusted.gpg.d/docker.gpg

sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable"

# 4c) Install containerd:

sudo apt update
sudo apt install -y containerd.io


# 4d) Configure containerd to start using systemd

containerd config default | sudo tee /etc/containerd/config.toml >/dev/null 2>&1
sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml

# 4e) Restart and enable containerd service:

sudo systemctl restart containerd
sudo systemctl enable containerd
