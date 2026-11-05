# PLAYER-WALK-ARM-02-QA — independent A/B/C visual assessment

**Verdict: PASS for C(PR144) at the tested DEV conditions, with the lining/hold residuals disclosed below.** This is a visual recommendation to proceed to the director's final appearance/Android decision, **not formal adoption, production registration, main merge or Pages authorization**.

Fixed PR144 head: `95e5563032095790e7a6887c74fa466f44a0bead`. Production reference main `74d0401`. A=production01→05→02→grounded06; B=PR14201/02 substitutions; C=PR14405/02 substitutions,01/06 retained fromproduction. Conditions90world/.300s percycle,300world/sreference,playback1x,bob25%,no whole-frame06offset. The reviewer read AGENTS/README but performed independent source/pixel/visual checks instead of accepting self-QA or arm-correlation scores.

No repository/original/candidate art, production source, browser or SAVE edits/runs by this reviewer. Parent owns the DEV implementation and serial browser tests. This is not the final exact feature-head code QA. Latest instruction is QA-only: no main/Pages/PR142/PR143 changes are approved.

## Independent evidence and viewing method

- Opened original/candidate source PNGs read-only, generated own native A/B/C05/02 plate, full4-pose strips, precise four boundary plates and game-scale/DPR illustrations.
- Reviewed own exactnative boundary images for01→05,05→02,02→06,06→01, including shoulder/elbow/wrist,02innercape/white lining and05cuff-bottom wrinkle.
- Reviewed parent actual paused truefieldscale PC/portrait C05captures, where real imagecanvas is128×80CSSpx, without preview enlargement.
- Independently decoded the actual parent portrait A/B/C1x browser WebM into chronological frames: Astart14.0s,B16.3s,C18.9s,about1s/condition,25fpssource(25/24/24decoded frames,more than3cycles each). Inspected the timeordered,unrescaled sprite crops alongside the fullpaused screenshots. Captions and rawURL/height records identifyA/B/C andfieldscale. This is **chronological rendered-frame inspection of parent recordings**, not a claim to have conducted own browser run, actual Android viewing or an unmeasured subjective live playtest.
- Parent root also recorded enlargedDEV loops; own initialPC Cloop13.0s onward was inspected as a separate enlargement/continuity check. Root actualtelemetry shows.300s decodedcycle andspatialheight80 forfieldmode. No instruction to treat nonzero liningmetrics as automatic failure was used.

AuthorMP4 was used only as reference: its generator additionally scales the DPR2.625render by2×nearest-neighbor beforeencoding. It is a60fps/.900s pose/timingillustration, not literal1xfield-size evidence. Actual root browser field captures were therefore used for the smallwrinkle criterion.

## Seven requested criteria

|criterion|verdict|independent finding|
|---|---|---|
|1.06→01 same asproduction|PASS|C keeps both originalgrounded06 andoriginal01. Their sourcepixel pair andallchosenROI differences equalA exactly;actualfieldchronology does not showB's new lowered01return.|
|2.05→02white lining reduced versusB|PASS, residual|TightC02patch preserves materiallymoreoriginal02lining. OwnliningROI MAE50.72(B)→43.42(C),versusA30.79. Native difference still visible; inactual1xfieldchronology it is a small localclothingdetail rather than a dominantpatchflash. NotclaimedperfectoridenticaltoA.|
|3.New01→05arm/sleeve step|PASS at testedscale|C05now lowers theleftglove;newmotion is visible enlarged. Shoulder/sleeve/forearmremainconnected. At actualfieldsize thechange reads as a smallarm movement,withoutan obviousdetachedsleeve orwholebodyjump.|
|4.02→06unnatural hold|PASS, briefnearhold disclosed|A short near-extremeleftarm interval remains,similarlytimed to theunchangedotherarm. Thewholecharacter stilladvances throughdistinctposes;actual1xframes do not showa conspicuous newfrozenjoint. This isnotproof of3Danatomicalgait.|
|5.C05cuff-bottomcloakwrinkle atfieldsize|PASS, visible enlarged|A smallnewfold/trimdetail belowthecuff isvisible in ownnativecomparison. It isnotintrusive intrue128×80CSScanvas screenshots/timeorderedfieldcapture. No needforfurtherassetrepair isestablished merelyfromthatnonzero detail.|
|6.Alljoints andcompositeedges|PASS forviewedevidence|No cleardetachedshoulder/elbow/wrist,doublelimboutline,rectangularmatte orabruptcut isvisible inthenative/fieldplates. Donorarmmaterialdoesnotimplyunchangedallcloth;remaininglining differencesstaylisted.|
|7.Feet/anchor/sourceSHA|PASS|BothCimages retainalllegs/shoes y≥870andheadsy<560 exactly;sourcecanvas/mode/alphaboundsunchanged. Maininput01/05/02/grounded06 bytechecked;C01/06remainunchanged references;B142PNGinputsbytecheckedagainstfixedPR142head.|

## Exact source and edit-scope checks

C05 SHA `6c857b4cbf1459df48ecd305b41ffa7f1b7b98a1458b6d2243a8c50c94e17bad`.
C02 SHA `614bdeffb8c09b3dbb7e0b688cea21efdfc7b68ccdeea0ddf53694f0bc13824f`.
Both actual2048×1280 RGBA.

|candidate|changedpixels|changedbbox(exclusive right/bottom)|outsidecore|outsidecore+3px|
|---|---:|---|---:|---:|
|C05|18,809|[1216,624,1337,849)|1,727|0|
|C02|20,938|[1216,615,1352,851)|1,639|0|

