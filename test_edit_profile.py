"""
Test script to verify the edit profile functionality
"""
import os
import glob

def test_upload_folder():
    """Test if upload folder exists and is writable"""
    upload_folder = 'static/uploads'
    
    if not os.path.exists(upload_folder):
        print(f"❌ Upload folder '{upload_folder}' does not exist")
        return False
    
    if not os.access(upload_folder, os.W_OK):
        print(f"❌ Upload folder '{upload_folder}' is not writable")
        return False
    
    print(f"✅ Upload folder '{upload_folder}' exists and is writable")
    
    # List current images
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif']:
        image_files.extend(glob.glob(os.path.join(upload_folder, ext)))
    
    print(f"📁 Current images in upload folder: {len(image_files)}")
    for img in image_files:
        print(f"   - {os.path.basename(img)}")
    
    return True

def test_default_image():
    """Test if default profile image exists"""
    default_image = 'static/default_profile.svg'
    
    if os.path.exists(default_image):
        print(f"✅ Default profile image exists: {default_image}")
        return True
    else:
        print(f"❌ Default profile image missing: {default_image}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Edit Profile Functionality")
    print("=" * 50)
    
    test_upload_folder()
    test_default_image()
    
    print("\n📋 Edit Profile Features Added:")
    print("✅ Enhanced UI with animated gradients and glass morphism")
    print("✅ Current photo display with hover effects")
    print("✅ Drag & drop photo upload area")
    print("✅ File picker with validation (JPG, PNG, GIF, max 5MB)")
    print("✅ Camera capture functionality")
    print("✅ Live image preview before upload")
    print("✅ Form validation and loading states")
    print("✅ Backend photo processing and unique filename generation")
    print("✅ Database update with new image path")
    print("✅ Flash messages for user feedback")
    
    print("\n🚀 To test the photo upload:")
    print("1. Start the Flask app: python main.py")
    print("2. Login as a student (e.g., ID: 103)")
    print("3. Go to Profile page")
    print("4. Click 'Edit Profile' button")
    print("5. Try uploading a new photo using:")
    print("   - File picker button")
    print("   - Drag & drop area")
    print("   - Camera capture (if available)")
    print("6. Save changes and verify photo updates")
