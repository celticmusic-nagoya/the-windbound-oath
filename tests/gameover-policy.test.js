'use strict';
const assert=require('node:assert/strict');
const {test}=require('node:test');
const {gameOverEnabled}=require('../js/gameover-policy.js');
test('safe before village attack',()=>{for(let s=0;s<5;s++)assert.equal(gameOverEnabled({storyStage:s}),false)});
test('enabled from village attack through prologue end',()=>{for(let s=5;s<=15;s++)assert.equal(gameOverEnabled({storyStage:s}),true)});
test('malformed and legacy missing stage fail closed',()=>{for(const p of [null,{}, {storyStage:'5'},{storyStage:-1},{storyStage:NaN},{storyStage:16}])assert.equal(gameOverEnabled(p),false)});

const {decideDefeat}=require('../js/gameover-policy.js');
test('one fallen ally is not a party wipe',()=>{assert.equal(decideDefeat({progress:{storyStage:10},activeHp:[0,35]}),'CONTINUE');assert.equal(decideDefeat({progress:{storyStage:10},activeHp:[50,0]}),'CONTINUE')});
test('pre-attack full wipe recovers, attack full wipe ends game',()=>{assert.equal(decideDefeat({progress:{storyStage:4},activeHp:[0,0]}),'RECOVER');assert.equal(decideDefeat({progress:{storyStage:5},activeHp:[0,0]}),'GAME_OVER')});
test('solo combat requires only the active ally to fall',()=>{assert.equal(decideDefeat({progress:{storyStage:3},activeHp:[0]}),'RECOVER');assert.equal(decideDefeat({progress:{storyStage:9},activeHp:[0]}),'GAME_OVER')});
test('Raider scripted rewind is explicitly preserved',()=>{assert.equal(decideDefeat({progress:{storyStage:12},activeHp:[0,0],raiderRewind:true}),'SCRIPTED_REWIND');assert.equal(decideDefeat({progress:{storyStage:12},activeHp:[0,0],raiderRewind:false}),'GAME_OVER')});
test('invalid HP input cannot trigger game over',()=>{for(const activeHp of [[],[NaN,0],[-1,0],null])assert.equal(decideDefeat({progress:{storyStage:12},activeHp}),'INVALID')});
