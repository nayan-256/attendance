#!/usr/bin/env python3
"""
Quick test to identify the exact issue by importing step by step
"""

import sys
import os

# Change to the correct directory
os.chdir(r"c:\Users\Lenovo\Desktop\gcoej all subjects\TY folder\Sem 6\Miniproject\attendance")

print("Testing imports one by one...")

try:
    print("1. Testing os, sqlite3...")
    import sqlite3
    print("✅ sqlite3 OK")

    print("2. Testing matplotlib...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    print("✅ matplotlib OK")

    print("3. Testing numpy, pandas...")
    import numpy as np
    import pandas as pd
    print("✅ numpy, pandas OK")

    print("4. Testing Flask...")
    from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
    print("✅ Flask OK")

    print("5. Testing datetime, collections...")
    from datetime import datetime, timedelta
    from collections import defaultdict
    print("✅ datetime, collections OK")

    print("6. Testing io, base64...")
    import io
    import base64
    print("✅ io, base64 OK")

    print("7. Testing face_recognition (this might hang)...")
    try:
        import face_recognition
        print("✅ face_recognition OK")
    except Exception as e:
        print(f"❌ face_recognition failed: {e}")

    print("8. Testing cv2...")
    try:
        import cv2
        print("✅ cv2 OK")
    except Exception as e:
        print(f"❌ cv2 failed: {e}")

    print("\n✅ All tests completed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
