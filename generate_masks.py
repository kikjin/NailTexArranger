import cv2
import os
import sys
import yaml

# Define the constant for the folder and file name
#MASK_FOLDER = 'masks'
COLOR_YAML = 'name_color_mapping.yaml'

def main():
    if len(sys.argv) != 2:
        print(f'Usage: python {sys.argv[0]} [mask image path]')
        return
    
    # Get the path of the mask image from the arguments
    mask_image_path = sys.argv[1]
    mask_image_name = os.path.splitext(os.path.basename(mask_image_path))[0]

    # Read the YAML file
    with open(COLOR_YAML, 'r') as file:
        color_mapping = yaml.safe_load(file)

    # Create 'masks' folder if it doesn't exist
    mask_folder = f'masks_{mask_image_name}'
    os.makedirs(mask_folder, exist_ok=True)

    # Read the mask image
    mask_image = cv2.imread(mask_image_path, cv2.IMREAD_UNCHANGED)

    # Create masks for each entry
    for mask_name, color_code in color_mapping.items():
        try:
            create_mask(mask_name, color_code, mask_image, mask_folder)
        except Exception as e:
            print(f'Error creating mask for {mask_name}: {e}')
    
    # If the mask folder is empty, delete it
    if not os.listdir(mask_folder):
        os.rmdir(mask_folder)
    else:
        print(f'Mask files created and saved in the folder: {mask_folder}')

def hex_to_bgr(hex_code):
    return tuple(reversed([int(hex_code[i:i+2], 16) for i in (1, 3, 5)]))

def create_mask(mask_name, color_code, mask_image, mask_folder):
    # Convert color code to BGR format
    color_bgr = hex_to_bgr(color_code)

    # Output BGR values
    print(f'Mask Name: {mask_name}, Color Code: {color_code}, BGR: {color_bgr}')

    # Exclude alpha channel and use BGR values for inRange
    mask_bgr = mask_image[:, :, :3]
    mask = cv2.inRange(mask_bgr, color_bgr, color_bgr)

    # Do not save if the mask is completely black
    if cv2.countNonZero(mask) == 0 and color_bgr != (0, 0, 0):
        print(f'Mask for {mask_name} is completely black. Not saving.')
        return

    # Save the mask image
    mask_path = os.path.join(mask_folder, f'{mask_name}.png')
    cv2.imwrite(mask_path, mask)
    print(f'Created mask for {mask_name}')

if __name__ == "__main__":
    main()
