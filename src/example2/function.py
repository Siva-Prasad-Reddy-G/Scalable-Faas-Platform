from flask import Flask, request, jsonify
import ctypes
from prometheus_client import Counter, Gauge, start_http_server
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
import psutil
import time
import subprocess
import multiprocessing


app = Flask(__name__)

# Define Prometheus metrics
function_requests_total = Counter('function_requests_total', 'Total number of requests to the function')
cpu_utilization_gauge = Gauge('cpu_utilization_percentage', 'CPU utilization percentage')
request_rate_gauge = Gauge('function_request_rate', 'Function request rate (requests per second)')
service_time_gauge = Gauge('function_service_time_seconds', 'Service time of the function in seconds')
network_bytes_sent = Counter('network_bytes_sent_total', 'Total number of bytes sent over the network')
network_bytes_recv = Counter('network_bytes_received_total', 'Total number of bytes received over the network')


start_time=time.time()

@app.route("/clear_metrics")
def clear_metrics():
    function_requests_total._value.set(0)
    cpu_utilization_gauge.set(0)
    service_time_gauge.set(0)
    network_bytes_sent._value.set(0)
    network_bytes_recv._value.set(0)
    start_time=time.time()
    registry = CollectorRegistry()
    return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}

cpu_process = None

def occupy_cpu(percentage):
    while True:
        # Get the current CPU usage
        cpu_percent = psutil.cpu_percent()

        # Adjust the workload based on the difference between actual and desired CPU usage
        if cpu_percent > 0.1:
            workload = min(1.0, percentage / cpu_percent)
        else:
            workload = 1.0

        # Start time
        start_time = time.time()

        # Perform CPU-bound task
        while (time.time() - start_time) < (percentage/100):
            pass

        # Sleep to balance CPU usage
        time.sleep(1 - percentage/100)

@app.route('/occupy_cpu/<int:percentage>', methods=['GET'])
def start_cpu_occupier(percentage):
    global cpu_process

    if 0 <= percentage <= 100:
        # Kill previous process if exists
        if cpu_process and cpu_process.is_alive():
            cpu_process.terminate()

        # Create a new process for occupying CPU
        cpu_process = multiprocessing.Process(target=occupy_cpu, args=(percentage,))
        cpu_process.start()
        return jsonify({'message': f'CPU is being occupied at {percentage}%'}), 200
    else:
        return jsonify({'error': 'Invalid percentage, must be between 0 and 100'}), 400

memory_process = None
memory_block = None

def allocate_memory(memory_size):
    try:
        memory_size = int(memory_size) * 1024*1024
    except ValueError:
        return jsonify({'error': 'Invalid memory size'}), 400

    if memory_size <= 0:
        return jsonify({'error': 'Memory size must be greater than 0'}), 400

    # Allocate memory of specified size
    ptr = ctypes.c_char * memory_size
    memory_block = ptr()

    return jsonify({'message': 'Memory allocated successfully'}), 200

@app.route('/allocate_memory/<int:memory_size>', methods=['GET'])
def start_memory_allocator(memory_size):
    global memory_process

    # Kill previous process if exists
    if memory_process and memory_process.is_alive():
        memory_process.terminate()

    # Create a new process for memory allocation
    memory_process = multiprocessing.Process(target=allocate_memory, args=(memory_size,))
    memory_process.start()
    use_allocated_memory()
    return jsonify({'message': f'Memory allocated with size {memory_size}'}), 200

@app.route('/use_memory', methods=['GET'])
def use_allocated_memory():
    global memory_block
    if memory_block is None:
        return jsonify({'error': 'Memory not allocated yet'}), 400

    # Use the allocated memory block
    data = b'Hello, world!' * (len(memory_block) // len(b'Hello, world!'))
    memory_block[0:len(data)] = data

    return jsonify({'message': 'Data written to allocated memory successfully'}), 200

stress_process = None

@app.route('/mem')
def index():
    return 'Memory Usage: ' + get_memory_usage()

def get_memory_usage():
    # Call system command to get memory usage using top
    result = subprocess.run(['top', '-b', '-n', '1'], capture_output=True, text=True)
    return result.stdout

@app.route('/memory/<int:memory_size>', methods=['GET'])
def manage_memory(memory_size):
    global stress_process
    try:
        size = int(memory_size) * 1024*1024
    except ValueError:
        return jsonify({'error': 'Invalid memory size'}), 400

    if size > 0:
        if stress_process:
            # Kill existing stress-ng process
            subprocess.run(['pkill', 'stress-ng'])
            stress_process = None

        # Start stress-ng process with specified size
        stress_process = subprocess.Popen(['stress-ng', '--vm', '1', '--vm-bytes', str(size)])
        return f'Started new stress-ng process with {size}MB memory size.'
    else:
        if stress_process:
            # Kill existing stress-ng process
            subprocess.run(['pkill', 'stress-ng'])
            stress_process = None
        return 'Not running stress-ng.'

@app.route("/")
def hello():
    time_invoked=time.time()

    # Increment request counter
    function_requests_total.inc()

    for i in range(100000):
        for j in range(1000):
            pass

    

    service_time = time.time() - time_invoked

    service_time_gauge.set(service_time)
    
    # Collect CPU utilization
    cpu_utilization = psutil.cpu_percent()
    cpu_utilization_gauge.set(cpu_utilization)


    return "Hello from Python function"

@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()
    # Register your Prometheus metrics collectors here
    # For example:
    # registry.register(...)

    elapsed_time = time.time() - start_time

    registry.register(function_requests_total)
    registry.register(cpu_utilization_gauge)
    registry.register(service_time_gauge)
    registry.register(network_bytes_sent)
    registry.register(network_bytes_recv)
    

    metric=generate_latest(registry)
    for line in metric.decode().split("\n"):
        if "function_requests_total" in line:
            try:
                value = float(line.split()[1])
                request_rate = value/elapsed_time
            except:
                pass
        if "function_requests_total" in line:
            try:
                no_of_requests = float(line.split()[1])
            except:
                pass
        if "cpu_utilization_percentage" in line:
            try:
                cpu_utilization = float(line.split()[1])
            except:
                pass
        if "function_service_time_seconds" in line:
            try:
                service_time= float(line.split()[1])
            except:
                pass

        if "network_bytes_sent_total" in line:
            try:
                bytes_sent= float(line.split()[1])
            except:
                pass
        if "network_bytes_received_total" in line:
            try:
                bytes_received= float(line.split()[1])
            except:
                pass
    request_rate_gauge.set(request_rate)
    registry.register(request_rate_gauge)


    network_stats = psutil.net_io_counters()
    network_bytes_sent.inc(network_stats.bytes_sent)
    network_bytes_recv.inc(network_stats.bytes_recv)

    output = ""
    output += "Number of Requests: " + str(no_of_requests) + "\n"
    output += "Request Rate: " + str(request_rate) + "\n"
    output += "Service Time: " + str(service_time) + "\n"
    output += "CPU Utilization: " + str(cpu_utilization) + "\n"
    output += "Bytes Sent: " + str(bytes_sent) + "\n"
    output += "Bytes Received: " + str(bytes_received) + "\n"
    return output, 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    # Start Prometheus HTTP server to expose metrics
    start_http_server(8000)
    
    # Run Flask app
    app.run(host='0.0.0.0')
