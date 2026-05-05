/* VIP Promotions — minimal JS */

// Auto-dismiss flash messages after 5 seconds
document.querySelectorAll('.flash').forEach(function(el) {
    setTimeout(function() {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.3s';
        setTimeout(function() { el.remove(); }, 300);
    }, 5000);
});

// Dirty form tracking — save button starts muted, goes green on change
(function() {
    var dirty = false;
    document.querySelectorAll('form[data-track-changes]').forEach(function(form) {
        var btn = form.querySelector('button[type="submit"]');
        if (!btn) return;
        btn.style.opacity = '0.45';
        btn.setAttribute('data-original-class', btn.className);
        function markDirty() {
            if (dirty) return;
            dirty = true;
            btn.style.opacity = '1';
            btn.classList.remove('btn-surface');
            btn.classList.add('btn-success');
        }
        form.querySelectorAll('input, select, textarea').forEach(function(el) {
            el.addEventListener('input', markDirty);
            el.addEventListener('change', markDirty);
        });
        form.addEventListener('submit', function() { dirty = false; });
    });
    window.addEventListener('beforeunload', function(e) {
        if (dirty) { e.preventDefault(); e.returnValue = ''; }
    });
})();
