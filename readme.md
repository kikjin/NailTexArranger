# NailTexArranger

[日本語のreadme](readme_jp.md)

NailTexArranger is a set of Python scripts designed to simplify the process of modifying 3D avatars by applying nail textures to them. It achieves this by clipping nail textures for each finger using mask images and placing them on another avatar's texture.

## Features

- Clip nail textures for individual fingers.
- Apply the clipped textures to an avatar body texture.
- Streamline the process of nail changes for 3D avatars.

## Requirements

- Python 3.x
- OpenCV (cv2)
- NumPy
- PyYAML

## Usage

1. Clone or download this repository to your local machine.

1. Ensure you have Python 3.x installed along with the required libraries (`cv2`, `NumPy`, `PyYAML`).

1. Prepare mask images to clip nail textures for each finger part. You can use `generate_masks.py` for that.

1. To use `generate_masks.py`, you have to create an image with specific colors on parts you want to clip. Colors to be painted are defined in `name_color_mapping.py`.

1. Run `clip_image.py` to clip the nail texture to each finger part.

1. Prepare a YAML file to define where each nail textures should be placed. You can use `generate_arrangement_settings.py` for that.

1. Run `arrange_images.py` to arrange clipped nail textures to your avatar's body texture.

## Getting Started

### Clone or Download
Run this command to clone this repository or just click the `Download ZIP` button.
```bash
git clone https://github.com/kikjin/NailTexArranger.git
```

### Install Python and required libraries
Install Python 3.x according to your OS.  
Install OpenCV, NumPy, PyYAML as follows:
```bash
pip install opencv-python numpy pyyaml
```

### Prepare images for clipping and arrangement
You need to prepare two images that match the nail texture and the avatar's body texture. For each part of the nail texture, paint specific colors to specify the areas to be clipped. Additionally, paint the same color corresponding to each finger to specify the paste destination area on the avatar's texture.  
The colors to be painted are defined in `name_color_mapping.yaml`. To change the colors for recognizing cutout/paste destination areas, please edit this file.
The source for clipping should be aligned with the shape of the nail or specified as a rectangle. If specified as a rectangle, it may interfere with adjacent nails depending on the UV layout of the paste destination.  
It is recommended to specify the paste destination as a rectangular area.

### Generate mask images
Generate mask images to clip as follows:
```
python generate_masks.py [mask image path]
```
Created masks are saved in `masks_MASK_IMAGE_NAME` folder.

### Clip nail texture
Clip the nail texture using the mask image you just created.
```
python clip_image.py [source image path] [mask folder path]
```
Clipped images are saved in `clipped_SOURCE_IMAGE_NAME` folder.

### Generate arrangement_settings.yaml
Generate your avatar's `arrangement_settings.yaml` as follows:
```
python generate_arrangement_settings.py [source image path]
```

`arrangement_settings_SOURCE_IMAGE_NAME.yaml` will be created.

### Arrange clipped images

```
python arrange_images.py [arrangement settings file] [clipped image folder] [composite image (optional)]
```
A transparent image with arranged nail texture will be created. If you specify a composite image (avatar body texture), an avatar texture with arranged nails will also be created.


## License

This project is licensed under the MIT License.