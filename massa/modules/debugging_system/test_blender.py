import os

def test():
    log_file = os.path.join(os.path.dirname(__file__), "test_blender_log.txt")
    with open(log_file, "w") as f:
        f.write("Hello from Blender!\n")

if __name__ == "__main__":
    test()
