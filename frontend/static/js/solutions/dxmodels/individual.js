let availableLanguages = [];
let availableCountries = [];
let xmlContent = "";
let inputEditor = null;
let outputEditor = null;

document.addEventListener("DOMContentLoaded", () => {
    initEditors();
    setupListeners();
});

function initEditors() {
    const cfg = { mode: "xml", theme: "monokai", lineNumbers: true, readOnly: true, lineWrapping: true, viewportMargin: 50 };
    inputEditor = CodeMirror.fromTextArea(document.getElementById("xml-input"), cfg);
    outputEditor = CodeMirror.fromTextArea(document.getElementById("xml-output"), cfg);
}

function setupListeners() {
    ModalManager.init((type, values) => {
        const el = type === "paises" ? "paises-count" : "idiomas-count";
        document.getElementById(el).textContent = `${values.length} seleccionados`;
    });

    if (requireCountries) {
        document.getElementById("btn-select-paises").addEventListener("click", () =>
            ModalManager.open("paises", "Seleccionar Paises", availableCountries)
        );
    }

    document.getElementById("btn-select-idiomas").addEventListener("click", () =>
        ModalManager.open("idiomas", "Seleccionar Idiomas", availableLanguages)
    );

    setupFileInput();

    document.getElementById("btn-procesar").onclick = procesarXML;
    document.getElementById("btn-limpiar").onclick = limpiar;
    document.getElementById("btn-copy-input").onclick = () => xmlContent && copyToClipboard(xmlContent);
    document.getElementById("btn-copy-output").onclick = () => {
        const v = outputEditor.getValue();
        if (v) copyToClipboard(v);
    };
    document.getElementById("btn-download").onclick = () => {
        const v = outputEditor.getValue();
        if (v) downloadFile(v, `${dataModel}_depurado.xml`);
    };
}

function setupFileInput() {
    const input = document.getElementById("xml-file");
    const label = document.getElementById("file-name");

    input.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        label.textContent = "Cargando archivo...";
        showLoader();

        try {
            const content = await readFile(file);
            const preview = content.substring(0, 50000);

            if (!validateXMLType(preview, dataModel)) {
                throw new Error(`El archivo no corresponde a ${XML_NAMES[dataModel]}`);
            }

            xmlContent = content;
            availableLanguages = extractLanguages(content);
            if (requireCountries) {
                availableCountries = extractCountries(content);
            }

            ModalManager.selectedIdiomas = [];
            ModalManager.selectedPaises = [];
            document.getElementById("idiomas-count").textContent = "0 seleccionados";
            if (requireCountries) {
                document.getElementById("paises-count").textContent = "0 seleccionados";
            }

            label.textContent = `OK ${file.name}`;
            label.style.color = "var(--color-success, #82C016)";
            document.getElementById("editor-section").style.display = "block";
            inputEditor.setValue(content);

            const msg = requireCountries
                ? `Archivo cargado: ${availableLanguages.length} idiomas, ${availableCountries.length} paises detectados`
                : `Archivo cargado: ${availableLanguages.length} idiomas detectados`;
            showToast(msg, "success");
        } catch (err) {
            xmlContent = "";
            availableLanguages = [];
            availableCountries = [];
            input.value = "";
            label.textContent = err.message;
            label.style.color = "var(--color-error, #f45a4a)";
            inputEditor.setValue("");
            document.getElementById("editor-section").style.display = "none";
            showToast(err.message, "error");
        } finally {
            hideLoader();
        }
    });
}

async function procesarXML() {
    if (!ModalManager.selectedIdiomas.length) {
        showToast("Selecciona al menos un idioma", "error");
        return;
    }
    if (requireCountries && !ModalManager.selectedPaises.length) {
        showToast("Selecciona al menos un pais", "error");
        return;
    }
    if (!xmlContent) {
        showToast("Carga un archivo XML primero", "error");
        return;
    }

    const endpoint = (dataModel === "cdm" || dataModel === "sdm")
        ? `/api/dxmodels/process/${dataModel}`
        : "/api/dxmodels/process/csf";

    showLoader();
    try {
        const res = await fetchAPI(endpoint, {
            method: "POST",
            body: JSON.stringify({
                xml_content: xmlContent,
                paises: ModalManager.selectedPaises,
                idiomas: ModalManager.selectedIdiomas,
            }),
        });
        outputEditor.setValue(res.resultado);
        showToast("Procesamiento completado", "success");
    } catch (e) {
        showToast("Error al procesar XML", "error");
    } finally {
        hideLoader();
    }
}

function limpiar() {
    const hasContent = xmlContent || ModalManager.selectedPaises.length || ModalManager.selectedIdiomas.length || outputEditor.getValue();
    if (!hasContent) {
        showToast("No hay nada que limpiar", "error");
        return;
    }

    xmlContent = "";
    availableLanguages = [];
    availableCountries = [];
    ModalManager.selectedPaises = [];
    ModalManager.selectedIdiomas = [];

    document.getElementById("xml-file").value = "";
    const label = document.getElementById("file-name");
    label.textContent = "Ningun archivo seleccionado";
    label.style.color = "";

    document.getElementById("editor-section").style.display = "none";
    inputEditor.setValue("");
    outputEditor.setValue("");

    if (requireCountries) {
        document.getElementById("paises-count").textContent = "0 seleccionados";
    }
    document.getElementById("idiomas-count").textContent = "0 seleccionados";

    showToast("Formulario limpiado", "success");
}
