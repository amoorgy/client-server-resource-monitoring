import socket
import threading
import logging
import json
from flask import Flask, render_template, request

# Flask App for Server
app = Flask(__name__)


client_data = {} # client data is empty in the beginning
thresholds = {} # there are no thresholds in the beginning
client_name_map = {} # this is for naming the client from 1 to however many are added
name_counter = 1 

@app.route('/', methods=['GET', 'POST'])
def monitor():
    global thresholds
    try:
        if request.method == 'POST':
            client = request.form['client']
            thresholds[client] = {
                "CPU Utilization": int(request.form.get('cpu', 0)),
                "CPU Temperature": int(request.form.get('cpu_temp', 0)),
                "Memory Utilization": int(request.form.get('memory', 0)),
                "GPU Memory Utilization": int(request.form.get('gpu_memory', 0)),
                "GPU Temperature": int(request.form.get('gpu_temp', 0))
            }
        
        # Convert client data to integers for comparison, handle invalid data
        for client, data in client_data.items():
            for key, value in data.items():
                # Try to convert the value to an integer, set default if it fails
                try:
                    client_data[client][key] = int(value)
                except ValueError:
                    # If the conversion fails, set a default value (e.g., 0 or a suitable number)
                    client_data[client][key] = 0  # You can adjust this default as needed

        # Convert thresholds to integers
        for client, threshold in thresholds.items():
            for key, value in threshold.items():
                thresholds[client][key] = int(value)

        return render_template('index.html', client_data=client_data, thresholds=thresholds)
    except Exception as e:
        logging.error(f"Error processing request in monitor route: {e}")
        return "An error occurred in monitor()."


def server_thread(conn):
    global name_counter
    try:
        # Receive client ID during the first connection
        client_id = conn.recv(1024).decode('utf-8').strip()
        if not client_id:
            logging.error("No client ID received. Closing connection.")
            conn.close()
            return

        # Assign a sequential name if it's a new client
        if client_id not in client_name_map:
            client_name_map[client_id] = f"Client {name_counter}"
            name_counter += 1

        client_name = client_name_map[client_id]
        logging.info(f"Received connection from {client_name} ({client_id})")

        # Initialize client data with default values if it's a new client
        if client_name not in client_data:
            client_data[client_name] = {
                "CPU Utilization": 0.0,
                "CPU Temperature": 0.0,
                "Memory Utilization": 0.0,
                "GPU Memory Utilization": 0.0,
                "GPU Temperature": 0.0
            }
            thresholds[client_name] = {
                "CPU Utilization": 0,
                "CPU Temperature": 0,
                "Memory Utilization": 0,
                "GPU Memory Utilization": 0,
                "GPU Temperature": 0
            }

        conn.send("Here is the link for adjusting thresholds: http://127.0.0.1:5000/".encode('utf-8'))

        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    logging.info(f"{client_name} disconnected.")
                    break

                # Update client data
                client_data[client_name] = json.loads(data)
                logging.info(f"Updated data for {client_name}")
            except Exception as e:
                logging.error(f"Error processing data from {client_name}: {e}")
                break
    except Exception as e:
        logging.error(f"Error in server_thread: {e}")
    finally:
        conn.close()


def check_threshold(client, metric, value):
    """Check if the client's value exceeds the threshold, return color class."""
    threshold = thresholds.get(client, {}).get(metric, 100)  # Default threshold is 100 if not set
    if value > threshold:
        return "high"  # Exceeds threshold, return high class
    else:
        return "normal"  # Within threshold, return normal class

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen(5)
    logging.info("Server listening...")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=server_thread, args=(conn,)).start()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    threading.Thread(target=start_server).start()
    app.run(host='0.0.0.0', port=5000)