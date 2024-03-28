import os
import subprocess

if __name__ == "__main__":
    for filename in os.listdir("Sample JSON Input Files"):
        output = open("Test Outputs/" + filename + "_output.txt", "w")
        res = subprocess.run(["python3","PyONParser.py", "Sample JSON Input Files/" + filename], capture_output=True)
        output.write(res.stdout.decode())
        output.close()