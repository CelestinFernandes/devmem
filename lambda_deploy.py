import subprocess
import os
import shutil
import sys

print("🚀 Building Lambda deployment package...")

# Use the current Python interpreter
python = sys.executable

# Clean previous builds
if os.path.exists("deployment_package"):
    shutil.rmtree("deployment_package")
if os.path.exists("lambda_package.zip"):
    os.remove("lambda_package.zip")

# Create deployment folder
os.makedirs("deployment_package", exist_ok=True)

# Install dependencies into deployment_package
print("📦 Installing dependencies...")
subprocess.run([
    python, "-m", "pip", "install", "-t", "deployment_package",
    "fastapi", "uvicorn", "mangum", "sentence-transformers",
    "transformers", "torch", "psycopg2-binary", "boto3", "python-dotenv"
], check=True)

# Copy application code
# Copy application code (skip missing folders)
print("📁 Copying application code...")
folders_to_copy = ["api", "services", "repositories", "prompts", "frontend"]
for folder in folders_to_copy:
    if os.path.exists(folder):
        shutil.copytree(folder, f"deployment_package/{folder}", dirs_exist_ok=True)
    else:
        print(f"⚠️  Folder '{folder}' not found, skipping.")

# Copy individual files
files_to_copy = ["main.py", "mock_extraction.py"]
for file in files_to_copy:
    if os.path.exists(file):
        shutil.copy(file, "deployment_package/")
    else:
        print(f"⚠️  File '{file}' not found, skipping.")
print("📁 Copying application code...")


# Copy .env (secrets)
if os.path.exists(".env"):
    shutil.copy(".env", "deployment_package/.env")
else:
    print("⚠️  .env file not found – Lambda will need environment variables set manually.")

# Create ZIP
print("📦 Creating ZIP package...")
shutil.make_archive("lambda_package", "zip", "deployment_package")

print("✅ Lambda package created: lambda_package.zip")
print(f"📊 Size: {os.path.getsize('lambda_package.zip') / (1024*1024):.2f} MB")