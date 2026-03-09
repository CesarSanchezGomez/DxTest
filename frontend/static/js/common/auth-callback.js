(function () {
    "use strict";
    const ALLOWED_DOMAIN = window.ALLOWED_DOMAIN || "dxgrow.com";

    function showError(message) {
        const spinner = document.getElementById("spinner");
        const errorMsg = document.getElementById("error-message");
        const errorText = document.getElementById("error-text");
        if (spinner) spinner.style.display = "none";
        if (errorText) errorText.textContent = message;
        if (errorMsg) errorMsg.style.display = "block";
    }

    function processCallback() {
        try {
            const params = new URLSearchParams(window.location.hash.substring(1));
            const accessToken = params.get("access_token");
            const refreshToken = params.get("refresh_token");
            const error = params.get("error");

            if (error) { showError(`Error de autenticacion: ${params.get("error_description") || error}`); return; }
            if (!accessToken) { showError("No se recibio el token de acceso. Intenta nuevamente."); return; }

            const payload = JSON.parse(atob(accessToken.split(".")[1]));
            if (!payload.email.endsWith(`@${ALLOWED_DOMAIN}`)) { showError(`Solo se permite acceso a usuarios de @${ALLOWED_DOMAIN}`); return; }

            const form = document.createElement("form");
            form.method = "POST";
            form.action = "/auth/session";

            const fields = { access_token: accessToken, email: payload.email };
            if (refreshToken) fields.refresh_token = refreshToken;

            for (const [name, value] of Object.entries(fields)) {
                form.appendChild(Object.assign(document.createElement("input"), { type: "hidden", name, value }));
            }

            document.body.appendChild(form);
            form.submit();
        } catch (err) { showError("Error inesperado: " + err.message); }
    }

    processCallback();
})();
