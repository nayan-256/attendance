# Temporary file to check main.py structure
import os
import sys

# Add the project directory to Python path
project_dir = r"c:\Users\Lenovo\Desktop\gcoej all subjects\TY folder\Sem 6\Miniproject\attendance"
sys.path.append(project_dir)

# Read main.py to understand current structure
with open(os.path.join(project_dir, "main.py"), "r") as f:
    content = f.read()

# Look for database models and routes
print("=== DATABASE MODELS ===")
if "class" in content:
    lines = content.split('\n')
    in_class = False
    for line in lines:
        if line.strip().startswith('class '):
            print(line.strip())
            in_class = True
        elif in_class and (line.strip().startswith('def ') or line.strip().startswith('class ') or line.strip() == ''):
            if line.strip().startswith('class '):
                print(line.strip())
            elif line.strip() == '':
                in_class = False

print("\n=== ROUTES ===")
for line in content.split('\n'):
    if '@app.route' in line or 'def ' in line:
        print(line.strip())
