import socket
import psutil
import time

def get_system_metrics():
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    temperature = 50  # Mock temperature since not all systems provide this data
    gpu = 0  # Mock GPU utilization as psutil does not directly support it
    return {"CPU": cpu, "Memory": memory, "GPU": gpu, "Temperature": temperature}

def start_client(client_name, server_ip):
    while True:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((server_ip, 8080))
            while True:
                metrics = get_system_metrics()
                conn.sendall(str(metrics).encode('utf-8'))
                time.sleep(5)
        except Exception as e:
            print(f"{client_name} failed to connect, retrying...")
            time.sleep(5)

if __name__ == '__main__':
    start_client("Client A", "192.168.192.142")