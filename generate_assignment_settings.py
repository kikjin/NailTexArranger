import cv2
import numpy as np
import os
import yaml
import sys

MAPPING = 'name_color_mapping.yaml'
OUTPUT_BASE_NAME = 'assignment_settings.yaml'

def main():
    if len(sys.argv) != 2:
        print(f'Usage: python {sys.argv[0]} [user_image_path]')
        sys.exit(1)

    user_image_path = sys.argv[1]
    mask_colors_path = MAPPING

    # Create output file name
    image_name = os.path.splitext(os.path.basename(user_image_path))[0]
    base_name, extension = os.path.splitext(os.path.basename(OUTPUT_BASE_NAME))
    output_settings_path = f'{base_name}_{image_name}{extension}'

    generate_settings(user_image_path, mask_colors_path, output_settings_path)

def hex_to_bgr(hex_code):
    return tuple(reversed([int(hex_code[i:i+2], 16) for i in (1, 3, 5)]))

def generate_settings(user_image_path, mask_colors_path, output_settings_path):
    # Load user-edited image
    user_image = cv2.imread(user_image_path)

    # Load mask colors
    with open(mask_colors_path, 'r') as file:
        mask_colors = yaml.safe_load(file)

    # Get default width and height from user-edited image
    default_width, default_height = user_image.shape[1], user_image.shape[0]

    # Initialize settings dictionary
    settings = {
        'Default_Width': default_width,
        'Default_Height': default_height
    }

    # Loop through mask colors to extract position and scale information
    for keyname, color_code in mask_colors.items():
        # Convert color code to BGR.
        bgr_color = hex_to_bgr(color_code)
        # Find coordinates of pixels with the color code
        coordinates = np.column_stack(np.where(np.all(user_image == bgr_color, axis=-1)))

        if len(coordinates) == 0:
            print(f'Warning: No pixels found for name {keyname}. Skipping.')
            continue

        # Calculate position and scale based on the found coordinates
        y, x = coordinates.min(axis=0)
        h, w = coordinates.max(axis=0) - coordinates.min(axis=0) + 1
        scale_x, scale_y = w / default_width, h / default_height

        # Convert numpy objects to regular Python types
        x, y, scale_x, scale_y = float(x), float(y), float(scale_x), float(scale_y)

        # Add assignment settings to the dictionary
        settings[keyname] = {
            'Scale_X': scale_x,
            'Scale_Y': scale_y,
            'X': x / default_width,
            'Y': y / default_height
        }

    # Write settings to settings.yaml
    with open(output_settings_path, 'w') as file:
        yaml.dump(settings, file)
    print(f'Setting file has generated. Output: {os.path.basename(output_settings_path)}')

if __name__ == "__main__":
    main()