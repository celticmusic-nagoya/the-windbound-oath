/* Wind classification only; story wind-stop hookup belongs to STEP 13.
 * Water and animal timelines never consult this flag. */
(function () {
  'use strict';
  let wind = true;
  function setWind(value) {
    wind = Boolean(value);
    const layer = document.getElementById('lindReviewLayer');
    if (layer) layer.dataset.wind = wind ? 'on' : 'off';
    return wind;
  }
  window.LindFieldEnvironment = Object.freeze({setWind,get wind(){return wind;}});
})();
