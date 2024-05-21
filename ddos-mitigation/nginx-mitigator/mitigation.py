import asyncio
import socket
from datetime import datetime, timedelta
import os

user_requests = {}
timeout_duration = timedelta(seconds=60)  # Adjust timeout duration as needed

async def handle_request(reader, writer):
    data = await reader.read(4096)
    request_data = data.decode("utf-8")

    client_address = writer.get_extra_info('peername')[0]

    if "GET /" in request_data:
        # Check if this is a GET request
        if client_address in user_requests:
            last_request_time = user_requests[client_address].get(request_data, datetime.min)
            if datetime.now() - last_request_time < timeout_duration:
                response = "HTTP/1.1 429 Too Many Requests\n\n"
                writer.write(response.encode("utf-8"))
                await writer.drain()
                writer.close()
                return
        else:
            user_requests[client_address] = {}

        user_requests[client_address][request_data] = datetime.now()

        if client_address in user_requests:
            user_requests[client_address] += 1
        else:
            user_requests[client_address] = 1

        if user_requests[client_address] > 10:
            response = "HTTP/1.1 429 Too Many Requests\n\n"
        else:
            response = "HTTP/1.1 200 OK\n\nHello, World!\n"
    else:
        response = "HTTP/1.1 400 Bad Request\n\n"

    log_request(client_address, request_data, response)

    writer.write(response.encode("utf-8"))
    await writer.drain()
    writer.close()

def log_request(client_address, request_data, response):
    # Create log directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create or append to the log file for the current date
    log_file_name = datetime.now().strftime('logs/%Y-%m-%d.log')
    with open(log_file_name, 'a') as log_file:
        log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {client_address} - {request_data.strip()} - {response.strip()}\n"
        log_file.write(log_entry)

async def main():
    server = await asyncio.start_server(handle_request, 'localhost', 8080)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server is shutting down...")
