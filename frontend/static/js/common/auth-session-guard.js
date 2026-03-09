(() => {
    const WARNING_BEFORE_MS = 10 * 60 * 1000;
    const CHECK_INTERVAL_MS = 10 * 1000;

    let countdownInterval = null;
    let checkInterval = null;
    let warningShown = false;
    let knownExpiresAt = null;

    function getExpiresAt() {
        const match = document.cookie.match(/(?:^|;\s*)session_expires_at=(\d+)/);
        return match ? parseInt(match[1], 10) * 1000 : null;
    }

    function formatTime(ms) {
        const totalSec = Math.max(0, Math.ceil(ms / 1000));
        const min = Math.floor(totalSec / 60);
        const sec = totalSec % 60;
        return `${min}:${sec.toString().padStart(2, "0")}`;
    }

    function showWarning(remainingMs, expiresAt) {
        if (warningShown) return;
        warningShown = true;
        knownExpiresAt = expiresAt;

        const overlay = document.createElement("div");
        overlay.id = "session-warning";
        overlay.className = "session-warning-overlay";
        overlay.innerHTML = `
            <div class="session-warning-card">
                <div class="session-warning-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                    </svg>
                </div>
                <h3>Su sesion esta por expirar</h3>
                <p class="session-warning-timer" id="session-timer">${formatTime(remainingMs)}</p>
                <p class="session-warning-desc">Si no renueva la sesion, sera redirigido al inicio de sesion.</p>
                <button type="button" id="session-renew-btn" class="btn btn-primary">Seguir trabajando</button>
            </div>
        `;
        document.body.appendChild(overlay);

        const timerEl = document.getElementById("session-timer");
        const renewBtn = document.getElementById("session-renew-btn");

        renewBtn.addEventListener("click", renewSession);

        countdownInterval = setInterval(() => {
            const expiresAt = getExpiresAt() || knownExpiresAt;
            if (!expiresAt) return;
            const left = expiresAt - Date.now();
            if (left <= 0) {
                clearInterval(countdownInterval);
                window.location.href = "/auth/logout";
                return;
            }
            timerEl.textContent = formatTime(left);
        }, 1000);
    }

    function hideWarning() {
        warningShown = false;
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }
        const el = document.getElementById("session-warning");
        if (el) el.remove();
    }

    async function renewSession() {
        const btn = document.getElementById("session-renew-btn");
        if (btn) {
            btn.disabled = true;
            btn.textContent = "Renovando...";
        }
        try {
            const res = await fetch("/auth/refresh", { method: "POST" });
            if (res.ok) {
                hideWarning();
            } else {
                window.location.href = "/auth/logout";
            }
        } catch {
            window.location.href = "/auth/logout";
        }
    }

    function checkSession() {
        const expiresAt = getExpiresAt();

        if (!expiresAt) {
            if (knownExpiresAt) window.location.href = "/auth/logout";
            return;
        }

        knownExpiresAt = expiresAt;
        const remaining = expiresAt - Date.now();

        if (remaining <= 0) {
            window.location.href = "/auth/logout";
            return;
        }

        if (remaining <= WARNING_BEFORE_MS) {
            showWarning(remaining, expiresAt);
        }
    }

    checkSession();
    checkInterval = setInterval(checkSession, CHECK_INTERVAL_MS);

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) checkSession();
    });
})();
