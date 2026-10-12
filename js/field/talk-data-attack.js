/* リルド村襲撃 (stage 5-8) の会話。以前は index.html の say('...') 直書きだったものを FieldTalk のテーブルへ移したもの。
 * 進行(attackStep / northPhase / 戦闘)は従来どおり index.html が持ち、ここは「何を言うか」と「立つフラグ」だけを持つ。
 * 各 npc は1シーンにつき1テーブル（呼び出し側が状況で id を選ぶ）。立つフラグ: atk_started / atk_rescued / atk_fiona_found / atk_knight_met / atk_escaped
 * （enterBurningVillage で一旦すべて下ろす。DEV ジャンプ後の再生も同じ状態から始まる）。 escapeLines = 脱出シーン(#escapeScene)の文言。 */
const ATTACK_ESCAPE_LINES = Object.freeze([
  'エイダン「まだ村に、助けを待ってる人が……！」',
  'フィオナ「エイダン……！　今は生き延びなきゃ。お願い……！」',
  'フィオナ「……行こう、エイダン。」',
  '二人は炎上する村を背に、川沿いの細い退路を走った。',
  '背後で角笛が鳴る。黒紫の光をまとった魔物たちが追ってくる。',
  'エイダン「橋は――駄目だ。向こうにもいる！」',
  'フィオナ「こっち！　川下に獣道があるはず！」',
  '地面が大きく揺れ、焼けた崖の縁が崩れた。',
  'エイダン「フィオナ！」',
  '二人の足元が崩れ、そのまま暗い谷へ落ちていった――。'
]);
const _atk = (npc, lines, set) => ({npc, entries: [{id: npc + '_1', priority: 10, mode: 'cycle', when: {stage: [5, 8]}, lines: [set ? {pages: [].concat(lines), set} : lines]}]});
// 目的 / 通知 / バナー / ポップ: 襲撃中に画面へ出る短い文言（キー参照: index.html の atkObj / atkNotice / atkBanner）
const ATTACK_TEXT = Object.freeze({
  obj: Object.freeze({find_fiona: '村の広場へ向かい、フィオナを探そう', talk_fiona: 'フィオナに話しかけよう', go_north: 'フィオナとともに村の北側へ向かおう',
    meet_knight: '村の北側で王国騎士と合流しよう', to_escape: '北の退路へ向かい、リルド村を脱出しよう', escape: 'フィオナとともに村から脱出しよう'}),
  notice: Object.freeze({mother_saved: '母娘は安全な道へ逃げていった', found_fiona: 'フィオナを見つけた', fiona_joined: 'フィオナが再び同行した', tainted_down: '異常化ゴブリンを退けた',
    talk_knight_first: '先に王国騎士と話そう'}),
  banner: Object.freeze({gob1: '母親が娘を庇っている――ゴブリンを退けよう！', gob: '魔物が立ちはだかった！', danger: '風が、止まった。'}),
  pop: Object.freeze({meet_knight: 'MAIN OBJECTIVE：村の北側で王国騎士と合流しよう'})
});
window.TalkDataAttack = Object.freeze({
  text: ATTACK_TEXT,
  escapeLines: ATTACK_ESCAPE_LINES,
  flags: Object.freeze(['atk_started', 'atk_rescued', 'atk_fiona_found', 'atk_knight_met', 'atk_escaped']),
  tables: [
    _atk('atk_enter', ['エイダン「広場で合流する約束だ……フィオナ、無事でいてくれ。」'], {atk_started: true}),
    _atk('atk_old', ['老人「うぅ……広場の方へ、魔物が……。娘さんが、一人で追っていった……」']),
    _atk('atk_mother_before', ['母親「この子だけでも……！」']),
    _atk('atk_mother_after', ['母親「本当にありがとう。娘と一緒に逃げます！」']),
    _atk('atk_child', ['子ども「お姉ちゃんが治してくれたの……それから、あっちへ走っていった……」']),
    _atk('atk_gob2_wait', ['エイダン「先にあの母娘を助けないと！」']),
    _atk('atk_rescued', ['母親「ありがとう……！　さあ、逃げましょう！」', 'エイダン「広場へ……フィオナを探さないと。」'], {atk_rescued: true}),
    _atk('atk_fiona', ['フィオナ「エイダン……！ よかった。さっきの人たちは逃がせた。でも、この魔物たち……普通じゃない。」'], {atk_fiona_found: true}),
    _atk('atk_knight_first', ['王国騎士「生存者か！　北門はもう保たない。川沿いの退路から森へ抜けろ！　我々がここを食い止める！」'], {atk_knight_met: true}),
    _atk('atk_knight_again', ['王国騎士「急げ！　この数は普通じゃない……黒いルーンに近づくな！」']),
    {npc: 'scene_escape', entries: [{id: 'scene_escape_1', priority: 1, mode: 'cycle', lines: [{pages: ATTACK_ESCAPE_LINES.slice(), set: {atk_escaped: true}}]}]}
  ]
});
