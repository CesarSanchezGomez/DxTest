// --- Toast ---

function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// --- Loader ---

function showLoader() {
    document.getElementById("loader").style.display = "flex";
}

function hideLoader() {
    document.getElementById("loader").style.display = "none";
}

// --- API ---

async function fetchAPI(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error en la peticion");
    }
    return response.json();
}

// --- File I/O ---

function downloadFile(content, filename) {
    const blob = new Blob([content], { type: "text/xml" });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), { href: url, download: filename });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function readFile(file) {
    return new Promise((resolve, reject) => {
        const CHUNK = 1024 * 1024;
        const chunks = [];
        let offset = 0;
        const reader = new FileReader();

        reader.onerror = () => reject(reader.error);
        reader.onload = (e) => {
            chunks.push(e.target.result);
            offset += CHUNK;
            if (offset < file.size) {
                setTimeout(next, 0);
            } else {
                resolve(chunks.join(""));
            }
        };

        function next() {
            reader.readAsText(file.slice(offset, offset + CHUNK));
        }
        next();
    });
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast("Copiado al portapapeles", "success");
    } catch {
        showToast("Error al copiar", "error");
    }
}

// --- XML Validators ---

const XML_VALIDATORS = {
    cdm: (c) => c.includes("<corporate-data-model"),
    sdm: (c) => c.includes("<succession-data-model"),
    csf_cdm: (c) =>
        c.includes("<country-specific-fields") &&
        c.includes("<hris-element") &&
        !c.includes("<format-group"),
    csf_sdm: (c) =>
        c.includes("<country-specific-fields") &&
        c.includes("<format-group"),
};

const XML_NAMES = {
    cdm: "Corporate Data Model",
    csf_cdm: "CSF Corporate Data Model",
    sdm: "Succession Data Model",
    csf_sdm: "CSF Succession Data Model",
};

function validateXMLType(content, type) {
    const validator = XML_VALIDATORS[type];
    return validator ? validator(content) : false;
}

// --- XML Metadata Extraction ---

function extractLanguages(xmlContent) {
    const langs = new Set();
    const regex = /xml:lang="([^"]+)"/g;
    let match;
    while ((match = regex.exec(xmlContent)) !== null) {
        langs.add(match[1]);
    }
    langs.delete("en-DEBUG");
    return [...langs].sort();
}

function extractCountries(xmlContent) {
    const countries = new Set();
    const regex = /<country\s[^>]*id="([^"]+)"/g;
    let match;
    while ((match = regex.exec(xmlContent)) !== null) {
        countries.add(match[1]);
    }
    return [...countries].sort();
}

// --- Modal ---

const ModalManager = {
    _currentType: "",
    _selectedPaises: [],
    _selectedIdiomas: [],
    _onConfirm: null,

    get selectedPaises() { return this._selectedPaises; },
    set selectedPaises(v) { this._selectedPaises = v; },
    get selectedIdiomas() { return this._selectedIdiomas; },
    set selectedIdiomas(v) { this._selectedIdiomas = v; },

    init(onConfirm) {
        this._onConfirm = onConfirm;
        document.getElementById("modal-close").onclick = () => this.close();
        document.getElementById("modal-cancel").onclick = () => this.close();
        document.getElementById("modal-confirm").onclick = () => this.confirm();
        document.getElementById("modal-selector").onclick = (e) => {
            if (e.target.id === "modal-selector") this.close();
        };
    },

    open(type, title, items) {
        if (!items.length) {
            showToast("No hay elementos disponibles. Carga un archivo XML primero.", "error");
            return;
        }

        this._currentType = type;
        document.getElementById("modal-title").textContent = title;
        const searchInput = document.getElementById("modal-search");
        searchInput.value = "";

        const container = document.getElementById("modal-options");
        const selected = type === "paises" ? this._selectedPaises : this._selectedIdiomas;
        container.innerHTML = "";

        items.forEach((code) => {
            const row = document.createElement("div");
            row.className = "checkbox-item";
            row.dataset.name = code.toLowerCase();

            const cb = document.createElement("input");
            cb.type = "checkbox";
            cb.id = `modal-${code}`;
            cb.value = code;
            cb.checked = selected.includes(code);

            const label = document.createElement("label");
            label.htmlFor = `modal-${code}`;
            label.textContent = code;

            row.append(cb, label);
            container.appendChild(row);
        });

        searchInput.oninput = (e) => {
            const q = e.target.value.toLowerCase();
            container.querySelectorAll(".checkbox-item").forEach((item) => {
                item.style.display = item.dataset.name.includes(q) ? "flex" : "none";
            });
        };

        document.getElementById("modal-selector").classList.add("active");
    },

    close() {
        document.getElementById("modal-selector").classList.remove("active");
    },

    confirm() {
        const values = [...document.querySelectorAll("#modal-options input:checked")].map((cb) => cb.value);
        if (!values.length) {
            showToast("Selecciona al menos un elemento", "error");
            return;
        }

        if (this._currentType === "paises") {
            this._selectedPaises = values;
        } else {
            this._selectedIdiomas = values;
        }

        this.close();
        showToast(`${values.length} elementos seleccionados`, "success");

        if (this._onConfirm) this._onConfirm(this._currentType, values);
    },
};

// --- Hamburger Menu ---

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
