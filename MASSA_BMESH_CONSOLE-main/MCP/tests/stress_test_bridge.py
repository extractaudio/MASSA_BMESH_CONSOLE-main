import socket
import json
import threading
import time
import random
import string
import sys

HOST = '127.0.0.1'
PORT = 5555
TOTAL_SEQUENTIAL = 100
CONCURRENT_THREADS = 20
REQUESTS_PER_THREAD = 10

import struct

def send_request(payload_data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(30.0)
            s.connect((HOST, PORT))
            
            # Prepare Payload
            if isinstance(payload_data, dict):
                msg_bytes = json.dumps(payload_data).encode('utf-8')
            else:
                msg_bytes = payload_data.encode('utf-8') if isinstance(payload_data, str) else payload_data
            
            # Send Length + Payload
            s.sendall(struct.pack('>I', len(msg_bytes)) + msg_bytes)
            
            # Read Response Length
            raw_len = recv_all(s, 4)
            if not raw_len: return {"status": "error", "msg": "Empty response"}
            
            msg_len = struct.unpack('>I', raw_len)[0]
            
            # Read Response
            data = recv_all(s, msg_len)
            return json.loads(data.decode('utf-8'))
            
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def recv_all(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet: return None
        data += packet
    return data

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def test_connection():
    print_header("TEST 1: Basic Connection")
    start = time.time()
    res = send_request({"skill": "get_materials", "params": {}})
    duration = time.time() - start
    
    if "materials" in res or "status" in res:
        print(f"[PASS] Connected in {duration:.4f}s")
        print(f"Response: {res}")
        return True
    else:
        print(f"[FAIL] Invalid response: {res}")
        return False

def test_sequential_flood():
    print_header(f"TEST 2: Sequential Flood ({TOTAL_SEQUENTIAL} Requests)")
    start = time.time()
    errors = 0
    
    for i in range(TOTAL_SEQUENTIAL):
        # Using get_materials as a lightweight 'ping'
        res = send_request({"skill": "get_materials"})
        if "materials" not in res and res.get("status") != "success":
            errors += 1
            print(f"Request {i} failed: {res}")
            
    duration = time.time() - start
    rate = TOTAL_SEQUENTIAL / duration
    print(f"Completed in {duration:.4f}s ({rate:.2f} req/s)")
    print(f"Errors: {errors}")

def worker(thread_id, errors_list):
    for i in range(REQUESTS_PER_THREAD):
        res = send_request({"skill": "get_materials"})
        if "materials" not in res and res.get("status") != "success":
            errors_list.append(f"T{thread_id}-R{i}")

def test_concurrent_flood():
    total_reqs = CONCURRENT_THREADS * REQUESTS_PER_THREAD
    print_header(f"TEST 3: Concurrent Flood ({total_reqs} Reqs, {CONCURRENT_THREADS} Threads)")
    
    threads = []
    errors = []
    start = time.time()
    
    for i in range(CONCURRENT_THREADS):
        t = threading.Thread(target=worker, args=(i, errors))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    duration = time.time() - start
    rate = total_reqs / duration
    
    print(f"Completed in {duration:.4f}s ({rate:.2f} req/s)")
    print(f"Errors: {len(errors)}")

def test_large_payload():
    print_header("TEST 4: Large Payload (1MB)")
    # Generate 1MB string
    large_str = "X" * (1024 * 1024)
    
    start = time.time()
    # Sending a valid skill but with a massive ignored param
    res = send_request({
        "skill": "get_materials", 
        "params": {"junk": large_str}
    })
    duration = time.time() - start
    
    if "materials" in res:
        print(f"[PASS] Handled 1MB payload in {duration:.4f}s")
    else:
        print(f"[FAIL] Failed to handle large payload: {res.get('msg')}")

def test_garbage_data():
    print_header("TEST 5: Garbage Data (JSON Parse Error)")
    start = time.time()
    
    # Send raw malformed JSON
    res = send_request("{ 'invalid': json_missing_quotes }")
    duration = time.time() - start
    
    # Expecting the bridge to catch the JSON error and return structured error
    if res.get("status") == "error":
        print(f"[PASS] Bridge caught invalid JSON in {duration:.4f}s")
        print(f"Error Msg: {res.get('msg')}")
    else:
        print(f"[FAIL] Unexpected response to garbage: {res}")

if __name__ == "__main__":
    if not test_connection():
        print("\n[CRITICAL] Cannot connect to Bridge. Is Blender running?")
        sys.exit(1)
        
    test_sequential_flood()
    test_concurrent_flood()
    test_large_payload()
    test_garbage_data()
    
    print("\nDONE.")
