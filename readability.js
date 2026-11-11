/* Safety: pressing Esc anywhere triggers Quick Exit, same as the Quick Exit button. */
(function () {
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape' && e.key !== 'Esc') return;
    if (typeof window.quickExit === 'function') { window.quickExit(); }
    else { window.location.replace('https://www.google.com'); }
  });
}());
