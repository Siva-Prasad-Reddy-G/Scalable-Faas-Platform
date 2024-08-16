import os
import subprocess
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import json

# Docker Hub username (replace with your Docker Hub username)
docker_username = "msanth"

# Load Kubernetes config from default location
config.load_kube_config()

# Kubernetes API client
k8s_client = client.ApiClient()

# Initialize Kubernetes API client
apps_api = client.AppsV1Api(k8s_client)
core_api = client.CoreV1Api(k8s_client)
scale_api = client.AutoscalingV2Api(k8s_client)
metrics_api = client.CustomObjectsApi(k8s_client)

#function_name="default"
#deployment_name="default"

def get_user_deployment_info():
    function_name = input("Enter the function name: ")
    image_name = input("Enter the docker docker image name (include username/imagename:tag): ")

    cpu_res = input("Enter the initial cpu resource required in format 100m (1 core = 1000m): ")
    cpu_limit = input("Enter the Maximum cpu resource required in format 100m (1 core = 1000m): ")
    mem_res = input("Enter the initial memory required in format 100Mi (= 100MB): ")
    mem_limit = input("Enter the Maximum memory required in format 100Mi (= 100MB): ")
    return function_name, image_name, cpu_res, cpu_limit, mem_res, mem_limit

def print_info(function_name, image_name, cpu_res, cpu_limit, mem_res, mem_limit):
    print("Function name = %s " % function_name)
    print("image name = %s " % image_name)
    print("cpu resource = %s " % cpu_res)
    print("CPU limit = %s " % cpu_limit)
    print("Memory resource = %s " % mem_res)
    print("Memory limit = %s " % mem_limit)

def create_deployment():

    function_name, image_name, cpu_res, cpu_limit, mem_res, mem_limit = get_user_deployment_info()
    # Define labels for the deployment
    labels = {"function": function_name}
    try:
            # Define container spec with resource limits
            container = client.V1Container(
                name=function_name,
                image=image_name,
                resources=client.V1ResourceRequirements(
                    requests={"cpu": cpu_res, "memory": mem_res},
                    limits={"cpu": cpu_limit, "memory": mem_limit}
                )
            )

            # Define deployment spec
            deployment_spec = client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels=labels),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(containers=[container])
                )
            )

            # Define deployment object
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(name=function_name),
                spec=deployment_spec
            )

            # Create deployment
            print("Creating deployment...")
            apps_api.create_namespaced_deployment(namespace="default", body=deployment)
            print("Deployment created successfully.")
    except ApiException as e:
            print("Exception when creating deployment: %s\n" % e)

def update_deployment():

    deployment_name, image_name, cpu_res, cpu_limit, mem_res, mem_limit = get_user_deployment_info()
    namespace="default"
    print_info(deployment_name, image_name, cpu_res, cpu_limit, mem_res, mem_limit)

    try:
        # Fetch existing deployment
        deployment = apps_api.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        # Update deployment with new image
        deployment.spec.template.spec.containers[0].image = image_name

        # Update CPU limit for the container
        deployment.spec.template.spec.containers[0].resources.requests["cpu"] = cpu_res
        deployment.spec.template.spec.containers[0].resources.limits["cpu"] = cpu_limit
        deployment.spec.template.spec.containers[0].resources.requests["memory"] = mem_res
        deployment.spec.template.spec.containers[0].resources.limits["memory"] = mem_limit

        # Apply the updated deployment
        print("Updating deployment...")
        apps_api.replace_namespaced_deployment(name=deployment_name, namespace=namespace, body=deployment)
    except ApiException as e:
        print("Exception when updating deployment: %s\n" % e)

def rollback_deployment(function_name):

    # Rollback deployment to previous revision
    print("Rolling back deployment...")
    apps_api.rollback_namespaced_deployment(name=function_name, namespace="default")

def manual_scale():
    deployment_name = input("Enter the deployment name: ")
    replicas = int(input("Enter the number of replicas to scale to: "))

    try:
        # Get current replicas
        deployment = apps_api.read_namespaced_deployment(name=deployment_name, namespace="default")
        current_replicas = deployment.spec.replicas

        # Determine scaling action
        if replicas > current_replicas:
            action = "up"
        elif replicas < current_replicas:
            action = "down"
        else:
            action = "unchanged"

        # Scale deployment
        apps_api.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace="default",
            body={"spec": {"replicas": replicas}}
        )
        print(f"Deployment '{deployment_name}' scaled {action} to {replicas} replicas successfully.")
    except ApiException as e:
        if e.status == 404:
            print(f"Deployment '{deployment_name}' does not exist.")
        else:
            print(f"Error scaling deployment '{deployment_name}': {e}")

