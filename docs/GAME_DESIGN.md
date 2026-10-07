# GAME_DESIGN.md

# THE WINDBOUND OATH
## Mionn na Gaoithe

## High concept
A Celtic-flavored orthodox fantasy JRPG set on the continent of アルヴェリア.
The ancient Rune Civilization manipulated wind, fire, water, earth, light, shadow, and life through runes.

Public history says a demon king tried to destroy the world and heroes sealed him.
The deeper truth is that the demon king may have been resisting or sealing an entity from outside the world, and the heroes misunderstood him.
The later true threat is 「虚無」, an outside-world force that consumes life and magic.

Core emotional theme:
「守れなかった者たちが、今度こそ誰かを守る」

Tagline:
「失った故郷。残された仲間。そして、風だけが知っていた真実。」

## Core pillars
1. Readable classic JRPG exploration and turn-based combat.
2. Celtic/nature/rune atmosphere rather than generic mobile-fantasy gloss.
3. A party built around people who failed to protect something and choose to protect again.
4. Compact but meaningful exploration: towns, side quests, hidden routes, chests, character events.
5. Battle readability: clear formation, compact UI, strong contact motion, distinct resources.
6. Systems that can scale from ordinary 4-person battles to multi-party fortress defense.

## Main cast roles
| Character | Role | Core identity |
|---|---|---|
| Aidan | physical swordsman | TP, close-range techniques, Oathblade |
| Fiona | healer/support | healing, life, plants, wind |
| Liam | thief/explorer | SPD, CRI, steal, scouting |
| Morwen | black mage | MAG, shadow/runes, Resonance 0–3 |
| Dwarf (TBD) | tank/blacksmith | cover, provoke, BREAK, forging |
| Dancer (TBD) | buff/debuff | DANCE CHAIN, action-order control |
| Lou | support fairy | FAIRY BLESSING, global support |

## Battle resources
### TP
Personal resource, max 100.
Start: 0.
Normal attack: +15.
Defend: +10.
一閃: -30.

### RUNE
Shared party resource, max 100.
Used for major rune/Oathblade/combination actions.
Keep it conceptually distinct from TP.

### Future systems
- BREAK gauge for later bosses.
- Morwen Resonance 0–3.
- DANCE CHAIN.
- Combination techniques.
- Lou's FAIRY BLESSING.

## Encounter types
- NORMAL
- PREEMPTIVE STRIKE: current concept RUNE +20.
- BACK ATTACK: enemy acts first.
Field-symbol direction/contact should eventually determine encounter type.
Bosses do not randomly receive back attacks.

## Party structure
Six controllable characters.
Four active in ordinary combat, two reserve.
All recruited reserves receive 100% EXP.
Lou is a separate support slot.

Later story architecture must support simultaneous Party A/B/C with independent map position/state and free switching in selected events.

## Fortress-defense signature sequence
A future large-scale defense can split the roster into three parties:
- main gate
- walls/flank
- underground/rune device

Switching is strategic, not real-time twitch play.
Enemy advance can be turn/step/event based.
Potential strategic actions:
- dwarf repairs gate
- Liam scouts
- Morwen seals rune transfer
- dancer buffs NPC soldiers
- Fiona heals defenders
- Aidan rallies
- Lou supports all parties globally

## Lou progression
Lou's fairy sanctuary/community was attacked by black-purple corrupted monsters.
Some companions died; others fled. Lou does not know how many survived.
Her journey includes finding named survivors.
Rescues unlock FAIRY BLESSING abilities.
Some survivors are mandatory; others optional.
Fairies sense the Void earlier than humans, so their trail also reveals world mystery.

## Progression
Level cap 50.
Story clear naturally around 35–40.
Completionists can reach 50.
Avoid forced grinding.
Prologue target around LV3 for Aidan/Fiona.

Core stats:
HP / MP / ATK / DEF / MAG / SPD / CRI / EVA

CRI/EVA should lean more heavily on gear, skills, and events.

## Prologue
Title: 「風が止んだ夜」
Target: 15–25 minutes.

Sequence:
1. Title
2. peaceful Lind Village
3. Aidan's house
4. training ground
5. Fiona
6. movement/interact/menu tutorial
7. wooden dummy battle
8. Fiona joins and heals; life rune flashes
9. sunset hill
10. night; wind and BGM stop
11. village attacked
12. find Fiona
13. burning village
14. two abnormal goblins
15. royal knights
16. flee north/river
17. collapse/fall
18. Moss Forest
19. ancient stone reacts to Fiona
20. goblins surround; Aidan loses weapon
21. Lou appears
22. ancient altar
23. 誓いの剣 calls Aidan
24. Goblin Raider
25. aftermath / Lou formally joins
26. dawn
27. Arthur's Fort
28. PROLOGUE END

## Later broad route
Chapter 1: capital.
Chapter 2: Elfen forest / Griffon.
Interlude: Morwen.
Chapter 3: Druid ruins / stone guardian.
Details beyond confirmed material should remain flexible.

## Presentation
Palette direction:
- #101820
- #17372f
- #e9dfc7
- #c5a45b
- #f2eee3

Typography direction:
- Cinzel
- Cormorant Garamond
- Noto Serif JP
- Noto Sans JP

Reference game viewport: 1280×720, but layout must be responsive.

Dialogue portraits: painterly anime.
Field: polished pixel art.
Battle: polished standalone sprites/assets.
Specials: portrait cut-ins + effects.

## UX
Main menu direction:
PARTY / ITEM / EQUIPMENT / SKILL / STATUS / SAVE / SETTINGS

Quest journal:
- メインクエスト
- サブクエスト

Objective notifications are transient, not permanent HUD clutter.

## Content constraints
Do not convert Fiona into an elf/fairy.
Do not scale Lou like a normal child/human.
Do not rename 誓いの剣.
Do not replace final standalone art with composite-sheet crops.
Do not casually rebalance the approved Goblin Raider encounter.
