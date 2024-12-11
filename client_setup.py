import socket
import time
import psutil
from pynvml import nvmlInit, nvmlShutdown, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo, nvmlDeviceGetUtilizationRates, nvmlDeviceGetTemperature, NVML_TEMPERATURE_GPU, NVMLError
import json
import uuid

def get_system_metrics():
    try:
        nvmlInit()

        handle = nvmlDeviceGetHandleByIndex(0)
        memory_info = nvmlDeviceGetMemoryInfo(handle)
        gpu_memory_used = memory_info.used / 1024**2
        gpu_memory_total = memory_info.total / 1024**2
        gpu_memory_utilization = (gpu_memory_used / gpu_memory_total) * 100
        gpu_temperature = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)

        cpu_utilization = psutil.cpu_percent(interval=1)

        memory = psutil.virtual_memory()
        memory_used = memory.used / 1024**3
        memory_total = memory.total / 1024**3
        memory_utilization = memory.percent  

        cpu_temp = psutil.sensors_temperatures().get('coretemp', [])[0].current if hasattr(psutil, 'sensors_temperatures') else "Temperature not available"

        nvmlShutdown()
        return {
            "CPU Utilization": cpu_utilization,
            "CPU Temperature": cpu_temp,
            "Memory Utilization": memory_utilization,
            "GPU Memory Utilization": gpu_memory_utilization,
            "GPU Temperature": gpu_temperature
        }

    except NVMLError as error:
        return {"Error": f"Failed to get GPU metrics: {error}"}
    except Exception as error:
        return {"Error": f"An error occurred: {error}"}

def wait_for_server_confirmation(host, port, client_name):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)
        client_socket.connect((host, port))
        print("Connected to server, waiting for confirmation...")

        start_time = time.time()
        while True:
            try:
                message = client_socket.recv(1024)
                if message:
                    phrase = message.decode('utf-8')
                    print(f"Received from server: {phrase}")
                    return True
            except socket.timeout:
                print("No response from server within 10 seconds. Closing connection.")
                client_socket.close()
                time.sleep(1)
            if time.time() - start_time > 10:
                print("No response from server within 10 seconds. Closing connection.")
                client_socket.close()
                return False

    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def start_client(server_ip):
    client_id = str(uuid.uuid4())  # Generate a unique client ID
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    max_attempts = 5
    attempts = 1
    connected = False

    while not connected and attempts <= max_attempts:
        try:
            client_socket.connect((server_ip, 8080))
            connected = True

            # Send the client ID immediately upon connection
            client_socket.sendall(client_id.encode('utf-8'))
            print(f"Client ID {client_id} sent to server.")
            
            confirmation = client_socket.recv(1024).decode('utf-8')
            print(f"Server response: {confirmation}")

            if confirmation != None:
                data = get_system_metrics()
                client_socket.sendall(json.dumps(data).encode('utf-8'))
                print(f"{client_id} has sent data.")
            else:
                print("Failed to establish connection.")
        except Exception as e:
            print(f"Attempt {attempts}: Error connecting to server: {e}")
            time.sleep(5)
            attempts += 1

    if not connected:
        print("Failed to connect to the server after multiple attempts. Exiting.")
        exit()
    client_socket.close()


if __name__ == '__main__':
    start_client("127.0.0.1")