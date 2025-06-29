#!/usr/bin/env python3
"""
Simple test to check imports step by step
"""

try:
    print("Testing basic imports...")
    import os
    import sqlite3
    print("✅ Basic imports successful")
    
    print("Testing matplotlib...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    print("✅ Matplotlib import successful")
    
    print("Testing Flask...")
    from flask import Flask
    print("✅ Flask import successful")
    
    print("Testing other libraries...")
    import pandas as pd
    import numpy as np
    print("✅ Pandas and numpy import successful")
    
    print("Testing face_recognition...")
    import face_recognition
    print("✅ Face recognition import successful")
    
    print("Testing cv2...")
    import cv2
    print("✅ OpenCV import successful")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
