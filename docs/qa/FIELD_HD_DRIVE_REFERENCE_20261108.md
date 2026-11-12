# FIELD-HD-OFFICIAL-MATCH-02 — Google Drive正本参照登録

- 参照ZIP: [THE_WINDBOUND_OATH_ALL_CHARACTER_REFERENCES.zip](https://drive.google.com/file/d/16t_kztYlobObrICfuOkmHuHrcGo92e1X/view)
- Drive file ID: `16t_kztYlobObrICfuOkmHuHrcGo92e1X`
- Drive確認日時: 2026-11-08
- Driveメタデータ: `application/zip` / 245497478 bytes / 2026-11-08更新。
- GitHub Actions生成元: [run 42460725583](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/42460725583)
- ZIP内は採用原本・候補・参考・NPC・敵画像が混在。**ZIPに入っているだけでは正式採用とは限らない**。
- ZIPの元ファイルは原本のまま、MANIFEST_SHA256.jsonを参照して個別SHA-256を照合する。

## 作業状況
- Driveファイルの存在・名前・容量・アクセス: **CONFIRMED**。
- ZIPバイト取得: Google Drive連携で取得済み。ただしこの実行ではローカル画像展開環境がエラーとなり、画像の目視照合は**NOT_RUN**。
- 正式イラストとの髪型・顔・衣装・装備照合: **NOT_RUN**。
- v5.3正式採用: **BLOCKED**（ディレクターから不一致指摘）。
- 独立透過RGBA/4方向/統一anchor/32-48px QA/Android実機: **NOT_RUN**。

## 次工程
1. ZIP展開・MANIFESTのSHA-256検証・採用原本と候補の仕分け。
2. モルウェンv3（学院首席18歳・研究院協力生、ニーソックス、正式髪型）、セレナv1、ブラムを優先し、エイダン・フィオナ・エマ・ルー・リアム・敵・NPCを順に公式画像照合。
3. 公式照合済みの個別キャラだけ独立透過RGBA 4方向を新規制作し、候補ディレクトリで技術QA。
4. 視覚QAとAndroid実機QAの後に本番登録。原本は上書きしない。
