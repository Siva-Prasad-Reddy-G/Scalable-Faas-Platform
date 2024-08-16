Functions as a Service (FaaS) Implementation

This repository contains an implementation of Functions as a Service (FaaS) using Docker and Kubernetes. The implementation includes functionalities for deploying, scaling, and managing serverless functions within a Kubernetes cluster.
Directory Structure

The repository is structured as follows:

    docker: Contains Docker-related files for building Docker images.
        setup: Scripts for setting up Docker on worker nodes.
        setup-master: Scripts for setting up Docker on the master node.
    src: Contains the Python implementation of the FaaS platform.
    report: container report and scripts used to generate the report.
    examples: Example function implementations for testing and demonstration purposes.
        example1: Basic example function.
        example2: Example function demonstrating autoscaling functionality.

Usage

To reproduce and test the FaaS implementation, follow these steps:

    On both the files, run
    1. Docker-install.sh 
    2. setup.sh
    3. setup2.sh
    4. setup3.sh
    On master node initialize Kubernetes cluster by running
    1. setup-master.sh
    On worker node, join the node to master/cluster with the instructions generated in above step.
    
Once the setup is done, confirm that the nodes are all up by running
bash kubectl get nodes

Then run faas platform using the below command
python faas.py
It would show an interactive menu. Follow the below sequence to reproduce the metrics.
1. Build example2
2. Deploy example2
3. Scale example2
4. Expose example2 as ClusterIP
5. Check logs and get metrics as and when required.

Now your function is deployed and ready for experiments.

Test Autoscaling: Use curl commands to trigger CPU and memory-intensive tasks and observe the scaling behavior.

    CPU Usage: Trigger CPU-intensive task with specified CPU percentage.

    bash

curl -X GET http://<cluster-ip>:5000/occupy_cpu/10

Memory Usage: Allocate memory with specified memory size in MBs.

bash

        curl -X GET http://<cluster-ip>:5000/allocate_memory/10

    Replace <cluster-ip> with the actual IP address of your Kubernetes cluster.

Contributing

Contributions to this project are welcome! Feel free to submit bug reports, feature requests, or pull requests to help improve the FaaS implementation.