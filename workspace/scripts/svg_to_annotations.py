import json
import re
import math
import sys
import argparse
from pathlib import Path

import numpy as np
from lxml import etree

DEFAULT_OUTPUT_FOLDER = Path(__file__).parent.parent / "annotations"  # デフォルトの出力先フォルダ

def get_svg_canvas_size(root):

    width = root.get('width')
    height = root.get('height')

    viewbox = root.get('viewBox')
    
    if viewbox:
        # viewBoxは "min-x min-y width height" の形式
        _, _, vb_width, vb_height = map(int, viewbox.split())
    else:
        vb_width, vb_height = None, None

    final_width = vb_width if vb_width else width
    final_height = vb_height if vb_height else height

    return int(final_width), int(final_height)

def get_element_id(element):
    """
    任意のSVG要素の名前（レイヤー名）を取得
    優先順位は `inkscape:label` > `serif:id` > `id`
    Inkscapeはserif:idを残すが、Affinity Designerは全て削除するため
    Adobe Illustratorはidを使うらしい（未確認）
    """

    ns = {
        'serif': 'http://www.serif.com/',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
    }

    # 名前空間をns辞書から取得
    serif_ns = ns.get('serif')
    inkscape_ns = ns.get('inkscape')

    # inkscape:label
    element_id = element.get(f'{{{inkscape_ns}}}label') if inkscape_ns else None
    if element_id is None:
        # serif:id
        element_id = element.get(f'{{{serif_ns}}}id') if serif_ns else None
    if element_id is None:
        # id (デフォルト)
        element_id = element.get('id')

    return element_id

def parse_transform(transform_str):
    """transform属性をアフィン変換行列に変換"""
    transform_matrix = np.eye(3)  # 単位行列 (初期状態)
    
    if not transform_str:
        return transform_matrix
    
    transform_cmds = re.findall(r'(\w+)\(([^)]+)\)', transform_str)
    for cmd, values in transform_cmds:
        values = list(map(float, values.replace(',', ' ').split()))

        if cmd == "translate":
            tx, ty = values + [0] * (2 - len(values))  # yがない場合は0
            matrix = np.array([[1, 0, tx],
                               [0, 1, ty],
                               [0, 0,  1]])
        elif cmd == "scale":
            sx, sy = values + [values[0]] * (2 - len(values))  # yがない場合はxと同じ
            matrix = np.array([[sx, 0, 0],
                               [0, sy, 0],
                               [0,  0, 1]])
        elif cmd == "rotate":
            angle = np.radians(values[0])
            cx, cy = values[1:3] if len(values) > 2 else (0, 0)
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            matrix = np.array([[cos_a, -sin_a, cx - cx * cos_a + cy * sin_a],
                               [sin_a,  cos_a, cy - cx * sin_a - cy * cos_a],
                               [0, 0, 1]]) # 回転中心へ移動→回転→元の位置へ戻す
        elif cmd == "matrix":
            if len(values) == 6:
                a, b, c, d, e, f = values
                matrix = np.array([[a, c, e],
                                   [b, d, f],
                                   [0, 0, 1]])
        elif cmd =='skewX':
            sx = values[0]
            matrix = np.array([[1, sx, 0],
                               [0, 1, 0],
                               [0, 0, 1]])
        elif cmd == 'skewY':
            sy = values[0]
            matrix = np.array([[1, 0, 0],
                               [sy, 1, 0],
                               [0, 0, 1]])
        else:
            raise ValueError(f"未対応の変形が含まれています: {cmd}")
        
        transform_matrix = transform_matrix @ matrix

    return transform_matrix

def get_global_transform(element):
    """全ての親のtransformを適用"""
    transform_matrix = np.eye(3)
    while element is not None:
        if 'transform' in element.attrib:
            try: 
                transform_matrix = parse_transform(element.attrib['transform']) @ transform_matrix
            except Exception as e:
                raise e
        element = element.getparent()
    return transform_matrix

