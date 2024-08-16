import matplotlib.pyplot as plt

# Given values
cpu_utilization = [0, 10, 30, 40, 50, 60, 80, 90, 100]
service_time = [1.36,
1.26,
1.30,
1.32,
1.35,
1.40,
1.35,
1.37,
1.35,
]
num_of_pods = [1, 2, 5, 5, 5, 5, 5, 5, 5]

# Plotting
plt.figure(figsize=(10, 6))

# CPU Utilization on x-axis
plt.plot(cpu_utilization, service_time, label='Service Time(s)', marker='o')

# Number of Pods
plt.plot(cpu_utilization, num_of_pods, label='Number of Pods', marker='o')

plt.title('Service Time and Number of Pods vs. CPU Utilization')
plt.xlabel('CPU Utilization Limit(%)')
plt.ylabel('Service Time(s)')
plt.legend()
plt.grid(True)
plt.text(100, 5, 'minReplicas: 1\nmaxReplicas: 5\nMax CPU utilization: 40%', bbox=dict(facecolor='lightblue', alpha=0.5))
for cpu, avg_cpu, pods in zip(cpu_utilization, service_time, num_of_pods):
   
        plt.text(cpu, avg_cpu, f'{avg_cpu}', ha='right', va='bottom')
        plt.text(cpu, pods, f'{pods}', ha='right', va='bottom')

plt.tight_layout()
plt.show()
