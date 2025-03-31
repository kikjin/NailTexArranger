# README

## これは何？
ネイルテクスチャを各指ごとに切り出し、アバターのボディテクスチャ上に再配置するために作られたPythonスクリプト群です。  
ただし、処理対象自体はネイルテクスチャに限るものではありません。

## 基本的な使い方と処理の仕組み

1. `[各アプリケーションなど]` 各テクスチャごとに、切り取り／貼り付け領域を指示するためのsvgファイルを作成します。
1. `[svg_to_annotations.py]` svgファイルから、指示された箇所の情報を読み取り、アノテーション（注釈）情報としてjson形式で保存します。
1. `[arrage_images.py]` 切り取り元の画像ファイルと、切り取り、貼り付け双方のアノテーションファイルを読み込み、各領域ごとに再配置された画像を出力します。

事前準備として、元のテクスチャ画像から、切り取り／貼り付け領域ごとにその領域を指示するためのSVGファイルを作成してもらう必要があります。SVGファイルに求める仕様は　を参照してください。
基本的には、長方形（rect）要素を切り出し箇所に合わせて配置します。
長方形要素の名前（レイヤー名）は各領域を特定するユニークな名前をつけます。
例として、「RightHandThumb」、「RightHandIndex」、「LeftFootMiddle」のようにします。
切り取られた領域は、同名の貼り付け領域に貼り付けられます。

SVGファイルの作成は、InkscapeやAffinity Designer、Adobe Illustratorなどを想定していますが、プログラムが処理できるSVGファイルを作成できればなんでも構いません。
InkscapeとAffinity Designerで動作を確認しています。

## ディレクトリ構成
```
NailTexArranger
├── docs
├── templates
└── workspace
    ├── README.md
    ├── annotations
    ├── inputs
    ├── outputs
    └── scripts
        ├── arrange_images.py
        ├── requirements.txt
        └── svg_to_annotations.py
```
- docs
    - 仕様書など
- templates
    - svgファイルのテンプレート
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

## 使い方

依存パッケージ
```
pip install 
```