def has_matrix_skew(transform_matrix):
    a = transform_matrix[0,0]
    b = transform_matrix[1,0]
    c = transform_matrix[0,1]
    d = transform_matrix[1,1]

    # skewがある場合、列ベクトルが直交する
    # 計算すると直角でも0.02くらいでることもある。
    dot = abs(a * b + c * d)
    print("ab+cd", dot)
    if dot > 1e-2:
       return True
    else:
        return False

def apply_transform(matrix, x, y, width, height):
    """変換行列を x, y, width, height に適用する"""
    # 中心点を計算
    center_x = x + width / 2
    center_y = y + height / 2

    # 中心点の変換
    point = np.array([center_x, center_y, 1])
    transformed_point = matrix @ point
    new_center_x, new_center_y = transformed_point[0], transformed_point[1]
    new_center_x, new_center_y = transform_point([center_x, center_y], matrix)

    # 幅と高さの変換（スケールを適用）
    sx = np.linalg.norm(matrix[:2, 0])  # X軸のスケール
    sy = np.linalg.norm(matrix[:2, 1])  # Y軸のスケール
    new_width = width * sx
    new_height = height * sy

    return new_center_x, new_center_y, new_width, new_height

def transform_point(point, transform_matrix):
    if len(point) != 2:
        raise ValueError(f"ポイント座標の形式が正しくありません: {point}")
    point_vector = np.array([point[0], point[1], 1])
    transformed_vector = transform_matrix @ point_vector
    transformed_point = [transformed_vector[0], transformed_vector[1]]
    return transformed_point

def vector(p1, p2):
    return np.array([p2[0] - p1[0], p2[1] - p1[1]])

def parse_length(length_str):
    """
    SVGの長さ属性（例："500", "500px"）から数値部分を抽出する。
    """
    try:
        return float(re.findall(r"[\d.]+", length_str)[0])
    except IndexError:
        return 0.0

def normalize_coord(val, total):
    """ 絶対値から相対値（0～1）に変換 """
    return val / total if total else 0.0

def parse_svg_file(svg_path, is_relative = True):
    """
    SVGファイルをパースして、アノテーション情報の辞書を返す。
    座標はすべて相対値 (0〜1) に正規化する。
    """

    coord_sys = 'relative' if is_relative else 'absolute'

    try:
        tree = etree.parse(svg_path)
    except Exception as e:
        raise ValueError(f"SVGファイルのパースに失敗しました") from e

    root = tree.getroot()
    ns = {
        'svg': 'http://www.w3.org/2000/svg'
    }

    try: 
        svg_width, svg_height = get_svg_canvas_size(root)
    except Exception as e:
        raise ValueError("SVGのキャンバスサイズの取得に失敗しました") from e

    output = {
        "canvas": {
            "width": svg_width,
            "height": svg_height,
            "coordinate_system": coord_sys
        },
        "regions": {}
    }

    for rect in root.findall('.//svg:rect', ns):
        rect_id = get_element_id(rect)

        # Affinity Designerから出力すると、rectではなくその親のgにレイヤー名が付与されるので、親gの名前もチェックする
        if rect_id is None:
            parent = rect.getparent()
            if parent is not None and parent.tag == (f"{{{ns["svg"]}}}g"):
                rect_id = get_element_id(parent)
            if rect_id is None:
                continue  # idが見つからなければスキップ

        # x, y, width, height（絶対座標）
        x = float(rect.get('x', '0'))
        y = float(rect.get('y', '0'))
        width = float(rect.get('width', '0'))
        height = float(rect.get('height', '0'))

        # 全ての親要素のtransformを適用
        try:
            transform_matrix = get_global_transform(rect)
        except Exception as e:
            print(f"トランスフォームの解析エラー: {e} 領域をスキップします: {rect_id}")
            continue

        # 変形後の頂点座標から剪断変形されているか判断する
        # matrixの(a * b + c * d)は0.02くらいでも直角らしい。ひとまず安全な方法で判定
        points = [[x,y], [x+width, y], [x+width, y+height], [x, y+height]]
        new_points = [transform_point(p, transform_matrix) for p in points]

        # 3頂点のなす角を求める
        vec1 = vector(new_points[0], new_points[1])
        vec2 = vector(new_points[1], new_points[2])
        dot_product = np.dot(vec1, vec2)
        angle_from_three_points = math.degrees(math.acos(dot_product / (np.sqrt(np.dot(vec1, vec1)) * np.sqrt(np.dot(vec2, vec2)))))
        
        # 許容範囲を大きめにとる(微小な剪断変形は無視する)
        if abs(angle_from_three_points - 90.0) > 1e-3:
            print(f"Warning: トランスフォームに剪断変形が含まれています。(角度={angle_from_three_points}°) スキップします。: {rect_id}")
            continue

        center_x_abs, center_y_abs, width, height = apply_transform(transform_matrix, x, y, width, height)

        if is_relative:
            # 正規化
            center = [
                normalize_coord(center_x_abs, svg_width),
                normalize_coord(center_y_abs, svg_height)
            ]
            size = [
                normalize_coord(width, svg_width),
                normalize_coord(height, svg_height)
            ]
        else:
            center = [center_x_abs, center_y_abs]
            size = [width, height]

        # angleの計算
        angle_vector = transform_matrix @ np.array([0, 1, 0])
        angle = math.degrees(math.atan2(angle_vector[0], angle_vector[1]))

        if angle == -0.0:
            angle = 0.0 # 念の為
        

        region = {
            "center": center,
            "size": size,
            "angle": angle
        }

        if rect_id in output["regions"]:
            print(f"Warning: 領域名 '{rect_id}' が重複しています。スキップします。")
            print(region)
            continue  

        output["regions"][rect_id] = region

    return output


