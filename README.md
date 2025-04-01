# NailTexArranger

## これは何？
ネイルテクスチャを各指領域ごとに切り出し、アバターのボディテクスチャ上に再配置するために作られたPythonスクリプト群です。  
ただし、処理対象自体はネイルテクスチャに限るものではありません。  
いわゆる「付け爪」ではなくアバター素体のテクスチャに統合することで、メッシュ容量及びテクスチャ容量の削減に有効です。

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
├── LICENSE
├── README.md
├── samples
└── workspace
    ├── annotations
    ├── inputs
    ├── outputs
    ├── requirements.txt
    └── scripts
        ├── arrange_images.py
        └── svg_to_annotations.py
```

- templates
    - svgファイルのテンプレートやサンプルファイル
- workspace
    - スクリプトの実行用フォルダ
- annotations
    - `svg_to_annotations.py`によって生成されるアノテーションファイルの出力先
- inputs
    - 入力ファイル（svgやテクスチャファイル）を入れる想定
- outputs
    - 生成されたテクスチャの出力先
- scripts
    - Pyhonスクリプト


## \[🔰初心者向け\] ダウンロードと環境構築について
説明が不要な方は飛ばしてください。

まず、このリポジトリの内容をダウンロードし、コマンドラインでpyhtonが実行できる環境を作成する必要があります。
コマンドライン操作自体に馴染みがない場合は、`cd`や`ls`などのごく基本的なコマンド操作を確認しておいてください。

### ダウンロード
[Releases](https://github.com/kikjin/NailTexArranger/releases)から最新のリリース(Source code (zip))をダウンロードし、解凍してください。  
その後、`NailTexArranger`フォルダを好きな場所に配置してください。

### pythonの環境構築
実行には**python 3**が必要です。今のところこのプロジェクトの作成は**python3.13**を使用しています。

#### pythonのインストール（macOSの場合）
標準でpython3がインストールされていますが、Homebrewから最新のpython3をインストールすることを推奨します。ただし、最近のApple Silicon搭載モデルではそれなりに新しいバージョンのpyhtonがインストールされているようなので、そのままでも実行できるかもしれません。

> [!TIP]
> macOS環境では、pythonの実行コマンドが`python`ではなく`python3`になっていることに注意してください。（`python`とするとpython2が実行されます。）  
> 以降のコマンド実行例では、`python`コマンドを全て`python3`に読み替えてください。

まず、Homebrewをインストールしていない場合は、以下のリンクよりアクセスし、「ターミナル」でHomebrewのインストールコマンドを実行してください。

https://brew.sh/ja/

Homebrewがインストールされたら、続けて以下のように入力してpythonをインストールします。
```bash
brew install python
```

インストールが完了したら、以下のように入力し、きちんとバージョンが表示されればOKです。
```
python --version
```

#### pythonのインストール（Windowsの場合）
「Windows PowerShell」を開き、以下のように入力してpythonをインストールします。
```
winget install python
```

インストールが完了したら、以下のように入力し、きちんとバージョンが表示されればOKです。
```
python --version
```

#### pyhton仮想環境の構築
pythonでは様々なパッケージをインストールして使用するため、プロジェクトごとに使用するパッケージを分けて管理することが推奨されます。
`venv`コマンドで仮想環境を作成できます。

まず、作業ディレクトリを`NailTexArranger/workspace`に移動してください。
```
cd <フォルダのパス>/NailTexArranger/workspace
```

**仮想環境の作成**
以下のコマンドで、仮想環境を作成します。
```
python -m venv venv
```
2つ目の`venv`は仮想環境名です。自由に設定できますが、そのまま`venv`とするのがお勧めです。

仮想環境に入ると、プロンプトの一番左端に`(venv)`と着くので区別できます。

**仮想環境の有効化**  
以下のように`venv`フォルダ内にある`activate`を実行すると仮想環境に入ります。
```
# macOS
source venv/bin/activate

