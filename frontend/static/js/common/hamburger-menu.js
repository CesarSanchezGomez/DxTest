(function () {
    const btn = document.getElementById("hamburger-btn");
    const menu = document.getElementById("header-quicklinks");
    if (!btn || !menu) return;

    const BP = 768;

    function position() {
        try {
            const header = document.querySelector(".header");
            const rect = header ? header.getBoundingClientRect() : btn.getBoundingClientRect();
            let w = menu.offsetWidth || 200;
            const m = 8;
            let left = Math.round(rect.right - w - m);

            if (w + m * 2 > window.innerWidth) {
                w = Math.max(120, window.innerWidth - m * 2);
                menu.style.width = `${w}px`;
                left = m;
            }
            if (left < m) left = m;
            if (left + w > window.innerWidth - m) left = Math.max(m, window.innerWidth - w - m);

            menu.style.left = `${left}px`;
            menu.style.top = `${Math.round(rect.bottom + 6)}px`;
        } catch {}
    }

    function clear() {
        menu.style.left = "";
        menu.style.top = "";
        menu.style.width = "";
    }

    function close() {
        btn.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
        menu.classList.remove("open");
        setTimeout(() => { if (!menu.classList.contains("open")) clear(); }, 300);
        try { btn.focus(); } catch {}
    }

    function open() {
        position();
        btn.classList.add("open");
        btn.setAttribute("aria-expanded", "true");
        menu.classList.add("open");
        const first = menu.querySelector("a");
        if (first) try { first.focus(); } catch {}
    }

    btn.addEventListener("click", (e) => {
        e.stopPropagation();
        menu.classList.contains("open") ? close() : open();
    });

    document.addEventListener("click", (e) => {
        if (!menu.contains(e.target) && !btn.contains(e.target)) close();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") close();
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > BP) {
            menu.classList.remove("open");
            btn.classList.remove("open");
            btn.setAttribute("aria-expanded", "false");
            clear();
        } else if (menu.classList.contains("open")) {
            position();
        }
    });

    window.addEventListener("scroll", () => {
        if (menu.classList.contains("open")) position();
    }, { passive: true });
})();
