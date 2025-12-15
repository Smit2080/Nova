import os
import sys
import py_compile

workspace = sys.argv[1]

if not workspace:
    print("workspace path required")
    sys.exit(2)

errors = []

# Walk through workspace and compile .py files for syntax checking
for root, dirs, files in os.walk(workspace):
    for f in files:
        if f.endswith(".py"):
            full_path = os.path.join(root, f)
            try:
                py_compile.compile(full_path, doraise=True)
            except Exception as e:
                errors.append(f"{full_path}: {e}")

if errors:
    print("Syntax check failed:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("syntax OK")
sys.exit(0)
