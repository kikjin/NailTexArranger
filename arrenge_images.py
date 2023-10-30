import cv2
import numpy as np
import os
import yaml
import re
import sys

OUTPUT_FOLDER = 'out'

def main():
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} [output settings file] [cropped image folder] [composite image (optional)]")
        return

    settings_path = sys.argv[1]

    cropped_img_folder = sys.argv[2]

    default_width, default_height = load_default_image_size(settings_path)

    composite_image_path = sys.argv[3] if len(sys.argv) > 3 else None

    if composite_image_path is not None:
        composite_image = cv2.imread(composite_image_path, cv2.IMREAD_UNCHANGED)
        # Use composite image size for output if specified
        output_width, output_height = composite_image.shape[1], composite_image.shape[0]
    else:
        # Use default size for output
        output_width, output_height = default_width, default_height

    output_image = np.zeros((output_height, output_width, 4), dtype=np.uint8)

    settings = load_settings(settings_path)

    # Loop to process images in the cropped_img_folder
    for mask_file, parameters in settings.items():
        # Create a pattern for the target file name
        pattern = f'.*_{mask_file}.png$'

        # Search for files matching the pattern
        matched_files = [f for f in os.listdir(cropped_img_folder) if re.match(pattern, f)]

        if not matched_files:
            print(f'Warning: No file found for {mask_file}. Skipping.')
            continue

        if len(matched_files) > 1:
            print(f'Warning: Multiple files found for {mask_file}. Using the first matched file: {matched_files[0]}.')

        # Select the first matched file
        matched_file = os.path.join(cropped_img_folder, matched_files[0])

        # Debug
        #print(parameters)

        # Read and resize the matched file
        scale_x = parameters.get('Scale_X', None)
        scale_y = parameters.get('Scale_Y', None)
        x = parameters.get('X', None)
        y = parameters.get('Y', None)
        alpha = parameters.get('Alpha', None)

        # Test
        #print(scale_x, scale_y, x, y, alpha)

        matched_image = cv2.imread(matched_file, cv2.IMREAD_UNCHANGED)
        h2, w2 = matched_image.shape[:2]
        h1, w1 = output_image.shape[:2]

        #print(output_image.shape)
        #print(matched_image.shape)

        if scale_x is None and scale_y is None:
            print(f'Warning: Both Scale_X and Scale_Y are not specified for {mask_file}. Skipping.')
            continue

        if scale_x is None:
            scale_x = scale_y * (w2 / h2)

        if scale_y is None:
            scale_y = scale_x / (w2 / h2)

        # Resize using Scale_X and Scale_Y
        composite_resized = cv2.resize(matched_image, None, fx=(w1 * scale_x) / w2, fy=(h1 * scale_y) / h2)
        #print(composite_resized.shape)

        # Get the size after resizing
        h2r, w2r = composite_resized.shape[:2]

        # Place image 2 at the specified position in image 1
        x_offset = int(w1 * x)
        y_offset = int(h1 * y)

        #print(f'x_offset: {x_offset}, y_offset: {y_offset}')

        for i in range(h2r):
            for j in range(w2r):
                if (
                    0 <= y_offset + i < h1 and
                    0 <= x_offset + j < w1 and
                    composite_resized[i, j, 3] != 0
                ):
                    output_image[y_offset + i, x_offset + j, :] = composite_resized[i, j, :]


    # Create output destination folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Save the composite result
    output_basename = cropped_img_folder.replace('cropped_','')
    output_path = os.path.join(OUTPUT_FOLDER, f'{output_basename}_arrenged.png')
    cv2.imwrite(output_path, output_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

    # Overlay output_image on composite_image
    # Assuming output_image and composite_image have an alpha channel
    if composite_image_path is not None:
        for i in range(h1):
            for j in range(w1):
                if output_image[i, j, 3] > 0:  # Check if the pixel in output_image is not fully transparent
                    composite_image[i, j, :] = output_image[i, j, :]

        # Save the combined image
        combined_path = os.path.join(OUTPUT_FOLDER, f'{os.path.splitext(os.path.basename(composite_image_path))[0]}_combined.png')
        cv2.imwrite(combined_path, composite_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        print(f'Combining complete. Output file: {os.path.basename(output_path)}, {os.path.basename(combined_path)} in \'{OUTPUT_FOLDER}\' folder.')
    else:
        print(f'Combining complete. Output file: {os.path.basename(output_path)} in \'{OUTPUT_FOLDER}\' folder.')

# Read the default image size from the settings file
def load_default_image_size(file_path):
    with open(file_path, 'r') as file:
        settings = yaml.safe_load(file)
    default_width = settings.get('Default_Width', 2048)
    default_height = settings.get('Default_Height', 2048)
    return default_width, default_height

# Read scale and position settings from the file
def load_settings(file_path):
    with open(file_path, 'r') as file:
        settings = yaml.safe_load(file)

    default_width = settings.pop('Default_Width', None)
    default_height = settings.pop('Default_Height', None)

    for finger, parameters in settings.items():
        if parameters is not None:
            if 'Scale_X' in parameters:
                parameters['Scale_X'] = float(parameters['Scale_X'])
            if 'Scale_Y' in parameters and parameters['Scale_Y'] is not None:
                parameters['Scale_Y'] = float(parameters['Scale_Y'])
            if 'X' in parameters and parameters['X'] is not None:
                parameters['X'] = float(parameters['X'])
            if 'Y' in parameters and parameters['Y'] is not None:
                parameters['Y'] = float(parameters['Y'])
            if 'Alpha' in parameters and parameters['Alpha'] is not None:
                parameters['Alpha'] = float(parameters['Alpha'])

    return settings

if __name__ == "__main__":
    main()
