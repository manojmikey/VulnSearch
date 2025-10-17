import subprocess
import time

# Test with a known good domain
test_domain = "uber.com"
print(f"🧪 Testing with domain: {test_domain}")

test_command = f"subfinder -d {test_domain} -silent -all"
result = subprocess.run(test_command.split(), capture_output=True, text=True, timeout=60)

print(f"Return code: {result.returncode}")
print(f"Stdout length: {len(result.stdout)}")
print(f"Stderr: {result.stderr}")
print("First few lines of output:")
for i, line in enumerate(result.stdout.split('\n')[:5]):
    if line.strip():
        print(f"  {i+1}. {line}")