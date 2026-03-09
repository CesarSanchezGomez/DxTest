(function () {
    "use strict";
    const SUPABASE_URL = window.SUPABASE_CONFIG?.url;
    const SUPABASE_KEY = window.SUPABASE_CONFIG?.key;
    if (!SUPABASE_URL || !SUPABASE_KEY) { console.error("Configuracion de Supabase no disponible"); return; }
    const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

    function showUrlError() {
        const error = new URLSearchParams(window.location.search).get("error");
        if (!error) return;
        const messages = { domain_not_allowed: "Solo se permite acceso a usuarios de @dxgrow.com", access_denied: "Acceso denegado. Por favor, intente nuevamente." };
        document.getElementById("error-container").innerHTML = `<div class="error-message">${messages[error] || error}</div>`;
    }

    async function loginWithGoogle() {
        try {
            const { error } = await supabaseClient.auth.signInWithOAuth({
                provider: "google",
                options: { redirectTo: window.location.origin + "/auth/callback", queryParams: { access_type: "offline", prompt: "consent", hd: "dxgrow.com" } },
            });
            if (error) document.getElementById("error-container").innerHTML = `<div class="error-message">${error.message}</div>`;
        } catch (err) {
            console.error("Error en login:", err);
            document.getElementById("error-container").innerHTML = '<div class="error-message">Error inesperado. Intente nuevamente.</div>';
        }
    }

    async function checkSession() {
        try { const { data: { session } } = await supabaseClient.auth.getSession(); if (session) window.location.href = "/"; } catch (err) { console.error("Error verificando sesion:", err); }
    }

    window.loginWithGoogle = loginWithGoogle;
    showUrlError();
    checkSession();
})();
