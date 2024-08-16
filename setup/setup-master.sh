#! /usr/bin/bash

# Setup kubernetes master..

sudo kubeadm init > /tmp/log.txt

# Update the below commands based on the log file.

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

#sudo kubeadm token create --print-join-command
# to create....

#kubeadm join 10.129.131.202:6443 --token 7fc5vq.vr3ripjxomnqomgd --discovery-token-ca-cert-hash sha256:12b0ca48c0497cb4d3f94d1debba78ae14a9f883858298331dcfa00987391019 


#kubeadm join 10.129.131.202:6443 --token 7pm28n.afbepf5vx2x5cmaw \
#	--discovery-token-ca-cert-hash sha256:12b0ca48c0497cb4d3f94d1debba78ae14a9f883858298331dcfa00987391019


# Check cluster node status
kubectl get nodes


# Setup network plugin

kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.25.0/manifests/calico.yaml
