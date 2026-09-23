// ── NAV ──────────────────────────────────────────────────────
const nav        = document.getElementById('nav');
const navClose   = document.getElementById('navClose');
const hamburger  = document.getElementById('hamburger');
const mobOverlay = document.getElementById('mobOverlay');

function openNav() {
    nav.classList.add('open');
    hamburger.classList.add('open');
    if (mobOverlay) mobOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}
function closeNav() {
    nav.classList.remove('open');
    hamburger.classList.remove('open');
    if (mobOverlay) mobOverlay.classList.remove('open');
    document.body.style.overflow = '';
}

if (hamburger)  hamburger.addEventListener('click', openNav);
if (navClose)   navClose.addEventListener('click', closeNav);
if (mobOverlay) mobOverlay.addEventListener('click', closeNav);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeNav(); });

document.querySelectorAll('.nav .nav-link').forEach(a => {
    a.addEventListener('click', () => { if (window.innerWidth <= 768) closeNav(); });
});

document.querySelectorAll('.nav-drop').forEach(drop => {
    const link = drop.querySelector('.nav-link');
    if (!link) return;
    link.addEventListener('click', e => {
        if (window.innerWidth <= 768) {
            e.preventDefault();
            drop.classList.toggle('open');
        }
    });
});

// ── HEADER SCROLL ────────────────────────────────────────────
const header    = document.getElementById('header');
const backToTop = document.getElementById('backToTop');

function checkHeaderScroll() {
    if (header) {
        if (header.classList.contains('header-auto-hide')) {
            header.classList.toggle('scrolled', window.scrollY > 80);
        } else {
            header.classList.toggle('scrolled', window.scrollY > 40);
        }
    }
    if (backToTop) backToTop.style.display = window.scrollY > 400 ? 'flex' : 'none';
}

window.addEventListener('scroll', checkHeaderScroll, { passive: true });
checkHeaderScroll();

if (backToTop) backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// ── ALERTS ───────────────────────────────────────────────────
document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.alert').remove());
});

// ── HERO BACKGROUND SLIDER ───────────────────────────────────
const heroBgs  = document.querySelectorAll('.hero-bg-item');
const heroDots = document.querySelectorAll('.hero-dot');
let heroCur = 0;
let heroTimer = null;

function heroSlide(n) {
    heroBgs.forEach(b => b.classList.remove('active'));
    heroDots.forEach(d => d.classList.remove('active'));
    heroCur = (n + heroBgs.length) % heroBgs.length;
    if (heroBgs[heroCur])  heroBgs[heroCur].classList.add('active');
    if (heroDots[heroCur]) heroDots[heroCur].classList.add('active');
}

if (heroBgs.length > 1) {
    heroTimer = setInterval(() => heroSlide(heroCur + 1), 5500);
}

// ── PRODUCT TABS ─────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = btn.dataset.tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const pane = document.getElementById(target);
        if (pane) pane.classList.add('active');
    });
});

// ── CALCULATOR TABS ──────────────────────────────────────────
document.querySelectorAll('.calc-tab').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = btn.dataset.calc;
        document.querySelectorAll('.calc-tab').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.calc-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const panel = document.getElementById(target);
        if (panel) panel.classList.add('active');
    });
});

// ── STATS COUNTER ANIMATION ──────────────────────────────────
if ('IntersectionObserver' in window) {
    const statEls = document.querySelectorAll('.stat-text .num[data-target]');
    if (statEls.length) {
        const counterObs = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                const el     = entry.target;
                const target = parseInt(el.dataset.target, 10);
                const suffix = el.dataset.suffix || '';
                const dur    = 1600;
                let startTs  = null;

                function step(ts) {
                    if (!startTs) startTs = ts;
                    const progress = Math.min((ts - startTs) / dur, 1);
                    const ease     = 1 - Math.pow(1 - progress, 3);
                    el.textContent = Math.floor(ease * target) + suffix;
                    if (progress < 1) requestAnimationFrame(step);
                }
                requestAnimationFrame(step);
                counterObs.unobserve(el);
            });
        }, { threshold: 0.6 });
        statEls.forEach(el => counterObs.observe(el));
    }
}

// ── SCROLL REVEAL ────────────────────────────────────────────
if ('IntersectionObserver' in window) {
    const revealObs = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.style.opacity = '1';
                e.target.style.transform = 'translateY(0)';
                revealObs.unobserve(e.target);
            }
        });
    }, { threshold: 0.08 });

    document.querySelectorAll('.feature-card, .product-card, .news-card, .stat-item, .news-side-item, .partner-item').forEach((el, i) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(22px)';
        el.style.transition = `opacity .45s ease ${(i % 5) * 0.07}s, transform .45s ease ${(i % 5) * 0.07}s`;
        revealObs.observe(el);
    });
}

// ── MULTI-LANGUAGE TRANSLATOR ─────────────────────────────────
function getLangCookie(name) {
    const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? decodeURIComponent(v[2]) : null;
}

function setLangCookie(name, value, days) {
    let expires = "";
    if (days) {
        let d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + d.toUTCString();
    }
    const host = window.location.hostname;
    document.cookie = name + "=" + value + expires + "; path=/";
    if (host && host !== 'localhost' && host !== '127.0.0.1') {
        document.cookie = name + "=" + value + expires + "; path=/; domain=" + host;
    }
}

function updateActiveLangButtons(activeLang) {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === activeLang);
    });
}

function applySelectedLanguage(targetLang) {
    localStorage.setItem('site_lang', targetLang);
    updateActiveLangButtons(targetLang);

    if (targetLang === 'vi') {
        setLangCookie('googtrans', '', -1);
        document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + window.location.hostname;
        window.location.reload();
        return;
    }

    const transValue = '/vi/' + targetLang;
    setLangCookie('googtrans', transValue, 30);

    const combo = document.querySelector('.goog-te-combo');
    if (combo) {
        combo.value = targetLang;
        combo.dispatchEvent(new Event('change'));
    } else {
        window.location.reload();
    }
}

document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        const lang = btn.dataset.lang;
        applySelectedLanguage(lang);
    });
});

// Check current language on load
(function checkCurrentLanguage() {
    const googtrans = getLangCookie('googtrans');
    let current = 'vi';
    if (googtrans) {
        if (googtrans.includes('/en')) current = 'en';
        else if (googtrans.includes('/zh')) current = 'zh-CN';
    } else {
        const saved = localStorage.getItem('site_lang');
        if (saved) current = saved;
    }
    updateActiveLangButtons(current);
})();
