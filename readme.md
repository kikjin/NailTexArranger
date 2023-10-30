# NailTexArranger

NailTexArranger is a set of Python scripts designed to simplify the process of modifying 3D avatars by applying nail textures to them. It achieves this by cropping nail textures for each finger using mask images and placing them on another avatar texture.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Usage](#usage)
- [Getting Started](#getting-started)
- [Examples](#examples)
- [License](#license)

## Features

- Crop nail textures for individual fingers.
- Apply the cropped textures to an avatar texture.
- Streamline the process of nail changes for 3D avatars.

## Requirements

- Python 3.x
- OpenCV (cv2)
- NumPy
- PyYAML


## Short Description

1. Clone or download this repository to your local machine.

1. Ensure you have Python 3.x installed along with the required libraries (`cv2`, `NumPy`, `PyYAML`).

1. Prepare mask images to crop nail texture for each finger part. You can use `generate_masks.py` for that.

1. Run `crop_image.py` to crop the nail texture to each finger part.

1. Prepare `output_settings.yaml` to define where each nail textures should be arranged. This file must be created for each avatar.

1. Run `combine_images.py` to arrange cropped nail textures to your avatar's body texture.


## Usage

1. Create an image to generate mask images for each finger part of the nail texture by using image editing software, etc.

1. Run the `generate_masks.py` script to generate mask
Place your nail texture images in the `cropped` folder.

1. Create or modify a YAML settings file specifying the parameters for each nail texture. Refer to the provided sample `settings.yaml` for guidance.

1. Run the `NailTexArranger.py` script, passing the settings file as an argument.

1. If a composite image is specified, it will overlay the generated nail arrangement on it. The result will be saved in the `out` folder.

## Getting Started

1. Clone the repository to your local machine:

```bash
git clone https://github.com/username/NailTexArranger.git
```

1. install the required libraries:
```bash
pip install opencv-python numpy pyyaml
```
1. Follow the steps outlined in the Usage section.

## Examples

For detailed examples and usage, refer to the examples directory.

## License

This project is licensed under the MIT License.