def scale_deployment():
    function_name = input("Enter the function name: ")
    min_replicas = int(input("Enter min replicas: "))
    max_replicas = int(input("Enter max replicas: "))
    cpu_target_percentage = int(input("Enter CPU target percentage: "))
    memory_target_percentage = int(input("Enter memory target percentage: "))
    namespace="default"
    try:
        # Check if HPA already exists
        hpa_exists = False
        try:
            scale_api.read_namespaced_horizontal_pod_autoscaler(name=f"{function_name}-hpa", namespace=namespace)
            hpa_exists = True
        except ApiException as e:
            pass

        # Define HorizontalPodAutoscaler object
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": f"{function_name}-hpa", "labels": {"function": function_name}},
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": function_name
                },
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,  # Adjust as needed
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": cpu_target_percentage  # Adjust as needed
                            }
                        }
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": memory_target_percentage  # Adjust memory utilization target as needed
                            }
                        }
                    }
                ]
            }
        }

        # Create or update HPA based on whether it already exists
        if hpa_exists:
            print("Updating HorizontalPodAutoscaler...")
            scale_api.replace_namespaced_horizontal_pod_autoscaler(name=f"{function_name}-hpa", namespace=namespace, body=hpa)
        else:
            print("Creating HorizontalPodAutoscaler...")
            scale_api.create_namespaced_horizontal_pod_autoscaler(namespace=namespace, body=hpa)

        print(f"HorizontalPodAutoscaler '{function_name}-hpa' created/updated successfully.")

    except ApiException as e:
        print(f"Error occurred while creating/updating HorizontalPodAutoscaler: {e}")

def get_cluster_ip(function_name, namespace):
    try:
        # Get cluster IP
        service = core_api.read_namespaced_service(name=function_name, namespace=namespace)
        destination_ports = [port.target_port for port in service.spec.ports]
        cluster_ip = f"{service.spec.cluster_ip}:{destination_ports}"
        return cluster_ip
    except Exception as e:
        print("Error retrieving cluster IP:", e)
        return None


def expose_service():
    function_name = input("Enter the function name: ")
    srv_type = input("Enter service type: LB(loadbalancer), NP(nodePort)i, CI(Cluster IP), or EN (external name): ")
    service_type="ClusterIP"
    if srv_type == "LB":
        service_type = "LoadBalancer"
    elif srv_type == "NP":
        service_type = "NodePort"
    elif srv_type == "CI":
        service_type = "ClusterIP"
    elif srv_type == "EN":
        service_type = "ExternalName"
    else:
        printf("Invalid choice")
        return

    src_port = int(input("Enter your cluster port: "))
    dst_port = int(input("Enter your port program is listening: "))
    namespace="default"
    try:
        # Check if service already exists
        service_exists = False
        try:
            core_api.read_namespaced_service(name=function_name, namespace=namespace)
            service_exists = True
        except ApiException as e:
            if e.status != 404:
                raise

        # Define service spec
        service_spec = client.V1ServiceSpec(
            selector={"function": function_name},
            ports=[client.V1ServicePort(protocol="TCP", port=src_port, target_port=dst_port)]
        )

        # Define service object
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=function_name, labels={"function": function_name}),
            spec=service_spec
        )

        # Create or update service based on service type
        if service_exists:
            print("Updating service...")
            core_api.replace_namespaced_service(name=function_name, namespace=namespace, body=service)
        else:
            print("Creating service...")
            core_api.create_namespaced_service(namespace=namespace, body=service)

        print("Cluster IP address = %s\n" % get_cluster_ip(function_name, namespace))

    except ApiException as e:
        print("Exception when updating deployment: %s\n" % e)


