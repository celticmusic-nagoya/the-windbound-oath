# Raider Android表示修正

基準main: `e3565b68acc581759d24c7f6154cdeb51d58f049`
作業ブランチ: `work/codex-raider-mobile-layout`

## 原因

- 横画面のboss boxは高さ最低440px。高さ260pxの実表示領域でtop=-185pxとなる。
- 味方spriteはz-index:auto、bossは25。そのため縦画面で重なると味方が隠れる。
- party HUDはsprite高さからbottomを計算するため、高さ260pxではtopが負になる。
- 増援は通常戦闘由来の固定スロット。狭い画面では味方や他の敵の占有範囲を考慮しない。

## 修正

独立CSSでRaiderの縦画面／高さ520px以下の横画面だけslotを定義。
縦画面はbossを上段、partyを下段左、増援2体を右の別段へ配置。
横画面はpartyを左、bossを右、増援を右下の別列へ配置。
味方spriteはbossより手前に描画。動作中の既存z-index・WAAPI・keyframesは維持。
BattlePartyLayoutはRaiderだけ狭い横画面で表示高さを40vh以内に、縦画面の横幅を31vw以内に収める。
party HUDは既存の計算によりsprite位置へ追従し、boss HUDは独立したまま。

低い横画面ではCOMMANDのlegacy align-content:centerによってcloseボタンがscroll領域上端の外へ出たため、startへ修正。色・半透明・コマンド・操作ロジックは維持。

**PC巨大表示は変更なし**。1280×720のboss boxは537.6×504px。
スマホでは画面内に収めるためbossの表示寸法と位置を調整。旧440px最低高さを維持すると実機の問題が解消できないため、今回のユーザー依頼に沿ってviewportに合わせた。
HP1250、phase >820 / >400 / <=400、画像、actor state、戦闘数式、motion distance/duration/easing、フィールドとcameraは変更なし。

## 検証

```
python3 -m http.server 8765
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python3 tests/battle/raider_mobile_layout.py
```

- 360×640、390×844、844×390、844×260、1280×720、1920×1080: PASS。
- mobileは全actor/HUD/add boxがviewport内、party/HUDと敵が交差しない、増援同士が交差しない。
- 回転時にinline HUD位置を再計算することを確認。
- 全6サイズでCOMMANDのtouch開閉、DEV kill→boss KO画像→Victory確認。
- 390×844で実際のAidan/Fiona攻撃→敵ターン、一閃＋防御→次ターン完了。
- JS例外0、HTTP error（404含む）0、console error0。
- 既存 `tests/moss/m4_e2e.py`: exit 0、森A1→A2→A3、結界条件、Lou→祭壇導線、errors []。
- `tools/moss/check_assets.py`: 0 error / 13既存warning。
- JS syntax / git diff --check: PASS。

Chromiumのviewport・touch emulationによる確認。Android実機での描画やbrowser chromeの変化は作者PLAYER QAが必要。
画像・生成マップ・フィールド・Battle数式は無変更。main統合・本番Pages公開は未実施。

## 作者承認後のmain統合（2026-10-11）

最新main `09142636a86a9048b23acf5ed26b6e71633b42e1` を基準に
`work/codex-raider-mobile-integration` へ変更を移植。indexの限定差分も作者が承認済み。
元の共有ブランチは保持し、history rewrite / force pushは行わない。

- 最新main上で6画面のviewportテスト: exit 0、404 / JS exception / console error 0。
- 最新mainの既存 `tests/battle/hit_sync.py`: exit 0、FAILS 0。一時fixtureの素材はテストが復元し、img/のgit差分0。
- fixture復元後に390×844の攻撃／一閃／防御／KO／Victoryを単独再確認。
- check_assets: 0 error / 13既存warning。旧embedded・旧Lou・番号asset参照0。
- フィールド・生成マップ・正式画像・BattleMotion実装の差分0。
- 旧m4-e2e.logはe3565b6基準の前回結果。今回はフィールド変更がないため最新mainで再実行していない。

今後、危険でなくClaudeの作業と干渉しない変更のmain pushは作者が包括承認済み。
Pages設定は変更せず、既存のmain公開フローへ委ねる。
