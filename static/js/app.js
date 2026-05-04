/* Marina Club Events — minimal JS */

// Auto-dismiss flash messages after 5 seconds
document.querySelectorAll('.flash').forEach(function(el) {
    setTimeout(function() {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.3s';
        setTimeout(function() { el.remove(); }, 300);
    }, 5000);
});