# Windows
.\venv\Scripts\activate
```

**仮想環境の無効化**
```
deactivate
```

<br />

これで準備が整いました。
**以降の操作は仮想環境(venv)に入った状態で行なってください。**

-----

## 基本的な使い方

以下、作業ディレクトリは`NailTexArranger/workspace`とします。

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
出力先フォルダは`workspace/outputs/<annotation1のファイル名>_to_<annotation2のファイル名>_[yyyyMMdd_HHmmss]/`です。  
実行のたびに`outputs`フォルダ内に自動でフォルダが作成されます。
指定した領域が切り取り・再配置された透過画像が出力されます。  
また、配置された領域のためのマスク画像も自動で生成されます。

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
  - レイヤー名は`inkscape:label`、`serif:id`、または`id`を読み取ります。

領域指定のための長方形は、以下の注意点があります。

- レイヤー名は切り取り／貼り付け領域を特定するための重複しない名前をつける必要があります
- レイヤー名に当たる属性が見つからない場合は読み取りません
- **長方形の"上"方向をネイルテクスチャの先端方向に合わせてください**
- 長方形は自由に移動・拡大縮小・回転できますが、せん断変形（shear、skew）は使用できません
- `path`や`polygon`など、`rect`以外の要素で記述された図形は読み取りません

svgファイルのテンプレートは`samples/template.svg`に保存されています。  
一からの作成ではなく、このファイルの編集を推奨します。

長方形の"向き"は切り取り／再配置する上で重要です。単に形状を合わせるのではなく、回転させて向きを合わせてからサイズを調整してください。ただし、どうもInkscapeでは図形の"向き"がわかりやすく表示されないようです……

一般に、ネイルテクスチャ側のUV形状とアバター側の爪のUV形状は異なるため、貼り付け時にアバター側UVの一部がはみ出てしまい、配置したネイルテクスチャが爪の全面に乗らない可能性があります。
これを避けるため、領域指定の長方形を配置する時は、

- 切り取り側はなるべく小さく
- 貼り付け側は大きめに

配置することをお勧めします。微妙な位置調整は何回か試行錯誤していただくか、出力後に画像編集ソフトで調整してください。

長方形を大きくするとUVの隣の島（UVアイランド）に被ってしまう時は、その部分を削除するためのマスク画像を別途用意することで、切り取り／貼り付け対象領域を調整できます。マスク画像は画像編集ソフトなどを使用して作成してください。

マスク画像の使い方は[矩形領域がUVの隣の島に干渉する場合](#矩形領域がUVの隣の島に干渉する場合)を参考にしてください。

## その他の使い方

### ボディテクスチャの指定
出力時に下に敷く画像(アバターのボディテクスチャなど)をオプション`-u`, `--underlay-image`で指定できます。
指定した場合、統合された画像が追加で出力されます。
```bash
python scripts/arrange_images.py inputs/nail_texture.png -a1 annotations/svg_from.json -a2 annotations/svg_to.json -u inputs/body_texture.png 
```

### 複数画像の処理
`arrange_images.py`の`input_image`には複数のファイルを渡すことができます。例えば、メインテクスチャ以外にカスタムノーマルマップやマスクテクスチャがある場合、1回でまとめて処理できます。  
その場合、出力時に下に敷く画像もそれぞれ指定することができます。
入力画像と下に敷く画像は順番を一致させる必要があります。

一部の入力テクスチャのみ対応する下に敷くテクスチャがない場合は `None`または`''`（空文字列）としてください
```bash
python scripts/arrange_images.py inputs/nail_texture.png inputs/nail_normal.png inputs/nail_rame.png -a1 annotations/svg_from.json -a2 annotations/svg_to.json -u inputs/body_texture.png None inputs/black_4k.png
```

### 矩形領域がUVの隣の島に干渉する場合
`arrange_images.py`はあくまで矩形領域で切り取り・貼り付けを行うため、UV配置によっては矩形領域が隣の島（UVアイランド）に重なってしまうことがあります。
これを避けるため、切り取り／貼り付け領域を制限するためのマスク画像を指定することができます。
切り取り時のマスクは`-m1`または `--pre-crop-mask`で指定します。貼り付け時のマスクは`-m2`または`--post-paste-mask`で指定します。
```bash
python scripts/arrange_images.py inputs/nail_texture.png -a1 annotations/svg_from.json -a2 annotations/svg_to.json -u inputs/body_texture.png -m1 inputs/nail_mask.png -m2 body_nail_mask.png
```
`--post-paste-mask`を指定した場合は、通常自動出力される、貼り付け領域のためのマスク画像は出力されません。

### 出力時の解像度を変更する
デフォルトでは出力される透過画像の解像度は`annotation2`に記載されたキャンバスサイズになります。
これは`annotaion2`を作成した時のSVGのキャンバスサイズと一致します。出力解像度を変更したい場合は、大きく2つの方法があります。

#### 1. annotaion2のjsonファイルを編集する
`svg_to_annotaions.py`によって出力されたjosnファイルを開いてください。  
一番上に`"canvas"`の`"width"`、`"height"`が記載されています。この値を変更してください。
```json
{
  "canvas": {
    "width": 2048,
    "height": 2048,
    "coordinate_system": "relative"
  }
}
```

#### 2. --width --height オプションを使用する
```bash
python scripts/arrange_images.py inputs/nail_texture.png -a1 annotations/svg_from.json -a2 annotations/svg_to.json --width 1024 --height 1024
```
`--width`、`--height`はそれぞれ`-w`、`-h`と書くこともできます。


いずれの方法を使用した場合も、下に敷く画像と合成した時の解像度は変更されません。この画像の解像度は下に敷く画像の解像度と同じになります。
変更されるのは透過画像の解像度と自動作成されるマスク画像の解像度です。

### その他使用可能なオプションを確認する
```
python scripts/arrange_images.py --help
```