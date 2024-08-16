import matplotlib.pyplot as plt

# Given values
cpu_utilization = [10, 30, 40, 50, 60, 80, 90, 100]
avg_cpu_utilization = [0.20,
18.23,
23.60,
29.51,
33.68,
29.66,
32.20,
22.98,
]
num_of_pods = [1, 1, 2, 2, 2, 3, 3, 5]

# Plotting
plt.figure(figsize=(10, 6))

# CPU Utilization on x-axis
plt.plot(cpu_utilization, avg_cpu_utilization, label='Avg CPU Utilization', marker='o')

# Number of Pods
plt.plot(cpu_utilization, num_of_pods, label='Number of Pods', marker='o')

plt.title('Average CPU Utilization and Number of Pods vs. CPU Utilization')
plt.xlabel('CPU Utilization Limit(%)')
plt.ylabel('Average CPU Utilization(%)')
plt.legend()
plt.grid(True)
plt.text(100, 5, 'minReplicas: 1\nmaxReplicas: 5\nMax CPU utilization: 40%', bbox=dict(facecolor='lightblue', alpha=0.5))
for cpu, avg_cpu, pods in zip(cpu_utilization, avg_cpu_utilization, num_of_pods):
   
        plt.text(cpu, avg_cpu, f'{avg_cpu}', ha='right', va='bottom')
        plt.text(cpu, pods, f'{pods}', ha='right', va='bottom')

plt.tight_layout()
plt.show()
