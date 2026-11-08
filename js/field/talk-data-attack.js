/* リルド村襲撃 (stage 5-8) の会話。以前は index.html の say('...') 直書きだったものを FieldTalk のテーブルへ移したもの。
 * 進行(attackStep / northPhase / 戦闘)は従来どおり index.html が持ち、ここは「何を言うか」と「立つフラグ」だけを持つ。
 * 各 npc は1シーンにつき1テーブル（呼び出し側が状況で id を選ぶ）。立つフラグ: atk_started / atk_rescued / atk_fiona_found / atk_knight_met / atk_escaped
 * （enterBurningVillage で一旦すべて下ろす。DEV ジャンプ後の再生も同じ状態から始まる）。 escapeLines = 脱出シーン(#escapeScene)の文言。 */
const ATTACK_ESCAPE_LINES = Object.freeze([
  'エイダン「まだ村に、助けを待ってる人が……！」',
  'フィオナ「エマおばあちゃんが……まだ見つからないの……！」',
  'エイダン「……必ず探す。でも今は、みんなを逃がさないと！」',
  '兵士「ここはもう保たん！　住民の避難は我々が引き受ける。二人とも退け！」',
  '背後で角笛が鳴る。黒紫の光をまとった魔物たちが追ってくる。',
  'エイダン「橋は――駄目だ。向こうにもいる！」',
  'フィオナ「エイダン！ もう逃げ道が……！」',
  'エイダン「……川だ！」',
  'フィオナ「えっ！？」',
  'エイダン「飛ぶぞ！ 手を離すな！」',
  'フィオナ「……うん！」',
  '二人は手を取り合い、川へ身を投げた。激しい流れが二人を下流へ運んでいく――。'
]);
const ATTACK_ESCAPE_PORTRAITS = Object.freeze([{"char":"aidan","face":"worried","side":"left"},{"char":"fiona","face":"worried","side":"right"},{"char":"aidan","face":"determined","side":"left"},{"char":null},{"char":null},{"char":"aidan","face":"surprised","side":"left"},{"char":"fiona","face":"worried","side":"right"},{"char":"aidan","face":"determined","side":"left"},{"char":"fiona","face":"surprised","side":"right"},{"char":"aidan","face":"determined","side":"left"},{"char":"fiona","face":"determined","side":"right"},{"char":null}]);
const _atk = (npc, lines, set, portraits) => ({npc, entries: [{id: npc + '_1', priority: 10, mode: 'cycle', when: {stage: [5, 8]}, lines: [set || portraits ? {pages: [].concat(lines), ...(set ? {set} : {}), ...(portraits ? {portraits} : {})} : lines]}]});
// 目的 / 通知 / バナー / ポップ: 襲撃中に画面へ出る短い文言（キー参照: index.html の atkObj / atkNotice / atkBanner）
const ATTACK_TEXT = Object.freeze({
  obj: Object.freeze({find_fiona: '村の広場へ向かい、フィオナを探そう', talk_fiona: 'フィオナに話しかけよう', go_north: 'フィオナとともに騎士のもとへ向かおう',
    meet_knight: '村の北側で王国騎士と合流しよう', to_escape: '騎士の指示に従い、川沿いの退路へ向かおう', escape: 'フィオナとともに川へ飛び込み、村から脱出しよう'}),
  notice: Object.freeze({mother_saved: '母娘は安全な道へ逃げていった', found_fiona: 'フィオナを見つけた', fiona_joined: 'フィオナが再び同行した', tainted_down: '異常化ゴブリンを退けた',
    talk_knight_first: '先に王国騎士と話そう'}),
  banner: Object.freeze({gob1: '母親が娘を庇っている――ゴブリンを退けよう！', gob: '魔物が立ちはだかった！', danger: '風が、止まった。'}),
  pop: Object.freeze({meet_knight: 'MAIN OBJECTIVE：村の北側で王国騎士と合流しよう'})
});
window.TalkDataAttack = Object.freeze({
  text: ATTACK_TEXT,
  escapeLines: ATTACK_ESCAPE_LINES,
  escapePortraits: ATTACK_ESCAPE_PORTRAITS,
  flags: Object.freeze(['atk_started', 'atk_rescued', 'atk_fiona_found', 'atk_knight_met', 'atk_escaped']),
  tables: [
    _atk('atk_enter', ['エイダン「広場で合流する約束だ……フィオナ、無事でいてくれ。」'], {atk_started: true},[{"char":"aidan","face":"worried","side":"left"}]),
    _atk('atk_old', ['老人「うぅ……広場の方へ、魔物が……。娘さんが、一人で追っていった……」']),
    _atk('atk_mother_before', ['母親「この子だけでも……！」']),
    _atk('atk_mother_after', ['母親「本当にありがとう。娘と一緒に逃げます！」']),
    _atk('atk_child', ['子ども「お姉ちゃんが治してくれたの……それから、あっちへ走っていった……」']),
    _atk('atk_gob2_wait', ['エイダン「先にあの母娘を助けないと！」'],undefined,[{"char":"aidan","face":"normal","side":"left"}]),
    _atk('atk_rescued', ['母親「ありがとう……！　さあ、逃げましょう！」', 'エイダン「広場へ……フィオナを探さないと。」'], {atk_rescued: true},[{"char":null},{"char":"aidan","face":"worried","side":"left"}]),
    _atk('atk_fiona', ['フィオナ「エイダン……！ よかった。さっきの人たちは逃がせた。でも、エマおばあちゃんが見つからないの……。この魔物たちも、普通じゃない。」'], {atk_fiona_found: true},[{"char":"fiona","face":"worried","side":"right"}]),
    _atk('atk_knight_first', ['王国騎士「生存者か！　避難者は我々が守る！　ここはもう保たん、川沿いへ退け！　我々が食い止める！」'], {atk_knight_met: true}),
    _atk('atk_knight_again', ['王国騎士「急げ！　黒いルーンをまとった魔物には近づくな！　住民は我々に任せろ！」']),
    {npc: 'scene_escape', entries: [{id: 'scene_escape_1', priority: 1, mode: 'cycle', lines: [{portraits:ATTACK_ESCAPE_PORTRAITS,pages: ATTACK_ESCAPE_LINES.slice(), set: {atk_escaped: true}}]}]}
  ]
});
