import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np


DEFAULT_OUTPUT_FOLDER = Path(__file__).parent.parent / "outputs"  # デフォルトの出力先フォルダ

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_json_file(file_path):
    file = Path(file_path)

    # ファイルが存在するか確認
    if not file.exists():
        raise FileNotFoundError(f"ファイルが存在しません：{file}")

    # JSON ファイルを読み込む
    try:
        with open(file, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"ファイルからJSONをデコードできませんでした： {file_path}.")
    except Exception as e:
        raise(f"予期しないエラーが発生しました： {e}")

def read_image_as_rgba(image_path):
    """
    画像をRGBAで読み込む。アルファチャンネルを持たない場合は追加する。
    """

    if image_path is None:
        return None
    
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません： {image_path}")

    image = cv2.imread(image_path.as_posix(), cv2.IMREAD_UNCHANGED)

    if image is None:
        raise IOError(f"画像の読み込みに失敗しました： {[image_path]}")

    if image.shape[2] == 3:
        alpha = np.ones((image.shape[0], image.shape[1]), dtype=np.uint8) * 255
        image = cv2.merge([image, alpha])

    return image

def convert_mask_to_grayscale(mask: np.ndarray) -> np.ndarray:
    """
    マスク画像をグレースケール化する。

    - 1チャンネル（グレースケール）の場合はそのまま返す
    - 3, 4チャンネル（RGB, RGBA）の場合は輝度計算してグレースケール化(アルファチャンネルは無視)
    """
    if len(mask.shape) == 2:
        # すでにグレースケール
        return mask
    
    elif len(mask.shape) == 3:
        h, w, c = mask.shape
        if c == 3 or c == 4:
            # RGB / RGBAの場合、NTSC係数を使ってグレースケール化
            return cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    raise ValueError("入力マスク画像はグレースケール, RGB, RGBAのいずれかである必要があります")

