import cv2
import numpy as np
import os
import sys

def main():
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} [source image path] [mask folder path]")
        return
    
    # Get the source image file name from the arguments
    src_image_path = sys.argv[1]
    src_image_name = os.path.splitext(os.path.basename(src_image_path))[0]

    mask_folder = sys.argv[2]

    # Load the source image
    src_image = cv2.imread(src_image_path, cv2.IMREAD_UNCHANGED)

    # Get a list of mask image file names
    mask_files = [f for f in os.listdir(mask_folder) if f.endswith('.png')]

    # Check and create the output folder if it doesn't exist
    output_folder = f'clipped_{src_image_name}'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop to process mask images one by one
    for mask_file in mask_files:
        mask_path = os.path.join(mask_folder, mask_file)  # File path of the mask image
        mask_image = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)  # Read the mask image in grayscale

        # Inside the loop, before applying the bitwise operation
        if mask_image.shape[:2] != src_image.shape[:2]:
            mask_image = cv2.resize(mask_image, (src_image.shape[1], src_image.shape[0]))

        # clip the original image using the ask
        # White parts (255) in the mask image will be the clipped area
        result_image = cv2.bitwise_and(src_image, src_image, mask=mask_image)

        # Add an alpha channel
        result_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2BGRA)
        result_image[:, :, 3] = mask_image

        # Clip transparent parts
        clipped_image = clip_transparent(result_image)

        # Generate output file name
        base_name = os.path.splitext(os.path.basename(src_image_path))[0]
        output_name = f'{base_name}_{os.path.splitext(mask_file)[0]}.png'

        # Save the clipped image as a transparent PNG
        output_path = os.path.join(output_folder, output_name)
        cv2.imwrite(output_path, clipped_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # Save as transparent PNG

    print(f'Clipping complete. Output destination: {output_folder}.')


def clip_transparent(image):
    # Detect transparent areas and get their coordinates
    alpha_channel = image[:, :, 3]
    non_transparent_indices = np.where(alpha_channel > 0)
    min_x = np.min(non_transparent_indices[1])
    max_x = np.max(non_transparent_indices[1])
    min_y = np.min(non_transparent_indices[0])
    max_y = np.max(non_transparent_indices[0])

    # Create a new image without the transparent parts
    clipped_image = image[min_y:max_y+1, min_x:max_x+1]

    return clipped_image

if __name__ == "__main__":
    main()
