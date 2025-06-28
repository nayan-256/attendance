import sqlite3
import os
import glob

def find_student_image(student_name):
    """
    Smart function to find student image from uploads folder
    Matches student name with uploaded image filenames
    """
    uploads_dir = os.path.join('static', 'uploads')
    
    if not os.path.exists(uploads_dir):
        return 'default_profile.svg'
    
    # Get all image files from uploads folder
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
    image_files = []
    
    for extension in image_extensions:
        image_files.extend(glob.glob(os.path.join(uploads_dir, extension)))
    
    if not image_files:
        return 'default_profile.svg'
    
    # Clean student name for matching
    clean_name = student_name.lower().replace(' ', '_').replace('.', '').strip()
    name_parts = [part.strip() for part in student_name.lower().split() if len(part.strip()) > 1]
    
    # Try different matching strategies
    best_match = None
    max_score = 0
    
    for image_path in image_files:
        image_filename = os.path.basename(image_path).lower()
        score = 0
        
        # Strategy 1: Exact name match
        if clean_name in image_filename:
            score += 15
        
        # Strategy 2: Individual name parts match
        for part in name_parts:
            if len(part) > 2 and part in image_filename:
                score += 5
        
        # Strategy 3: First name + last name combination
        if len(name_parts) >= 2:
            first_last = f"{name_parts[0]}_{name_parts[-1]}"
            if first_last in image_filename:
                score += 12
            
            # Also try without underscore
            first_last_nospace = f"{name_parts[0]}{name_parts[-1]}"
            if first_last_nospace in image_filename:
                score += 10
        
        # Strategy 4: Any name part at the beginning of filename
        for part in name_parts:
            if len(part) > 2 and image_filename.startswith(part):
                score += 8
        
        # Strategy 5: Loose matching for common variations
        if len(name_parts) > 0:
            first_name = name_parts[0]
            if len(first_name) > 3 and first_name in image_filename:
                score += 6
        
        if score > max_score:
            max_score = score
            best_match = image_path
    
    if best_match and max_score > 0:
        # Convert to relative path for web serving
        relative_path = best_match.replace('\\', '/').replace('static/', '')
        return relative_path
    else:
        # Return default profile image if no good match found
        return 'default_profile.svg'

def test_image_matching():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute('SELECT name, student_id, image_path FROM users')
    users = cur.fetchall()
    
    print('Testing Image Matching:')
    print('=' * 50)
    
    for user in users:
        name = user["name"]
        stored_path = user["image_path"]
        
        # Test our find_student_image function
        matched_path = find_student_image(name)
        
        print(f'Student: {name}')
        print(f'  Stored in DB: {stored_path}')
        print(f'  Smart Match: {matched_path}')
        
        # Check if files exist
        if stored_path:
            clean_stored = stored_path.replace('\\', '/').replace('static/', '')
            stored_exists = os.path.exists(os.path.join('static', clean_stored))
            print(f'  DB Image Exists: {stored_exists}')
        
        matched_exists = os.path.exists(os.path.join('static', matched_path))
        print(f'  Matched Image Exists: {matched_exists}')
        print()
    
    conn.close()

if __name__ == "__main__":
    test_image_matching()
