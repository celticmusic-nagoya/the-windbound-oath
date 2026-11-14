'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const combat=fs.readFileSync('js/prologue-combat.js','utf8'),loading=fs.readFileSync('js/battle-loading.js','utf8'),html=fs.readFileSync('index.html','utf8'),screen=fs.readFileSync('js/gameover-screen.js','utf8');
test('Raider never rewinds or rematches after party wipe',()=>{assert.doesNotMatch(combat,/時間を巻き戻す|BattleLoading\.rematch|startRaiderBattle\(\)\)/);assert.doesNotMatch(loading,/function rematch\(|rematch,cancel/);assert.match(combat,/if\(rbHP<=0&&rbFHP<=0\)/);assert.match(combat,/GameOverScreen\?\.show/)});
test('normal combat only triggers GAME OVER on full party wipe at attack stage',()=>{assert.match(combat,/aahp<=0&&\(normalFHP<=0\|\|!activeAlly/);assert.match(combat,/GameOverPolicy\?\.gameOverEnabled\(\{storyStage\}\)/)});
test('single Raider KO can recover without GAME OVER',()=>{assert.match(combat,/if\(rbHP<=0\|\|rbFHP<=0\)\{log\('raider','態勢を立て直した/)});
test('overlay, CSS and title-return boundary are loaded',()=>{assert.match(html,/src="js\/gameover-policy\.js/);assert.match(html,/src="js\/gameover-screen\.js/);assert.match(html,/href="css\/gameover-screen\.css/);assert.match(screen,/タイトルでセーブを選んで再開/);assert.match(fs.readFileSync('js/title-screen.js','utf8'),/returnToTitle/)});