def get_deployment_info():
    try:
        # List deployments in all namespaces
        namespace="default"

        deployments = apps_api.list_namespaced_deployment(namespace=namespace).items

        # Print header
        #print("{:<30} {:<15} {:<20} {:<20} {:<20}".format(
        #    "Deployment", "Resource Limits", "Resource Usage", "Exposed URL", "HPDA Info"))

        print("{:<30} {:<15} {:<15} {:<20} {:<20} {:<20}".format(
            "Deployment", "Replicas", "Resource Limits", "Resource Usage", "Exposed URL", "HPDA Info"))

        for deployment in deployments:
            deployment_name = deployment.metadata.name
            replicas = deployment.status.replicas
            if replicas == None:
                replicas = 0

            # Get resource limits
            limits = deployment.spec.template.spec.containers[0].resources.limits

            # Get pods associated with the deployment
            pods = core_api.list_namespaced_pod(namespace=namespace, label_selector=f"function={deployment_name}").items

            # Initialize pod resource usage
            cpu_usage_total = 0
            memory_usage_total = 0

            # Get resource usage for each pod
            for pod in pods:
                pod_name = pod.metadata.name

                # Get resource metrics for the pod
                try:
                    metrics = metrics_api.get_namespaced_custom_object(
                        group="metrics.k8s.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="pods",
                        name=pod_name
                    )

                    # Extract CPU and memory usage from metrics
                    cpu_usage = metrics["containers"][0]["usage"]["cpu"]
                    memory_usage = metrics["containers"][0]["usage"]["memory"]

                    # Accumulate total usage
                    cpu_usage_total += int(cpu_usage[:-1])  # Convert string like "1234n" to int (removing "n" suffix)
                    memory_usage_total += int(memory_usage[:-2])  # Convert string like "1234Ki" to int (removing "Ki" suffix)
                except ApiException as e:
                    pass
                except ValueError as value_error:
                    pass

            # Calculate average usage across all pods
            num_pods = len(pods)
            avg_cpu_usage = cpu_usage_total / num_pods if num_pods > 0 else 0
            avg_memory_usage = memory_usage_total / num_pods if num_pods > 0 else 0

            # Get resource usage
            usage = {
                "num_pods": num_pods,
                "avg_cpu_usage (m)": avg_cpu_usage/1e6,
                "avg_memory_usage (Mi)": avg_memory_usage/(1024*1024)
            }

            # Get exposed URL (if service is exposed)
            service_name = f"{deployment_name}-svc"
            try:
                service = core_api.read_namespaced_service(name=service_name, namespace=namespace)
                exposed_url = f"{service.spec.cluster_ip}:{service.spec.ports[0].port}"
            except ApiException as e:
                if e.status == 404:
                    exposed_url = "Not exposed"
                else:
                    exposed_url = "service error "

            # Get HPDA (HorizontalPodAutoscaler) if exists
            hpa_name = f"{deployment_name}-hpa"
            try:
                hpa = scale_api.read_namespaced_horizontal_pod_autoscaler(name=hpa_name, namespace=namespace)
                min_replicas = hpa.spec.min_replicas
                max_replicas = hpa.spec.max_replicas
                cpu_target_percentage = next(m.resource.target.average_utilization for m in hpa.spec.metrics if m.type == "Resource" and m.resource.name == "cpu")
                memory_target_percentage = next((m.resource.target.average_utilization for m in hpa.spec.metrics if m.type == "Resource" and m.resource.name == "memory"), 0)
                #hpa_info = f"Min Replicas: {min_replicas}, Max Replicas: {max_replicas}, CPU Target: {cpu_target_percentage}%, Memory Target: {memory_target_percentage}%"
                hpa_info = {
                        "min replicas":min_replicas,
                        "max replicas": max_replicas,
                        "cpu target %":cpu_target_percentage,
                        "mem target %":memory_target_percentage
                        }
            except ApiException as e:
                if e.status == 404:
                    hpa_info = "No HPA found"
                else:
                    hpa_info = "HPA Error"

            # Get replica sets
            replica_sets = apps_api.list_namespaced_replica_set(namespace=deployment.metadata.namespace).items

            # Print deployment info
            print("{:<30} {:<15} {:<15} {:<20} {:<20} {:<20}".format(
                deployment_name, replicas, json.dumps(limits), json.dumps(usage), exposed_url, json.dumps(hpa_info)))

    except Exception as e:
        print(f"Error occurred while getting deployment info: {e}")


