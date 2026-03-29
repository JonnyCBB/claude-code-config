# Presenter Features Reference

Speaker view, cross-tab sync, blackout/whiteout, theme toggle, print stylesheet, and scroll-driven animations.

## Speaker / Presenter View

Press "S" to open a presenter window with speaker notes, elapsed timer, and pacing indicator. Uses `BroadcastChannel` for sync (simpler than `postMessage`, survives window refresh, 96%+ support).

**HTML (hidden speaker notes per slide):**
```html
<section class="slide">
    <h2>Our Strategy</h2>
    <p>Content visible to audience...</p>
    <aside class="notes">
        Mention Q3 results. Pause for questions.
        Transition: "Now let me show you the numbers..."
    </aside>
</section>
```

**CSS:**
```css
aside.notes { display: none; } /* Hidden in main presentation */
```

**JS (BroadcastChannel sync):**
```javascript
// In SlidePresentation class:
openPresenterView() {
    const presenterHTML = `<!DOCTYPE html>
    <html><head><style>
        body { font-family: system-ui; background: #1a1a1a; color: #fff; display: grid;
               grid-template: "current next" 60% "notes timer" 40% / 1fr 1fr;
               height: 100vh; gap: 1rem; padding: 1rem; }
        .current-slide { grid-area: current; border: 2px solid #4361ee; }
        .next-slide { grid-area: next; opacity: 0.6; }
        .notes-panel { grid-area: notes; overflow-y: auto; padding: 1rem;
                       background: #2d2d2d; border-radius: 8px; }
        .timer-panel { grid-area: timer; display: flex; flex-direction: column;
                       align-items: center; justify-content: center; }
        .elapsed { font-size: 3rem; font-variant-numeric: tabular-nums; }
        .pacing { font-size: 1.2rem; margin-top: 1rem; }
        .pacing.behind { color: #ff4444; }
        .pacing.ahead { color: #44ff44; }
        iframe { width: 100%; height: 100%; border: none; border-radius: 8px; }
    </style></head><body>
        <div class="current-slide"><iframe id="current"></iframe></div>
        <div class="next-slide"><iframe id="next"></iframe></div>
        <div class="notes-panel" id="notes">Speaker notes appear here</div>
        <div class="timer-panel">
            <div class="elapsed" id="elapsed">00:00</div>
            <div class="pacing" id="pacing">On pace</div>
        </div>
        <script>
            const channel = new BroadcastChannel('slide-sync');
            const startTime = Date.now();
            // Update timer
            setInterval(() => {
                const s = Math.floor((Date.now() - startTime) / 1000);
                document.getElementById('elapsed').textContent =
                    String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0');
            }, 1000);
            // Listen for slide changes
            channel.onmessage = (e) => {
                const { slide, total, notes } = e.data;
                document.getElementById('notes').innerHTML = notes || '<em>No notes for this slide</em>';
                // Pacing
                const elapsed = (Date.now() - startTime) / 1000;
                const expectedPace = (slide / total);
                const actualPace = elapsed / (elapsed + (total - slide) * (elapsed / Math.max(slide, 1)));
                const pacing = document.getElementById('pacing');
                pacing.textContent = actualPace > expectedPace + 0.1 ? 'Behind pace' :
                                     actualPace < expectedPace - 0.1 ? 'Ahead of pace' : 'On pace';
                pacing.className = 'pacing ' + (actualPace > expectedPace + 0.1 ? 'behind' :
                                                actualPace < expectedPace - 0.1 ? 'ahead' : '');
            };
        </script>
    </body></html>`;
    window.open(URL.createObjectURL(new Blob([presenterHTML], {type: 'text/html'})));
}

// In goToSlide():
const notes = this.slides[index].querySelector('aside.notes');
new BroadcastChannel('slide-sync').postMessage({
    slide: index,
    total: this.slides.length,
    notes: notes ? notes.innerHTML : ''
});
```

## Code Copy Button

```css
pre { position: relative; }
pre .copy-btn {
    position: absolute; top: 0.5rem; right: 0.5rem;
    background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
    color: inherit; padding: 0.25rem 0.5rem; border-radius: 4px;
    font-size: var(--small-size); cursor: pointer;
    opacity: 0; transition: opacity 0.2s;
}
pre:hover .copy-btn { opacity: 1; }
pre .copy-btn.copied { background: rgba(0,255,100,0.2); }
```

```javascript
document.querySelectorAll('pre code').forEach(block => {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.addEventListener('click', async () => {
        await navigator.clipboard.writeText(block.textContent);
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
    });
    block.parentElement.appendChild(btn);
});
```

## Cross-Tab Sync (Audience Follow-Along)

Different from speaker view (which opens a new window with notes). Cross-tab sync lets audience members open the same presentation URL and follow along — when the presenter advances, all synced tabs advance too.

```javascript
/* ===========================================
   CROSS-TAB SYNC (Audience Follow-Along)
   Uses BroadcastChannel to sync slide position
   across all tabs/windows with the same presentation.

   Presenter tab: broadcasts slide changes
   Audience tabs: receive and follow

   Press P to toggle presenter mode (broadcasting).
   =========================================== */

// In SlidePresentation class:

initCrossTabSync() {
    this.syncChannel = new BroadcastChannel('slide-audience-sync');
    this.isPresenter = false;

    // Listen for sync messages
    this.syncChannel.onmessage = (e) => {
        if (this.isPresenter) return; // Presenter doesn't follow
        if (e.data.type === 'navigate') {
            this.goToSlide(e.data.slideIndex, { broadcast: false });
        }
    };
}

togglePresenterMode() {
    this.isPresenter = !this.isPresenter;
    document.body.classList.toggle('presenter-mode', this.isPresenter);
    // Visual indicator
    if (this.isPresenter) {
        this.showNotification('Presenter mode ON — audience tabs will follow');
    } else {
        this.showNotification('Presenter mode OFF');
    }
}

showNotification(text) {
    const el = document.createElement('div');
    el.className = 'sync-notification';
    el.textContent = text;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2000);
}

// Modify goToSlide() to broadcast when in presenter mode:
// Add options parameter: goToSlide(index, options = {})
goToSlide(index, { broadcast = true } = {}) {
    // ... existing navigation logic ...

    // Broadcast to synced tabs
    if (broadcast && this.isPresenter && this.syncChannel) {
        this.syncChannel.postMessage({
            type: 'navigate',
            slideIndex: index
        });
    }
}

// In keyboard handler:
case 'p':
case 'P':
    this.togglePresenterMode();
    break;
```

```css
/* ===========================================
   CROSS-TAB SYNC UI
   =========================================== */
.sync-notification {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    padding: 0.5rem 1.5rem;
    background: color-mix(in oklch, var(--bg-primary), black 20%);
    color: var(--text-primary);
    border-radius: 2rem;
    font-size: var(--small-size);
    z-index: 10000;
    animation: notification-fade 2s ease forwards;
}

@keyframes notification-fade {
    0%, 70% { opacity: 1; }
    100% { opacity: 0; }
}

/* Presenter mode indicator — subtle border glow */
body.presenter-mode::before {
    content: '';
    position: fixed;
    inset: 0;
    border: 2px solid var(--accent, #4a9eff);
    pointer-events: none;
    z-index: 9999;
    opacity: 0.5;
}
```

**Anti-slop note**: This reuses the existing `BroadcastChannel` pattern from speaker view but uses a different channel name (`slide-audience-sync` vs `slide-sync`). Speaker view opens a separate window with notes/timer, while cross-tab sync just mirrors slide navigation across same-URL tabs. The `{ broadcast: false }` option in `goToSlide()` prevents infinite feedback loops. Presenter mode requires explicit opt-in via P key — audience tabs just follow by default.

## Slide Pause (Blackout / Whiteout)

Press B for blackout, W for whiteout. Press again to dismiss.

```css
.blackout-overlay {
    position: fixed; inset: 0;
    z-index: 9999;
    transition: opacity 0.3s;
    pointer-events: none;
    opacity: 0;
}
.blackout-overlay.active {
    pointer-events: auto;
    opacity: 1;
}
.blackout-overlay.black { background: #000; }
.blackout-overlay.white { background: #fff; }
```

```javascript
// In keyboard handler:
case 'b': case 'B':
    this.toggleOverlay('black'); break;
case 'w': case 'W':
    this.toggleOverlay('white'); break;

toggleOverlay(color) {
    let overlay = document.querySelector('.blackout-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'blackout-overlay';
        document.body.appendChild(overlay);
    }
    if (overlay.classList.contains('active') && overlay.classList.contains(color)) {
        overlay.classList.remove('active');
    } else {
        overlay.className = `blackout-overlay ${color} active`;
    }
}
```

## Runtime Theme Toggle (T Key)

Each preset can define 2-3 runtime variants (light/dark/high-contrast) that swap CSS custom properties only. The preset remains the base design system; the toggle adjusts colors.

```css
/* ===========================================
   RUNTIME THEME VARIANTS
   T key cycles through color variants within the
   current preset. Stored in localStorage.
   Each preset defines its own variants.
   =========================================== */

/* Default variant (the preset's original colors) */
html[data-theme="default"] {
    /* Uses preset's original --bg-primary, --text-primary, etc. */
}

/* Dark variant */
html[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --text-primary: #e8e8e8;
    --text-secondary: #a0a0a0;
    /* Accent stays the same */
}

/* Light variant */
html[data-theme="light"] {
    --bg-primary: #fafafa;
    --text-primary: #1a1a1a;
    --text-secondary: #555;
    /* Accent stays the same */
}
```

```javascript
/* ===========================================
   THEME TOGGLE
   Cycles through preset color variants with T key.
   Persists choice to localStorage.
   =========================================== */

// In SlidePresentation class:

initThemeToggle() {
    this.themes = ['default', 'dark', 'light'];
    this.themeIndex = 0;

    // Restore saved theme
    const saved = localStorage.getItem('slide-theme');
    if (saved && this.themes.includes(saved)) {
        this.themeIndex = this.themes.indexOf(saved);
        document.documentElement.dataset.theme = saved;
    }
}

cycleTheme() {
    this.themeIndex = (this.themeIndex + 1) % this.themes.length;
    const theme = this.themes[this.themeIndex];
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('slide-theme', theme);
}

// In keyboard handler:
case 't':
case 'T':
    this.cycleTheme();
    break;
```

**Anti-slop note**: This is NOT the same as switching between presets. The preset defines the full design system (fonts, layouts, decorative elements). Theme cycling only swaps color custom properties (`--bg-primary`, `--text-primary`, `--text-secondary`). The preset's accent color, fonts, and structural elements remain unchanged. Instruct presenters to define their own variant colors based on the preset's palette.

## Print / PDF Stylesheet

```css
/* ===========================================
   PRINT STYLESHEET
   One slide per page. Hidden navigation.
   =========================================== */
@media print {
    html { scroll-snap-type: none; }
    body { overflow: visible; }
    .slide {
        height: auto;
        min-height: 100vh;
        overflow: visible;
        page-break-after: always;
        scroll-snap-align: none;
    }
    /* Show all fragments */
    .fragment { opacity: 1 !important; transform: none !important; }
    /* Hide UI */
    .nav-dots, .progress-bar, .keyboard-hint,
    .edit-hotzone, .edit-toggle, .copy-btn,
    .blackout-overlay, .playback-controls { display: none !important; }
    /* Video slides show placeholder */
    .slide-video { display: none; }
    .video-play-btn { display: none; }
    .video-container::after {
        content: '[Video]';
        font-style: italic;
        color: var(--text-secondary);
    }
    /* Preserve backgrounds */
    * { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
}
```

## Scroll-Driven Animations (Progressive Enhancement)

Wrap all scroll-driven animations in `@supports (animation-timeline: view())`. Keep the Intersection Observer JavaScript as the primary approach — scroll-driven CSS is a progressive enhancement that provides smoother animations in supported browsers. Chrome 115+, Safari 26+. Firefox: behind flag.

```css
/* ===========================================
   SCROLL-DRIVEN ANIMATIONS (Progressive Enhancement)
   Pure CSS alternative to Intersection Observer for entrance animations.
   =========================================== */
@supports (animation-timeline: view()) {
    .reveal {
        animation: slide-entrance linear both;
        animation-timeline: view();
        animation-range: entry 0% entry 100%;
    }
    @keyframes slide-entrance {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* CSS-only progress bar */
    .progress-bar {
        animation: progress-fill linear;
        animation-timeline: scroll(root);
    }
    @keyframes progress-fill {
        from { transform: scaleX(0); }
        to { transform: scaleX(1); }
    }
}
```