def determine_output_path(input_svg: Path, output_arg: Path | None):
    """
    入力SVGファイル名と第二引数 (出力パス) を元に、最終的な出力パスを決定する。
    
    ルール：
      - 第二引数が存在しない、または空の場合：
          → DEFAULT_OUTPUT_FOLDER/annotations_from_＜入力SVGファイル名_without拡張子＞.json
      - 第二引数が存在する場合：
          - もしフォルダの場合：そのフォルダ内に上記のデフォルトファイル名で出力
          - ファイル名を含むパスの場合：そのファイルパスで出力
    """
    input_basename = input_svg.stem
    default_filename = f"{input_basename}.json"

    # 第二引数が空の場合
    if output_arg is None or output_arg == Path():
        output_folder = DEFAULT_OUTPUT_FOLDER
        output_folder.mkdir(parents=True, exist_ok=True)
        return output_folder / default_filename

    if output_arg.is_dir():
        # フォルダが指定された場合
        output_arg.mkdir(parents=True, exist_ok=True)
        return output_arg / default_filename
    else:
        # 出力パスにディレクトリ部分がなければ、DEFAULT_OUTPUT_FOLDER を使用
        output_dir = output_arg.parent if output_arg.parent != Path() else DEFAULT_OUTPUT_FOLDER
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / output_arg.name
    
def main():
    parser = argparse.ArgumentParser(description='SVGファイルから長方形（rect）要素の位置情報を抽出するスクリプトです。')

    parser.add_argument('input_svg', nargs='+', help='SVGファイル')
    parser.add_argument('-o', '--output-path', help='出力先フォルダ')

    args = parser.parse_args()

    input_svgs = [Path(p) for p in args.input_svg]
    output_arg = Path(args.output_path) if args.output_path else None

    input_svg = input_svgs[0] # 後で対応する

    # 入力SVGファイルの存在チェック
    if not input_svg.is_file():
        print(f"エラー: 入力SVGファイルが存在しません: {input_svg}")
        sys.exit(1)

    try:
        annotations = parse_svg_file(input_svg)
    except Exception as e:
        print(f"エラー: SVGファイルの解析に失敗しました: {e}")
        sys.exit(1)
    
    if not annotations["regions"]:
        print(f"アノテーションが空です。")

    output_path = determine_output_path(input_svg, output_arg)

    try:
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(annotations, f, indent=2, ensure_ascii=False)
        print(f"SVGファイル '{input_svg}' からアノテーション情報を抽出し、'{output_path}' に出力しました。")
    except Exception as e:
        print(f"エラー: JSONファイルの出力に失敗しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()