def build_and_push_image():
    """
    Build the Docker image and push it to Docker Hub.
    """
    function_name = input("Enter the name of the docker directory: ")
    version_tag = input("Enter the version tag of image: ")
    # Change directory to function directory
    os.chdir(function_name)
    
    try:
        # Build Docker image
        subprocess.run(["docker", "build", "-t", f"{docker_username}/{function_name}:{version_tag}", "."], check=True)
        
        # Push Docker image to Docker Hub
        subprocess.run(["docker", "push", f"{docker_username}/{function_name}:{version_tag}"], check=True)
    except subprocess.CalledProcessError as e:
        print("Error occurred during Docker image build or push:")
        print(e)
        
    # Change back to original directory
    os.chdir("..")

def get_deployment_logs():
    deployment_name = input("Enter the deployment name to get logs: ")
    namespace="default"
    try:
        # Get logs for deployment pods
        pod_list = core_api.list_namespaced_pod(namespace=namespace, label_selector=f"function={deployment_name}")
        for pod in pod_list.items:
            pod_name = pod.metadata.name
            container_list = pod.spec.containers
            for container in container_list:
                container_name = container.name
                print(f"Logs for pod '{pod_name}', container '{container_name}':")
                logs = core_api.read_namespaced_pod_log(name=pod_name, namespace=namespace, container=container_name)
                print(logs)
                print("="*50)

    except Exception as e:
        print(f"Error occurred while getting logs for deployment '{deployment_name}': {e}")

def delete_deployment(deployment_name, namespace):
    try:
        # Delete deployment
        apps_api.delete_namespaced_deployment(name=deployment_name, namespace=namespace)

        print(f"Deployment '{deployment_name}' deleted successfully.")

    except Exception as e:
        print(f"Error occurred while deleting deployment '{deployment_name}': {e}")

def delete_resources_by_label():
    deployment_name = input("Enter the deployment name to delete: ")
    label_selector = f"function={deployment_name}"
    namespace="default"
    try:

        # Delete deployments
        deployments = apps_api.list_namespaced_deployment(namespace=namespace, label_selector=label_selector).items
        for deployment in deployments:
            apps_api.delete_namespaced_deployment(name=deployment.metadata.name, namespace=namespace, body=client.V1DeleteOptions())
            print(f"Deployment '{deployment.metadata.name}' deleted successfully.")

        # Delete service
        services = core_api.list_namespaced_service(namespace=namespace, label_selector=label_selector).items
        for service in services:
            core_api.delete_namespaced_service(name=service.metadata.name, namespace=namespace, body=client.V1DeleteOptions())
            print(f"Service '{service.metadata.name}' deleted successfully.")

        # Delete HorizontalPodAutoscaler (HPA)
        hpas = scale_api.list_namespaced_horizontal_pod_autoscaler(namespace=namespace, label_selector=label_selector).items
        for hpa in hpas:
            scale_api.delete_namespaced_horizontal_pod_autoscaler(name=hpa.metadata.name, namespace=namespace, body=client.V1DeleteOptions())
            print(f"HorizontalPodAutoscaler '{hpa.metadata.name}' deleted successfully.")

        delete_deployment(deployment_name, namespace)
        print("All resources deleted successfully.")

    except Exception as e:
        print(f"Error occurred while deleting resources: {e}")

def describe_pods_events(deployment_name, namespace="default"):
    try:
        # Get pods associated with the deployment
        pods = core_api.list_namespaced_pod(namespace=namespace, label_selector=f"function={deployment_name}").items
        # Describe events for each pod
        for pod in pods:
            print(f"Name: {pod.metadata.name}")
            print(f"Namespace: {pod.metadata.namespace}")
            print(f"Status: {pod.status.phase}")
            print("Pod IP:", pod.status.pod_ip)
            print("Node Name:", pod.spec.node_name)
            print("Containers:")
            for container in pod.spec.containers:
                print(f"  - Name: {container.name}")
                print(f"    Image: {container.image}")
                print(f"    Image Pull Policy: {container.image_pull_policy}")
                print("    Resources:")
                if container.resources:
                    print(f"      Requests: {container.resources.requests}")
                    print(f"      Limits: {container.resources.limits}")
                else:
                    print("      Not specified")
                print("-----container----")
            print("Events:")
            events = core_api.list_namespaced_event(namespace=pod.metadata.namespace, field_selector=f"involvedObject.name={pod.metadata.name}").items
            if events:
                for event in events:
                    print(f"  - {event.metadata.creation_timestamp}: {event.message}")
            else:
                print("  No events found")

            print("------------------")
    except Exception as e:
        print("Error describing pods and events:", e)

