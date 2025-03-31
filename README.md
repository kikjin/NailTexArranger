# NailTexArranger

## これは何？
ネイルテクスチャを各指領域ごとに切り出し、アバターのボディテクスチャ上に再配置するために作られたPythonスクリプト群です。  
ただし、処理対象自体はネイルテクスチャに限るものではありません。

## 基本的な使い方と処理の流れ

1. `[各アプリケーション]` 各テクスチャごとに、切り取り／貼り付け領域を指示するためのsvgファイルを作成します。
1. `[svg_to_annotations.py]` svgファイルから、指示された箇所の情報を読み取り、アノテーション（注釈）情報としてjson形式で保存します。
1. `[arrage_images.py]` 切り取り元の画像ファイルと、切り取り、貼り付け双方のアノテーションファイルを読み込み、各領域ごとに再配置された画像を出力します。

事前準備として、元のテクスチャ画像から、切り取り／貼り付け領域ごとにその領域を指示するためのSVGファイルを作成してもらう必要があります。
SVGファイルでは、長方形（rect）要素を切り出し箇所に合わせて配置します。
長方形要素の名前（レイヤー名）は各領域を特定するユニークな名前をつけます。
例として、「RightHandThumb」、「RightHandIndex」、「LeftFootMiddle」のようにします。
切り取られた領域は、同名の貼り付け領域に貼り付けられます。

SVGファイルの作成は、InkscapeやAffinity Designer、Adobe Illustratorなどを想定していますが、プログラムが処理できるSVGファイルを作成できればなんでも構いません。
InkscapeとAffinity Designerで動作を確認しています。

## ディレクトリ構成
```
NailTexArranger
├── samples
└── workspace
    ├── annotations
    ├── inputs
    ├── outputs
    └── scripts
        ├── arrange_images.py
        ├── requirements.txt
        └── svg_to_annotations.py
```

- templates
    - svgファイルのテンプレートやサンプルファイル
- workspace
    - スクリプト本体や生成ファイルの出力先
- annotations
    - `svg_to_annotations.py`によって生成されるアノテーションファイルの出力先
- inputs
    - 入力ファイル（svgやテクスチャファイル）を入れる想定
- outputs
    - 生成されたテクスチャの出力先
- scripts
    - Pyhonスクリプト

## 基本的な使い方

### 依存パッケージのインストール
```bash
pip install lxml numpy opencv-python
```
または
```bash
pip install -r requirements.txt
```

### アノテーションファイルの作成
```
python scripts/svg_to_annotations.py inputs/svg_from.svg
```
`workspace/annotations/`に`<svgのファイル名>.json`として作成されます。  
アノテーションファイルは切り取り側と貼り付け側の2つ作成する必要があります。


### 切り抜きと再配置
```bash
python scripts/arrange_images.py -a1 annotations/svg_from.json -a2 annotations/svg_to.json inputs/nail_texture.png
```
出力先は`workspace/outputs/<annotation1のファイル名>_to_<annotation2のファイル名>_[yyyyMMdd_HHmmss]/`です。  
指定された領域が切り取り再配置された透過画像と、再配置された領域のマスク画像が生成されます。

## SVGファイルの作成方法

切り抜き領域の指定には、指定のためのベクターグラフィックデータ（.svg）を何らかの方法で作成する必要があります。  
このファイルは切り抜き・貼り付け箇所を指定するためのものなので、同じUV配置をもつテクスチャ間で共有することできます。

SVGを編集するためのソフトとして、[Inkscape](https://inkscape.org/ja/)または[Affinity Designer](https://affinity.serif.com/ja-jp/designer/)の使用を推奨します。
Adobe Illustratorから出力したSVGファイルも使用できると思いますが、動作は未確認です。

`svg_to_annotaions.py`はSVGファイルから以下の情報を読み取ります。
- キャンバスサイズ
  - `svg`要素の`viewbox`サイズ
  - `viewbox`がない場合は`svg`要素の`width`、`height`
- 領域指定のための長方形
  - `rect`要素の位置、大きさ、回転、レイヤー名
  - レイヤー名に当たる属性が見つからない場合は読み取りません
  - `path`や`polygon`など、`rect`以外の要素で記述された図形は読み取りません

svgファイルのテンプレートは`samples/template.svg`に保存されています。  
一からの作成ではなく、このファイルの編集を推奨します。

一般に、ネイルテクスチャ側のUV形状とアバター側のUV形状は異なるため、貼り付け時にアバター側UVの一部がはみ出てしまい、配置したネイルテクスチャが爪の全面に乗らない可能性があります。
これを避けるため、領域指定の矩形を配置する時は、

- 切り取り側はなるべくUVギリギリ
- 貼り付け側は大きめに

配置することをお勧めします。微妙な位置調整は何回か試行錯誤していただくか、出力後に画像編集ソフトで調整してください。

## その他の使い方

### ボディテクスチャの指定
出力時に下に敷く画像(アバターのボディテクスチャなど)をオプション`-u`, `--underlay-image`で指定できます。
指定した場合、切り取り・再配置された透過画像を上に重ねた画像が追加で出力されます。
```bash
python scripts/arrange_images.py -a1 annotations/svg_from.json -a2 annotations/svg_to.json -u inputs/body_texture.png inputs/nail_texture.png
```

### 複数画像の処理
`input_image`には複数のファイルを渡すことができます。例えば、メインテクスチャ以外にカスタムノーマルマップやマスクテクスチャがある場合、1回でまとめて処理できます。  
その場合、出力時に下に敷く画像もそれぞれ指定することができます。
入力画像と下に敷く画像は順番を一致させる必要があります。

出力時に下に敷くテクスチャがない場合は `None`または`''`としてください
```bash
python scripts/arrange_images.py -a1 annotations/svg_from.json -a2 annotations/svg_to.json -u inputs/body_texture.png None inputs/black_4k.png inputs/nail_texture.png inputs/nail_normal.png inputs/nail_rame.png
```

### 矩形領域がUVの隣の島に干渉する場合
`arrange_images.py`はあくまで矩形領域で切り取り・貼り付けを行うため、UV配置によっては矩形領域が隣の島に重なってしまうことがあります。
これを避けるため、切り取り／貼り付け領域を制限するためのマスク画像を指定することができます。
切り取り時のマスクは`-m1`または `--pre-crop-mask`で指定します。貼り付け時のマスクは`-m2`または`--post-paste-mask`で指定します。
```bash
python scripts/arrange_images.py -a1 annotations/svg_from.json -a2 annotations/svg_to.json -u inputs/body_texture.png -m1 inputs/nail_mask.png -m2 body_nail_mask.png inputs/nail_texture.png
```
