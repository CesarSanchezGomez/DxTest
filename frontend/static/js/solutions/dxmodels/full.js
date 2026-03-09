let files = { cdm: null, csf_cdm: null, sdm: null, csf_sdm: null };
let extractedMeta = { cdm: null, csf_cdm: null, sdm: null, csf_sdm: null };

document.addEventListener("DOMContentLoaded", () => { setupListeners(); });

function getMergedLanguages() {
    const all = new Set();
    for (const meta of Object.values(extractedMeta)) {
        if (meta?.languages) meta.languages.forEach((l) => all.add(l));
    }
    return [...all].sort();
}

function getMergedCountries() {
    const all = new Set();
    for (const meta of Object.values(extractedMeta)) {
        if (meta?.countries) meta.countries.forEach((c) => all.add(c));
    }
    return [...all].sort();
}

function setupListeners() {
    ModalManager.init((type, values) => {
        const el = type === "paises" ? "paises-count" : "idiomas-count";
        document.getElementById(el).textContent = `${values.length} seleccionados`;
    });

    document.getElementById("btn-select-paises").addEventListener("click", () =>
        ModalManager.open("paises", "Seleccionar Paises (CSF)", getMergedCountries())
    );
    document.getElementById("btn-select-idiomas").addEventListener("click", () =>
        ModalManager.open("idiomas", "Seleccionar Idiomas", getMergedLanguages())
    );

    setupFileInputs();
    document.getElementById("btn-procesar-completo").addEventListener("click", procesarCompleto);
    document.getElementById("btn-limpiar-completo").addEventListener("click", limpiarTodo);
}

function setupFileInputs() {
    ["cdm", "csf-cdm", "sdm", "csf-sdm"].forEach((type) => {
        const input = document.getElementById(`file-${type}`);
        const status = document.getElementById(`status-${type}`);
        const key = type.replace("-", "_");

        input.addEventListener("change", async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            status.textContent = `Cargando... (${sizeMB} MB)`;
            status.classList.remove("loaded", "error");

            const isLarge = file.size > 3 * 1024 * 1024;
            if (isLarge) showLoader();

            try {
                const content = await readFile(file);
                const preview = content.substring(0, 50000);

                if (!validateXMLType(preview, key)) {
                    throw new Error(`El archivo no corresponde a ${XML_NAMES[key]}`);
                }

                files[key] = content;
                const languages = extractLanguages(content);
                const countries = (key === "csf_cdm" || key === "csf_sdm") ? extractCountries(content) : [];
                extractedMeta[key] = { languages, countries };

                status.textContent = `OK ${file.name} (${sizeMB} MB)`;
                status.classList.add("loaded");
                addLog(`OK ${type.toUpperCase()}: ${file.name} (${sizeMB} MB) - ${languages.length} idiomas${countries.length ? `, ${countries.length} paises` : ""}`);
                showToast("Archivo cargado correctamente", "success");
            } catch (err) {
                input.value = "";
                files[key] = null;
                extractedMeta[key] = null;
                status.textContent = `Error: ${err.message}`;
                status.classList.add("error");
                showToast(err.message, "error");
                addLog(`Error: ${err.message}`);
            } finally {
                if (isLarge) hideLoader();
            }
        });
    });
}

async function procesarCompleto() {
    if (!ModalManager.selectedIdiomas.length) { showToast("Selecciona al menos un idioma", "error"); return; }
    const hasCSF = files.csf_cdm || files.csf_sdm;
    if (hasCSF && !ModalManager.selectedPaises.length) { showToast("Selecciona al menos un pais para archivos CSF", "error"); return; }
    if (!Object.values(files).some(Boolean)) { showToast("Carga al menos un archivo XML", "error"); return; }

    showLoader();
    addLog("Iniciando procesamiento...");

    try {
        const response = await fetch("/api/dxmodels/process/full", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                cdm_xml: files.cdm, csf_cdm_xml: files.csf_cdm,
                sdm_xml: files.sdm, csf_sdm_xml: files.csf_sdm,
                paises: ModalManager.selectedPaises, idiomas: ModalManager.selectedIdiomas,
            }),
        });

        if (!response.ok) { const err = await response.json(); throw new Error(err.detail || "Error en el procesamiento"); }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = Object.assign(document.createElement("a"), { href: url, download: "data_models_depurados.zip" });
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);

        addLog("OK Procesamiento completado - ZIP descargado");
        showToast("Procesamiento completado", "success");
    } catch (e) {
        addLog(`Error: ${e.message}`);
        showToast("Error al procesar XML", "error");
    } finally { hideLoader(); }
}

function limpiarTodo() {
    const hasFiles = Object.values(files).some(Boolean);
    const hasSelection = ModalManager.selectedPaises.length || ModalManager.selectedIdiomas.length;
    const hasLog = document.getElementById("log-output").innerHTML.trim();
    if (!hasFiles && !hasSelection && !hasLog) { showToast("No hay nada que limpiar", "error"); return; }

    files = { cdm: null, csf_cdm: null, sdm: null, csf_sdm: null };
    extractedMeta = { cdm: null, csf_cdm: null, sdm: null, csf_sdm: null };
    ModalManager.selectedPaises = []; ModalManager.selectedIdiomas = [];
    document.getElementById("paises-count").textContent = "0 seleccionados";
    document.getElementById("idiomas-count").textContent = "0 seleccionados";

    ["cdm", "csf-cdm", "sdm", "csf-sdm"].forEach((type) => {
        document.getElementById(`file-${type}`).value = "";
        const status = document.getElementById(`status-${type}`);
        status.textContent = "No cargado";
        status.classList.remove("loaded", "error");
    });

    document.getElementById("log-output").innerHTML = "";
    showToast("Formulario limpiado", "success");
}

function addLog(message) {
    const log = document.getElementById("log-output");
    const ts = new Date().toLocaleTimeString();
    log.innerHTML += `[${ts}] ${message}\n`;
    log.scrollTop = log.scrollHeight;
}