def get_hpa1():
    deployment_name = input("Enter the deployment name to delete: ")
    namespace="default"
    try:
        # Get HPA
        hpa = scale_api.read_namespaced_horizontal_pod_autoscaler(name=deployment_name+"-hpa", namespace=namespace)
        print("Name: %s, Min replicas: %d, Max replicas: %d" % (hpa.metadata.name, hpa.spec.min_replicas, hpa.spec.max_replicas))
        for metric in hpa.spec.metrics:
            if metric.type == "Resource":
                print("Resource metric: %s, Target average utilization: %d%%" % (metric.resource.name, metric.resource.target.average_utilization))
            # Add handling for other metric types if needed

    except Exception as e:
        print("Exception when describing HPA: %s" % str(e))

def get_hpa():
    deployment_name = input("Enter the deployment name to delete: ")
    namespace="default"
    label_selector = f"involvedObject.name={deployment_name}-hpa"
    try:
        # Get events related to the HPA
        events = core_api.list_namespaced_event(namespace=namespace, label_selector=label_selector)

        # Print events
        for event in events.items:
            print(f"Name: {event.metadata.name}")
            print(f"Message: {event.message}")
            print(f"Reason: {event.reason}")
            print(f"Last Timestamp: {event.last_timestamp}")
            print("----")

    except Exception as e:
        print("Exception when listing events: %s" % str(e))

def select_misc_operation():
    print("Select the miscellaneous operation:")
    print("1. Get Cluster IP")
    print("2. Show Additional Pods Information")
    print("3. Show HPA info ")
    print("4. Exit")

    while True:
        try:
            choice = int(input("Enter your choice (1-4): "))
            if 1 <= choice <= 4:
                return choice
            else:
                print(choice)
                print("Invalid choice. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def misc_info():
    while True:
        choice = select_misc_operation()

        if choice == 1:
            print("Get Cluster IP...")
            function_name = input("Enter the function name: ")
            namespace="default"
            # Call function to build Docker
            print("Cluster IP address for use : %s\n" % get_cluster_ip(function_name, namespace))
        elif choice == 2:
            print("Additional Information of Pods ...")
            function_name = input("Enter the function name: ")
            namespace="default"
            # Call function to deploy function
            describe_pods_events(function_name, namespace)
        elif choice == 3:
            print("HPA informatio...")
            get_hpa()
        elif choice == 4:
            print("Exiting...")
            break

def select_operation():
    print("Select an operation:")
    print("1. Build Docker")
    print("2. Deploy Function")
    print("3. Update Deployment")
    print("4. Delete deployment/label")
    print("5. Scale Deployment")
    print("6. Expose Service")
    print("7. Get Function Logs")
    print("8. Get resource usage")
    print("9. Manual Scaling ")
    print("10. Misc functions")
    print("11. Exit")

    while True:
        try:
            choice = int(input("Enter your choice (1-11): "))
            if 1 <= choice <= 11:
                return choice
            else:
                print(choice)
                print("Invalid choice. Please enter a number between 1 and 11.")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    while True:
        choice = select_operation()

        if choice == 1:
            print("Building Docker...")
            # Call function to build Docker
            build_and_push_image()
        elif choice == 2:
            print("Deploying Function...")
            # Call function to deploy function
            create_deployment()
        elif choice == 3:
            print("Updating Deployment...")
            # Call function to update deployment
            update_deployment()
        elif choice == 4:
            print("Rolling back Deployment...")
            # Call function to rollback deployment
            delete_resources_by_label()
        elif choice == 5:
            print("Scaling Deployment...")
            # Call function to scale deployment
            scale_deployment()
        elif choice == 6:
            print("Exposing Service...")
            # Call function to expose service
            expose_service()
        elif choice == 7:
            print("Function logs ...")
            # Call function to expose service
            get_deployment_logs()
        elif choice == 8:
            print("Resource Information ...")
            # Call function to expose service
            get_deployment_info()
        elif choice == 9:
            print("Resource Information ...")
            # Call function to expose service
            manual_scale()
        elif choice == 10:
            print("Resource Information ...")
            # Call function to expose service
            misc_info()
        elif choice == 11:
            print("Exiting...")
            break
