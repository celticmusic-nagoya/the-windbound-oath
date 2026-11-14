'use strict';
const assert=require('node:assert/strict');
const {test}=require('node:test');
const {gameOverEnabled}=require('../js/gameover-policy.js');
test('safe before village attack',()=>{for(let s=0;s<5;s++)assert.equal(gameOverEnabled({storyStage:s}),false)});
test('enabled from village attack through prologue end',()=>{for(let s=5;s<=15;s++)assert.equal(gameOverEnabled({storyStage:s}),true)});
test('malformed and legacy missing stage fail closed',()=>{for(const p of [null,{}, {storyStage:'5'},{storyStage:-1},{storyStage:NaN},{storyStage:16}])assert.equal(gameOverEnabled(p),false)});
