# DEV-CAMERA-01 — 開発専用3Dビューア

**用途:** THE WINDBOUND OATH の3DアセットQA専用。ゲーム本体、正式CG、セーブデータには接続しない。

## Android / PCでの起動

1. GitHub Actions の `aidan-roof-candidate-qa.yml` を対象ブランチで実行し、成功した `aidan-dev-camera-glb-v2` Artifactをダウンロードする。
2. ZIPを展開し、`aidan_house_master_v2.glb` を端末に保存する。
3. ブラウザで `tools/dev-camera/index.html` のHTTPS配信URLを開く（開発検証用の外部配信サービスを使用する場合は正式公開ではないことに注意）。
4. 上部のファイル選択でGLBを選ぶ。モデル名と「読込完了」が出ることを確認する。
5. 1本指ドラッグで回転、2本指でズーム/パン。27°俯瞰・正面・背面・左右・真上・全体表示を試す。

GLBは現在、手動ファイル選択で読み込む。GitHub ActionsのArtifactは公開サイトの恒久的なモデルURLではない。

## QAゲート

- G1: 既存正本と本番コードに変更なし
- G2: 建物の美術品質は独立判定。GLB出力成功では合格にならない
- G3: Actions `dev_camera_glb` でGLB magic/version/length、mesh数、SHA-256を確認
- G4: Android Chrome実機の読込、回転、ズーム、全プリセット、レイヤー切替、メモリ/フレームレートは未実施。端末で結果を記録する

## 既知の制約

- three.js 0.170.0 をCDNから読み込むため、初回アクセス時はネットワークが必要
- 現在のビューアは開発専用。ゲーム内の自由カメラ機能ではない
- v2モデルは候補段階。PBR材質・UV・美術QAは未完了
- GitHub Actions Artifactは7日間保持