Provided edit_envelope matches independently computed3pxbinarydilation ofedit_core exactly. Alpha-channel changedpixel counts99/690 remaininside thatenvelope; do not claimallalpha unchanged. Overallalpha bounds remainunchanged. Enclosedalpha200holes05=3and02=844 matchtheirproductioninputs. Both heads<560,legs≥870andprotectedotherarm/centralbodyx<1150 arepixel-identical. Every4productioninput isbyte-equal to main74d0401. AllB142sourcecandidate PNGs arebyte-equal toPR142 `01511ee1a8f0b198ef185900b2c0ec010ac20262`.

Independent donor-core comparisons:
- C05glove ROI[1270,780,1310,805) equals A02shift(−1,−1),0RGBA differences.
- C02glove ROI[1290,745,1320,780) equals groundedA06shift(+7,+9),0RGBA differences.

These are genuine retained handdesigns and exacttranslations,not fabricatednewgloveart. They do not independently certify natural timing or permit treating gloveimageheight as worlddepth/contact.

## Allfourboundary appearance metrics and interpretation

Own registered compositeRGB MAE(0..255),withsamefixedROIs as prior independentreview. These are **imageappearance differences,not handmotion/naturalnessscores**. GloveROI[1240,710,1360,825)includesnearbycloth;liningROI[1300,740,1390,855).

|edge|gloveA/B/C|liningA/B/C|visualmeaning|
|---|---|---|---|
|01→05|27.24/27.26/34.37|33.26/31.40/32.53|Cintroduces lowered05handmotion; liningdifference staysnearA.|
|05→02|35.59/59.02/54.93|30.79/50.72/43.42|CremovespartofthewideBpatch,whilearmraised/liningchange remainslargerthanA.|
|02→06|52.67/34.88/38.45|49.81/39.01/44.16|Cretains a briefnear-extremehandinterval,withoutfreezingwholepose.|
|06→01|50.54/56.62/50.54|40.38/47.00/40.38|CrestoresA's exactboundary;B's extra returndifference isgone.|

Protected oppositearm andchestROI metrics areidenticalA/B/C on allfour edges. C05→02lining is≈14.4%belowB but≈41%aboveA. These aremeaningfulresiduals todisclose,notautomaticvisualFAIL thresholds. Wholefieldview matters:the observedlocalCdetail isacceptablysmall at thetestsize/rate. The difference remainsreadable inenlargedinspection anddirectorcanstillpreferA'smaterialstability.

Thefour explicitplates are `own-edge-01-05-ABC.png`, `own-edge-05-02-ABC.png`, `own-edge-02-06-ABC.png`, `own-edge-06-01-ABC.png`. Native images are not forcedtoagreeviaregistrationwarpsorcroppedtoless-than-requiredgarmentregions. `own-05-cuff-wrinkle.png` isolates the newsmallC05detail; `own-native-05-02-ABC.png` and `own-cycle-arms-ABC.png` providecontext.

## Arm trajectory and wholecycle judgment, without correlation-only proof

The visible leftglove changes from production01's intermediate/downpose toC05'slowerpose,thenC02'sraisedpose,withgrounded06unchanged. In conjunctionwiththeunchangedotherarm, this reads as a moreopposed swinggrouping thanA's near-same01/05leftpose followedby thelow02pose. C02→06 retains a smallrelativeholdnear theupperextreme; it is not literallythe identicalwholeframe or a stalledanimation. C's01reference restores the established06→01return instead ofB's high→lowleftarmjump atwrap.

Donortranslation consistency is independentlyverified by pixel identity. Authorupdated4pointcorrelations are supplementary only:fourmanualhandlandmarks,projectionandchestregistration do notprove3Darmphase,forceorbiomechanics. No newcorrelationnumber wasusedas theverdict. The conclusion comesfrom scopedsourcepreservation,allfourboundaryviews andtimeorderedactual1xfieldrenderframes.

## Recommendation and limits

Recommend **C(PR144) as thepreferred candidate for the director's final appearance/Android decision**, keeping cycle90,bob25%,fullframeoffsetOFF,1x. ComparedwithB itrestores theproductionwrap andreduces the intrusiveinnerlining patch whilepreserving theimprovedopposed armgrouping. At thetestedactualfieldscale itsremaining05wrinkle and05→02liningchange are not sufficientreasons torequestanotherassetrevision. No newmandatoryvisualfix wasfound.

ThisPASS doesnotmeanzero liningdifference,perfectcontinuousanatomicalmotion,oractualAndroidPASS. The.300sloop isstill brisk;short02→06hold andlocalmaterialchangesremainexplicit. RealAndroidfinaltastejudgment andformaladoption arepending. Root'sfullregression/protection/feature-headcodeQA are separateevidence. LatestuserinstructionisQAonly:no productionregistration,mainmerge,PagesorPR142/143changes.

## Reproduction / provenance

Run `python analyze.py --repo <checkout> --out <analysisdir>` againstthefixedcandidateinputs. Itreads sourceart andwritesonlyanalysisoutputs(defaultfresh/tmp). `independent-arm02-metrics.json` includesexactSHA/maskchecks/allboundaryROIs.

`inspect_capture.py --video <parent portrait fieldscale WebM> --out <analysisdir> --clips A=14.0 B=16.3 C=18.9 --duration 1 --crop 117 218 185 289` reproduces the timeorderedactualfieldplatefor thisspecificcapture. Clipranges/provenance are in `actual-video-inspection.json`. Thecapture is25fps andresized;full-resolutiontruefieldpausedphotos werealsoinspected. Theactualframeplate isnotanartist-generatedGIForstaticresamplinganimation. `own-game-scale-ABC.png`is a separatestaticDPRillustrationandislabelledassuch,notanAndroidcapture.
