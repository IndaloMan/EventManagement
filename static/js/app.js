/* EventManagement — app JS */

// Light/dark theme toggle
(function() {
    var btn = document.getElementById('themeToggleBtn');
    if (!btn) return;
    var isLight = localStorage.getItem('sb_theme') === 'light';
    function applyTheme(light) {
        if (light) {
            document.documentElement.classList.add('light-theme');
            localStorage.setItem('sb_theme', 'light');
            btn.textContent = '☽';
            btn.style.color = '#1C3A6B';
        } else {
            document.documentElement.classList.remove('light-theme');
            localStorage.setItem('sb_theme', 'dark');
            btn.textContent = '☀';
            btn.style.color = '#FF9F0A';
        }
    }
    applyTheme(isLight);
    btn.addEventListener('click', function() {
        isLight = !isLight;
        applyTheme(isLight);
    });
})();

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

// Hamburger nav toggle
(function() {
    var t = document.getElementById('navToggle');
    if (t) t.addEventListener('click', function() {
        document.getElementById('navLinks').classList.toggle('open');
    });
    document.addEventListener('click', function(e) {
        var nav = document.getElementById('navLinks');
        if (nav && !nav.contains(e.target) && e.target !== t) {
            nav.classList.remove('open');
        }
    });
})();

// Collapsible cards
document.querySelectorAll('.card-header').forEach(function(header) {
    header.addEventListener('click', function() {
        this.closest('.card').classList.toggle('expanded');
    });
});
