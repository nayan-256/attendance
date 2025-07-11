#!/usr/bin/env python3
"""
Minimal test to check specific imports and see what's hanging
"""

print("Starting import test...")

try:
    print("Testing basic imports...")
    import os
    import sqlite3
    import json
    print("✓ Basic imports successful")
    
    print("Testing Flask import...")
    from flask import Flask
    print("✓ Flask import successful")
    
    print("Testing matplotlib import...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    print("✓ Matplotlib import successful")
    
    print("Testing pandas import...")
    import pandas as pd
    print("✓ Pandas import successful")
    
    print("All imports completed successfully!")
    
except Exception as e:
    print(f"✗ Error during import: {e}")
    import traceback
    traceback.print_exc()
