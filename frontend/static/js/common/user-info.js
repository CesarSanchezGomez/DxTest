document.addEventListener("DOMContentLoaded", async () => {
    const avatarEl = document.getElementById("user-avatar");
    if (!avatarEl) return;

    const CACHE_KEY = "userAvatarData";
    const CACHE_TTL = 3600000;

    function showInitials(email) {
        const initials = email.split("@")[0].substring(0, 2).toUpperCase();
        avatarEl.style.display = "none";
        const div = document.createElement("div");
        div.className = "user-avatar-initials";
        div.textContent = initials;
        avatarEl.parentNode.insertBefore(div, avatarEl);
    }

    function applyAvatar(email, url) {
        if (url) {
            avatarEl.src = url; avatarEl.alt = "User avatar"; avatarEl.style.display = "";
            const prev = avatarEl.previousSibling;
            if (prev?.className === "user-avatar-initials") prev.remove();
        } else { showInitials(email); }
        avatarEl.title = email;
    }

    try {
        const cached = JSON.parse(localStorage.getItem(CACHE_KEY));
        if (cached && Date.now() - cached.timestamp < CACHE_TTL) applyAvatar(cached.email, cached.url);
    } catch {}

    try {
        const res = await fetch("/auth/user");
        if (!res.ok) throw new Error("Not authenticated");
        const data = await res.json();
        const email = data.user.email;
        const url = data.user.user_metadata?.avatar_url || data.user.user_metadata?.picture;
        applyAvatar(email, url);
        localStorage.setItem(CACHE_KEY, JSON.stringify({ url, email, timestamp: Date.now() }));
    } catch {
        localStorage.removeItem(CACHE_KEY);
        window.location.href = "/auth/login";
    }
});
