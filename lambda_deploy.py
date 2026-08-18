import subprocess
import os
import shutil
import sys

print(" Building Lambda deployment package (lightweight) ...")

python = sys.executable

# Clean
if os.path.exists("deployment_package"):
    shutil.rmtree("deployment_package")
if os.path.exists("lambda_package.zip"):
    os.remove("lambda_package.zip")

os.makedirs("deployment_package", exist_ok=True)

# Install lightweight dependencies
print(" Installing dependencies...")
#windows
# subprocess.run([
#     python, "-m", "pip", "install", "-t", "deployment_package",
#     "fastapi", "uvicorn", "mangum", "psycopg2-binary", "requests", "python-dotenv", "numpy"
# ], check=True)

subprocess.run([
    python, "-m", "pip", "install",
    "--platform", "manylinux2014_x86_64",
    "--python-version", "3.12",
    "--only-binary=:all:",
    "-t", "deployment_package",
    "fastapi", "uvicorn", "mangum", "psycopg2-binary",
    "requests", "python-dotenv", "numpy"
], check=True)

# Copy code
print(" Copying application code...")
for folder in ["api", "services", "repositories", "prompts", "frontend"]:
    if os.path.exists(folder):
        shutil.copytree(folder, f"deployment_package/{folder}", dirs_exist_ok=True)
    else:
        print(f"  Folder '{folder}' not found, skipping.")

for file in ["main.py", "mock_extraction.py"]:
    if os.path.exists(file):
        shutil.copy(file, "deployment_package/")
    else:
        print(f"  File '{file}' not found, skipping.")

if os.path.exists(".env"):
    shutil.copy(".env", "deployment_package/.env")

# Create ZIP
print("Creating ZIP package...")
shutil.make_archive("lambda_package", "zip", "deployment_package")

print(f"Lambda package created: lambda_package.zip")
print(f"Size: {os.path.getsize('lambda_package.zip') / (1024*1024):.2f} MB")