import os
from PIL import Image
import numpy as np

# Directory containing the BMP images
input_directory = 'dataset'

# Get the current directory where the code is located
output_directory = 'dataset'

try:
    # Loop through each BMP file in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith('.BMP'):
            # Open the BMP image using PIL
            image_path = os.path.join(input_directory, filename)
            image = Image.open(image_path)
            
            # Convert the image to a NumPy array
            image_array = np.array(image)
            
            # Save the NumPy array as a .npy file in the current directory
            npy_filename = os.path.splitext(filename)[0] + '.npy'
            npy_filepath = os.path.join(output_directory, npy_filename)
            np.save(npy_filepath, image_array)
    print("Conversion and saving completed successfully.")
except Exception as e:
    print(f"An error occurred: {e}")
