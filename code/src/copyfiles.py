import os
import shutil

# Define the root directory and destination folder
root_dir = "generated_emails"  # Change this to your root directory path
destination_folder = "resources"  # Change this to your target folder

# Ensure the destination folder exists
os.makedirs(destination_folder, exist_ok=True)

# Walk through the directory structure and copy .eml files
for dirpath, _, filenames in os.walk(root_dir):
    for file in filenames:
        if file.endswith(".eml"):
            source_path = os.path.join(dirpath, file)
            destination_path = os.path.join(destination_folder, file)

            # Avoid overwriting files with the same name
            counter = 1
            while os.path.exists(destination_path):
                base, ext = os.path.splitext(file)
                destination_path = os.path.join(destination_folder, f"{base}_{counter}{ext}")
                counter += 1
            
            shutil.copy2(source_path, destination_path)
            print(f"Copied: {source_path} -> {destination_path}")

print("All .eml files have been copied successfully!")