def apply_mask(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    任意のチャンネル数の画像に対して、マスクを適用する関数。
    
    - 完全透明(マスク=0)の部分のRGB値を (0,0,0) にする。
    - それ以外の部分のRGB値はそのまま保持。
    - 入力画像のチャンネル数 (1, 3, 4) に対応。
    """

    mask = convert_mask_to_grayscale(mask)
    mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
    mask = np.clip(mask, 0, 255).astype(np.uint8) # 念の為

    # Grayscale image (1 channel)
    if len(image.shape) == 2 or image.shape[2] == 1:
        image = image.astype(np.float32)
        # Expand mask to match image dimensions if necessary
        image = image * (mask[..., np.newaxis] / 255.0)
        return image.astype(np.uint8)

    # Color image without alpha (3 channels)
    elif image.shape[2] == 3:
        # Add alpha channel from mask and set fully transparent pixels to black
        new_image = np.dstack([image, mask])
        new_image[mask == 0, :3] = 0
        return new_image

    # RGBA image (4 channels)
    # 元々透明なら透明を維持。そうでない場合は透明度を乗算
    elif image.shape[2] == 4:
        image = image.copy()
        original_alpha = image[:, :, 3]
        new_alpha = (original_alpha.astype(np.float32) / 255.0) * (mask.astype(np.float32) / 255.0) * 255.0
        new_alpha[original_alpha == 0] = 0
        image[:, :, 3] = new_alpha.astype(np.uint8)
        return image

    else:
        raise ValueError("Unsupported number of channels in image")

def create_small_image_overlay(small_img, large_img_size, region):
    """
    小さな画像を大きな画像の指定箇所に回転を考慮して配置する
    透明な大きい画像を用意し、そこに配置してから回転する
    余計な部分も回転していて計算量が無駄に多そうな気持ちはある
    """
    center = region["center"]
    size = region["size"]
    angle = region["angle"]

    offset = (int(center[0] - size[0] / 2), int(center[1] - size[1] / 2))
    size =(int(size[0]), int(size[1]))
    center = tuple(center)

    # 透明な画像を作成
    large_img = np.zeros((large_img_size[0], large_img_size[1], 4), dtype=np.uint8)

    resized_small_img = cv2.resize(small_img, size)
    large_img[offset[1]:offset[1]+size[1], offset[0]:offset[0]+size[0], :4] = resized_small_img
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1)

    rotated_img = cv2.warpAffine(large_img, rotation_matrix, (large_img.shape[1], large_img.shape[0]))

    return rotated_img

def convert_relative_to_absolute(annotation, canvas_size):
    coordinate_system = annotation['canvas']['coordinate_system']

    # absoluteの場合はそのまま返す
    if coordinate_system == "absolute":
        return annotation

    if coordinate_system != "relative":
        raise ValueError(f"Unsupported coordinate system: {coordinate_system}")

    canvas_width, canvas_height = canvas_size

    annotation_abs = {
        'canvas': annotation['canvas'].copy(),
        'regions': {}
    }
    annotation_abs['canvas']['coordinate_system'] = 'absolute'

    for region_name, region_data in annotation['regions'].items():
        region_abs = region_data.copy()

        # 'center'の相対座標を絶対座標に変換
        region_abs['center'] = [
            region_data['center'][0] * canvas_width,  # X座標
            region_data['center'][1] * canvas_height  # Y座標
        ]
        
        # 'size'の相対座標を絶対座標に変換
        region_abs['size'] = [
            region_data['size'][0] * canvas_width,  # 幅
            region_data['size'][1] * canvas_height  # 高さ
        ]

        # 他のフィールドはそのままコピー
        annotation_abs['regions'][region_name] = region_abs
    
    return annotation_abs

def crop_and_rearrange(input_image: np.ndarray, annotation1: dict, annotation2: dict, underlay_image=None, pre_crop_mask=None, post_paste_mask=None, creates_mask=False):
     # 入力と出力の画像サイズ
    input_size = (input_image.shape[1], input_image.shape[0])
    output_size = (int(annotation2["canvas"]["width"]), int(annotation2["canvas"]["height"]))   

    if pre_crop_mask is not None:
        input_image = apply_mask(input_image, pre_crop_mask)

    # 相対座標を絶対座標に変換
    annotation1_abs = convert_relative_to_absolute(annotation1, input_size)
    annotation2_abs = convert_relative_to_absolute(annotation2, output_size)

    # 出力画像と出力マスク画像を準備
    output_image = np.zeros((output_size[1], output_size[0], 4), dtype=np.uint8)
    if creates_mask: output_mask_image = np.zeros((output_size[1], output_size[0], 4), dtype=np.uint8)  # 黒（0）のマスク画像

    # annotation2の領域ごとに処理
    for region_name, region2 in annotation2_abs["regions"].items():

        # annotation1から同名の領域を取得
        if region_name in annotation1_abs["regions"]:
            region1 = annotation1_abs["regions"][region_name]
        else:
            logger.warning(f"領域がannotation1に見つからないためスキップします: {region_name} ")
            continue

        # annotationのregion情報から領域を指定
        src_rect_center = (int(region1['center'][0]), int(region1['center'][1]))
        src_rect_size = (int(region1['size'][0]), int(region1['size'][1]))
        angle = region1['angle']

        # todo: 回転ではみ出る可能性があるので、"回転+中央に移動"にする

        # ステップ1: 切り抜き
        # Extract rotated region from the source image (region1)
        rotation_matrix = cv2.getRotationMatrix2D(src_rect_center, angle, 1)
        rotated_region = cv2.warpAffine(input_image, rotation_matrix, input_size)

        # Calculate the bounding box of the rotated region
        rotated_x = int(src_rect_center[0] - src_rect_size[0] / 2)
        rotated_y = int(src_rect_center[1] - src_rect_size[1] / 2)
        rotated_w = int(src_rect_size[0]) 
        rotated_h = int(src_rect_size[1])

        # Crop the rotated region
        cropped_image = rotated_region[rotated_y:rotated_y + rotated_h, rotated_x:rotated_x + rotated_w]

        # ステップ2: 貼り付け
        small_image_overlay = create_small_image_overlay(cropped_image, output_size, region2)

        # 大きな画像と回転後の透明な画像をアルファブレンドで合成
        for c in range(0, 4):
            output_image[:, :, c] = output_image[:, :, c] * (1 - small_image_overlay[:, :, 3] / 255.0) + small_image_overlay[:, :, c] * (small_image_overlay[:, :, 3] / 255.0)

        # マスク画像の作成
        # マスク用に、真っ白なcropped_imgを作る
        if creates_mask:
          white_cropped_image = np.ones((cropped_image.shape[0], cropped_image.shape[1], 4), dtype=np.uint8) * 255
          small_mask_image_overlay = create_small_image_overlay(white_cropped_image, output_size, region2)

          output_mask_image = np.maximum(output_mask_image, small_mask_image_overlay)

    # 出力画像が透明な場合、エラーを出す
    if np.sum(output_image) == 0:
        raise ValueError("Output mask image is completely blank. No regions were processed.")
    
    if post_paste_mask is not None:
        output_image = apply_mask(output_image, post_paste_mask)

    output_images = {}
    output_images["output"] = output_image
    if creates_mask:
        if output_mask_image is not None: 
            output_mask_image = convert_mask_to_grayscale(output_mask_image)
            output_images["mask"] = output_mask_image

    # underlay_imageが存在する場合、その上に合成
    if underlay_image is not None:
        underlay_height, underlay_width = underlay_image.shape[:2]

        if underlay_width != output_size[0] or underlay_height != output_size[1]:
            # サイズを調整する
            output_image = cv2.resize(output_image, (underlay_width, underlay_height))

        # 出力画像とoverlay画像を合成
        for c in range(0, 4):
            underlay_image[:, :, c] = underlay_image[:, :, c] * (1 - output_image[:, :, 3] / 255.0) + output_image[:, :, c] * (output_image[:, :, 3] / 255.0)

        output_images["composite"] = underlay_image
    
    return output_images

def create_output_directory(output_path: Path, annotation1_path: Path, annotation2_path: Path):
    """
    アノテーション1とアノテーション2のファイル名からフォルダ名を作成し、output_path の中に作成する
    """

    annotation1_name = annotation1_path.stem
    annotation2_name = annotation2_path.stem
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_folder_name = f"{annotation1_name}_to_{annotation2_name}_{date_str}"
    new_output_path = output_path / new_folder_name

    new_output_path.mkdir(parents=True, exist_ok=True)
    
    return new_output_path

def determine_file_base_name(image_path: Path, annotation2_path: Path):
    base_name = f"{image_path.stem}_for_{annotation2_path.stem}"
    return base_name

def determine_mask_name(annotation2_path: Path):
    mask_name = f"{annotation2_path.stem}_mask"
    return mask_name

def determine_composite_name(annotation1_path: Path, overlay_image_path: Path):
    overlay_name = f"{overlay_image_path.stem}_with_{annotation1_path.stem}"
    return overlay_name

def save_image(image, output_path):
    cv2.imwrite(output_path, image)
    logger.info(f"Image saved to {output_path}")

def process_images_batch(
    input_image_paths,
    annotation1_path,
    annotation2_path,
    output_base_dir_path=DEFAULT_OUTPUT_FOLDER,
    underlay_image_paths=None,
    width_override=None,
    height_override=None,
    pre_crop_mask_path=None,
    post_paste_mask_path=None
):
    input_image_paths = [Path(p) for p in input_image_paths]
    annotation1_path = Path(annotation1_path)
    annotation2_path = Path(annotation2_path)
    underlay_image_paths = [Path(p) for p in underlay_image_paths] if underlay_image_paths else []

    width_override = int(width_override) if width_override else None
    height_override = int(height_override) if height_override else None
    pre_crop_mask_path = Path(pre_crop_mask_path) if pre_crop_mask_path else None
    post_paste_mask_path = Path(post_paste_mask_path) if post_paste_mask_path else None

    input_images = []
    for path in input_image_paths:
        try:
            image = read_image_as_rgba(path)
            input_images.append(image)
        except Exception as e:
            logger.warning(f"{e} \n - このファイルはスキップされます。")
            input_images.append(None)
    #input_imagesが空か全部Noneだったらエラーで処理を終わる
    if not input_images or all(image is None for image in input_images):
        raise ValueError("入力画像が空です。全ての画像読み込みに失敗しました。")

    annotation1 = load_json_file(annotation1_path)
    annotation2 = load_json_file(annotation2_path)

    if width_override:
        annotation2['canvas']['width'] = width_override
    if height_override:
        annotation2['canvas']['height'] = height_override

    # underlay path normalization
    if not underlay_image_paths:
        underlay_image_paths = [None]
    if len(underlay_image_paths) > len(input_image_paths):
        excess = underlay_image_paths[len(input_image_paths):]
        logger.warning("underlay_imageの要素数が多すぎます。underlay_imageの要素数はinput_imageの要素数以下である必要があります。\n - 以下のテクスチャは無視されます。")
        for item in excess:
            logger.warning(f" - {item}")

    underlay_paths_cleaned = []
    for i in range(len(input_image_paths)):
        try:
            path = underlay_image_paths[i]
            if not path or str(path).lower() == 'none':
                underlay_paths_cleaned.append(None)
            else:
                underlay_paths_cleaned.append(path)
        except IndexError:
            underlay_paths_cleaned.append(None)

    underlay_images = [read_image_as_rgba(img) for img in underlay_image_paths]

    pre_crop_mask = read_image_as_rgba(pre_crop_mask_path) if pre_crop_mask_path else None
    post_paste_mask = read_image_as_rgba(post_paste_mask_path) if post_paste_mask_path else None

    # 出力先フォルダを作成
    output_base_dir_path = DEFAULT_OUTPUT_FOLDER
    output_base_dir_path.mkdir(parents=True, exist_ok=True)
    output_dir = create_output_directory(output_base_dir_path, annotation1_path, annotation2_path)

    creates_mask = post_paste_mask is None

    # メイン処理のループ
    for i in range(len(input_images)):
        if input_images[i] is None:
            continue

        try:
            output_images = crop_and_rearrange(
                input_images[i], annotation1, annotation2,
                underlay_images[i], pre_crop_mask, post_paste_mask, creates_mask
            )
        except Exception as e:
            logger.error(f"エラーが発生したため'{input_image_paths[i]}'の処理は中断されました：\n - {e}")
            continue

        file_name = determine_file_base_name(input_image_paths[i], annotation2_path)
        for type, img in output_images.items():
            if type == "output":
                save_image(img, output_dir / f"{file_name}.png")
            elif type == "mask":
                mask_name = determine_mask_name(annotation2_path)
                save_image(img, output_dir / f"{mask_name}.png")
                creates_mask = False
            elif type == "composite":
                underlay_file_name = determine_composite_name(annotation1_path, underlay_image_paths[i])
                save_image(img, output_dir / f"{underlay_file_name}.png")
            else:
                save_image(img, output_dir / f"{file_name}_{type}.png")

    if not any(output_dir.iterdir()):
        output_dir.rmdir()
        logger.warning("出力内容が空です。")

    logger.info("処理を完了しました。")

def main():
    parser = argparse.ArgumentParser(
        description='画像とアノテーションファイルから複数の矩形領域を切り取り再配置するスクリプトです。',
        add_help=False
    )

    parser.add_argument('--help', action='help', help='このヘルプメッセージを表示')
    parser.add_argument('input_image', nargs='+', help='切り取られるテクスチャファイル')
    parser.add_argument('-a1', '--annotation1', required=True, help='切り取り箇所を指定するアノテーションファイル')
    parser.add_argument('-a2', '--annotation2', required=True, help='貼り付け箇所を指定するアノテーションファイル')
    parser.add_argument('-u', '--underlay-image', nargs='*', help='出力画像の下に重ねる画像。input_imageが複数ある場合は同じ順番で複数指定する。')
    parser.add_argument('-w', '--width', help='出力画像の幅。省略した場合annotation2のキャンバスサイズを使用します。')
    parser.add_argument('-h', '--height', help='出力画像の高さ。省略した場合annotation2のキャンバスサイズを使用します。')
    parser.add_argument('-m1', '--pre-crop-mask', help='切り取り領域を詳細指定するためのマスク画像')
    parser.add_argument('-m2', '--post-paste-mask', help='貼り付け領域を詳細指定するためのマスク画像')

    args = parser.parse_args()

    try:
        process_images_batch(
            args.input_image,
            args.annotation1,
            args.annotation2,
            DEFAULT_OUTPUT_FOLDER,
            args.underlay_image,
            args.width,
            args.height,
            args.pre_crop_mask,
            args.post_paste_mask
        )
    except Exception as e:
        logger.critical(f"{e}")

if __name__ == '__main__':
    main()