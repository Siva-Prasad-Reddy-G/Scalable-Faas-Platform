#! /usr/bin/bash

# Step 1: Update and Upgrade Ubuntu (all nodes)
sudo apt update
sudo apt upgrade

# Step 2: Disable Swap (all nodes) for performance
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# Step 3: Add kernel parameters (all nodes)
#
# 3a) Load required kernel modules..
sudo tee /etc/modules-load.d/containerd.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

# 3b) Configure critical kernel parameters..
sudo tee /etc/sysctl.d/kubernetes.conf <<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF

# 3c) restart the system changes
sudo sysctl --system
