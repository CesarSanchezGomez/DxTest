document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const API_BASE = '/api/dx-sentinel';

    const uploadForm = document.getElementById('uploadForm');
    const statusDiv = document.getElementById('status');
    const resultCard = document.getElementById('resultCard');
    const resultInfo = document.getElementById('resultInfo');
    const countryModal = document.getElementById('countryModal');
    const openModalBtn = document.getElementById('openCountryModal');
    const closeModalBtn = document.getElementById('closeCountryModal');
    const cancelModalBtn = document.getElementById('cancelCountrySelection');
    const confirmModalBtn = document.getElementById('confirmCountrySelection');
    const countryCheckboxesDiv = document.getElementById('countryCheckboxes');
    const selectAllBtn = document.getElementById('selectAllCountries');
    const deselectAllBtn = document.getElementById('deselectAllCountries');
    const selectedCountLabel = document.getElementById('selectedCountriesCount');
    const selectedPreview = document.getElementById('selectedCountriesPreview');
    const countrySearch = document.getElementById('countrySearch');
    const languageSelect = document.getElementById('languageCode');
    const languageHelper = document.getElementById('languageHelper');

    let csfFileId = null;
    let uploadedMainFileId = null;
    let selectedCountries = [];
    let selectedLanguage = 'en-US';

    const XML_VALIDATORS = {
        sdm: (c) => c.includes('<succession-data-model'),
        csf_sdm: (c) => c.includes('<country-specific-fields') && c.includes('<format-group')
    };

    // ─── Utilidades ─────────────────────────────────────────────────────

    function showToast(message, type) {
        const container = document.getElementById('toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = 'toast ' + (type || 'success');
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(function () { toast.remove(); }, 5000);
    }

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
        return container;
    }

    function showLoader(show, message) {
        let loader = document.querySelector('.loader');
        if (show) {
            if (!loader) {
                loader = document.createElement('div');
                loader.className = 'loader';
                loader.innerHTML = '<div class="spinner"></div><p>' + (message || 'Procesando...') + '</p>';
                document.body.appendChild(loader);
            } else {
                loader.querySelector('p').textContent = message || 'Procesando...';
            }
        } else if (loader) {
            loader.remove();
        }
    }

    function setStatus(message, type) {
        statusDiv.style.display = 'block';
        statusDiv.className = 'toast ' + (type || 'info');
        statusDiv.style.marginBottom = 'var(--spacing-md)';
        statusDiv.innerHTML = message;
    }

    // ─── Validacion XML ─────────────────────────────────────────────────

    function validateXMLFile(file, expectedType) {
        return new Promise(function (resolve, reject) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const content = e.target.result;
                const validator = XML_VALIDATORS[expectedType];
                if (!validator) { reject(new Error('Tipo de validacion desconocido')); return; }
                if (!validator(content)) {
                    const msgs = {
                        sdm: 'El archivo principal debe ser un Succession Data Model valido',
                        csf_sdm: 'El archivo CSF debe ser un CSF Succession Data Model valido'
                    };
                    reject(new Error(msgs[expectedType]));
                    return;
                }
                resolve(true);
            };
            reader.onerror = function () { reject(new Error('Error al leer el archivo')); };
            reader.readAsText(file);
        });
    }

    // ─── API calls ──────────────────────────────────────────────────────

    async function uploadFile(file, fileType) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);

        const response = await fetch(API_BASE + '/upload', {
            method: 'POST', body: formData, credentials: 'include'
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Upload failed');
        }
        const result = await response.json();
        if (!result.success) throw new Error(result.message || 'Upload failed');
        return result.file_id;
    }

    async function deleteServerFile(fileId) {
        if (!fileId) return;
        try {
            await fetch(API_BASE + '/upload/' + fileId, { method: 'DELETE', credentials: 'include' });
        } catch (e) {
            console.warn('No se pudo eliminar archivo:', e);
        }
    }

    async function extractLanguagesFromSDM(fileId) {
        const response = await fetch(API_BASE + '/languages/' + fileId, {
            method: 'GET', credentials: 'include'
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Error al extraer idiomas');
        }
        const result = await response.json();
        if (!result.success) throw new Error(result.message || 'Error al extraer idiomas');
        return result.languages;
    }

    async function extractCountriesFromCSF(fileId) {
        const response = await fetch(API_BASE + '/countries/' + fileId, {
            method: 'GET', credentials: 'include'
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Error al extraer paises');
        }
        const result = await response.json();
        if (!result.success) throw new Error(result.message || 'Error al extraer paises');
        return result.countries;
    }

    async function processFiles(mainFileId, csfId, languageCode, countryCodes) {
        const payload = {
            main_file_id: mainFileId,
            csf_file_id: csfId || null,
            language_code: languageCode,
            country_codes: countryCodes && countryCodes.length > 0 ? countryCodes : null
        };

        const response = await fetch(API_BASE + '/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Processing failed');
        }
        const result = await response.json();
        if (!result.success) throw new Error(result.message || 'Processing failed');
        return result;
    }

    // ─── Language ───────────────────────────────────────────────────────

    function resetLanguageSelection() {
        selectedLanguage = 'en-US';
        languageSelect.innerHTML = '<option value="en-US">en-US (por defecto)</option>';
        languageSelect.disabled = true;
        languageSelect.value = 'en-US';
        if (languageHelper) {
            languageHelper.textContent = 'Se activara al subir SDM';
            languageHelper.style.color = 'var(--color-gray-dark)';
        }
    }

    function populateLanguageSelect(languages) {
        languageSelect.innerHTML = '';
        languages.forEach(function (lang) {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = lang;
            if (lang === selectedLanguage) option.selected = true;
            languageSelect.appendChild(option);
        });
        languageSelect.disabled = false;
    }

    // ─── Country modal ──────────────────────────────────────────────────

    function openModal() {
        countryModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(function () { countrySearch.focus(); }, 100);
    }

    function closeModal() {
        countryModal.classList.remove('active');
        document.body.style.overflow = '';
        countrySearch.value = '';
        filterCountries('');
    }

    function updateSelectedCount() {
        const allCb = countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]');
        const count = Array.from(allCb).filter(function (cb) { return cb.checked; }).length;
        selectedCountLabel.textContent = count + ' seleccionados';
    }

    function updatePreview() {
        if (selectedCountries.length === 0) {
            selectedPreview.textContent = 'Ningun pais seleccionado';
            selectedPreview.style.color = 'var(--color-gray-dark)';
        } else {
            const preview = selectedCountries.length <= 3
                ? selectedCountries.join(', ')
                : selectedCountries.slice(0, 3).join(', ') + ' +' + (selectedCountries.length - 3) + ' mas';
            selectedPreview.textContent = selectedCountries.length + ' seleccionados: ' + preview;
            selectedPreview.style.color = 'var(--color-success)';
        }
    }

    function filterCountries(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        const items = countryCheckboxesDiv.querySelectorAll('.checkbox-item');
        items.forEach(function (item) {
            const cb = item.querySelector('input[type="checkbox"]');
            item.style.display = cb.value.toLowerCase().includes(term) ? 'flex' : 'none';
        });
        updateSelectedCount();
    }

    function populateCountryCheckboxes(countries) {
        countryCheckboxesDiv.innerHTML = '';
        countries.forEach(function (country) {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'checkbox-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = 'country_' + country;
            checkbox.value = country;
            checkbox.checked = selectedCountries.includes(country);
            checkbox.addEventListener('change', updateSelectedCount);

            const label = document.createElement('label');
            label.htmlFor = 'country_' + country;
            label.textContent = country;

            itemDiv.addEventListener('click', function (e) {
                if (e.target !== checkbox) {
                    checkbox.checked = !checkbox.checked;
                    updateSelectedCount();
                }
            });

            itemDiv.appendChild(checkbox);
            itemDiv.appendChild(label);
            countryCheckboxesDiv.appendChild(itemDiv);
        });
        updateSelectedCount();
    }

    function getSelectedCountriesFromModal() {
        const cbs = countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(cbs).map(function (cb) { return cb.value; });
    }

    function resetCountrySelection() {
        selectedCountries = [];
        csfFileId = null;
        countryCheckboxesDiv.innerHTML = '';
        openModalBtn.disabled = true;
        selectedPreview.textContent = 'Ningun pais seleccionado';
        selectedPreview.style.color = 'var(--color-gray-dark)';
        var helper = document.getElementById('countryCodeHelper');
        if (helper) {
            helper.textContent = 'Se activara al subir CSF';
            helper.style.color = 'var(--color-gray-dark)';
        }
    }

    // ─── Event listeners ────────────────────────────────────────────────

    countrySearch.addEventListener('input', function (e) { filterCountries(e.target.value); });
    openModalBtn.addEventListener('click', openModal);
    closeModalBtn.addEventListener('click', closeModal);
    cancelModalBtn.addEventListener('click', closeModal);

    confirmModalBtn.addEventListener('click', function () {
        selectedCountries = getSelectedCountriesFromModal();
        updatePreview();
        closeModal();
        if (selectedCountries.length > 0) {
            showToast(selectedCountries.length + (selectedCountries.length === 1 ? ' pais seleccionado' : ' paises seleccionados'), 'success');
        }
    });

    selectAllBtn.addEventListener('click', function () {
        countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = true; });
        updateSelectedCount();
    });

    deselectAllBtn.addEventListener('click', function () {
        countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = false; });
        updateSelectedCount();
    });

    countryModal.addEventListener('click', function (e) { if (e.target === countryModal) closeModal(); });

    // ─── File change handlers ───────────────────────────────────────────

    document.getElementById('mainFile').addEventListener('change', async function (e) {
        const file = e.target.files[0];
        const display = document.getElementById('mainFileName');

        if (!file) {
            display.textContent = 'Ningun archivo seleccionado';
            if (uploadedMainFileId) { await deleteServerFile(uploadedMainFileId); uploadedMainFileId = null; }
            resetLanguageSelection();
            return;
        }

        display.textContent = 'Validando ' + file.name + '...';

        try {
            await validateXMLFile(file, 'sdm');
            display.textContent = file.name;
            display.style.color = 'var(--color-success)';

            showLoader(true, 'Extrayendo idiomas del SDM...');
            uploadedMainFileId = await uploadFile(file, 'sdm');
            const languages = await extractLanguagesFromSDM(uploadedMainFileId);
            showLoader(false);

            populateLanguageSelect(languages);
            if (languages.length === 1) selectedLanguage = languages[0];

            if (languageHelper) {
                languageHelper.textContent = languages.length + (languages.length === 1 ? ' idioma encontrado' : ' idiomas encontrados');
                languageHelper.style.color = 'var(--color-success)';
            }
            showToast(languages.length + ' idioma(s) encontrado(s) en el SDM', 'success');
        } catch (error) {
            display.textContent = error.message;
            display.style.color = 'var(--color-error)';
            e.target.value = '';
            showLoader(false);
            resetLanguageSelection();
            showToast(error.message, 'error');
        }
    });

    document.getElementById('csfFile').addEventListener('change', async function (e) {
        const file = e.target.files[0];
        const display = document.getElementById('csfFileName');

        if (!file) {
            display.textContent = 'Ningun archivo seleccionado (opcional)';
            resetCountrySelection();
            return;
        }

        display.textContent = 'Validando ' + file.name + '...';

        try {
            await validateXMLFile(file, 'csf_sdm');
            display.textContent = file.name;
            display.style.color = 'var(--color-success)';

            showLoader(true, 'Extrayendo paises del CSF...');
            csfFileId = await uploadFile(file, 'csf_sdm');
            const countries = await extractCountriesFromCSF(csfFileId);
            showLoader(false);

            openModalBtn.disabled = false;
            selectedCountries = [];
            populateCountryCheckboxes(countries);
            updatePreview();

            var helper = document.getElementById('countryCodeHelper');
            if (helper) {
                helper.textContent = countries.length + (countries.length === 1 ? ' pais encontrado' : ' paises encontrados');
                helper.style.color = 'var(--color-success)';
            }
            showToast(countries.length + ' pais(es) encontrado(s) en el CSF', 'success');
        } catch (error) {
            display.textContent = error.message;
            display.style.color = 'var(--color-error)';
            e.target.value = '';
            showLoader(false);
            resetCountrySelection();
            showToast(error.message, 'error');
        }
    });

    // ─── Form submit ────────────────────────────────────────────────────

    uploadForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const submitBtn = document.querySelector('button[type="submit"]');
        const mainFile = document.getElementById('mainFile').files[0];
        const languageCode = languageSelect.value;

        if (!mainFile && !uploadedMainFileId) {
            showToast('Selecciona el archivo principal', 'error');
            return;
        }
        if (csfFileId && selectedCountries.length === 0) {
            showToast('Selecciona al menos un pais del CSF', 'error');
            return;
        }

        submitBtn.disabled = true;
        var originalText = submitBtn.textContent;
        submitBtn.textContent = 'Procesando...';

        try {
            showLoader(true, 'Procesando archivos...');
            var countriesToSend = csfFileId ? selectedCountries : null;
            var result = await processFiles(uploadedMainFileId, csfFileId, languageCode, countriesToSend);
            showLoader(false);
            displayResult(result);
        } catch (error) {
            console.error(error);
            showLoader(false);
            setStatus('Error: ' + error.message, 'error');
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });

    // ─── Display result ─────────────────────────────────────────────────

    function displayResult(processResult) {
        var downloadId = processResult.download_id;

        resultInfo.innerHTML =
            '<div class="form-grid-3" style="margin-bottom: var(--spacing-md);">' +
                '<div class="form-group">' +
                    '<label>Campos:</label>' +
                    '<div class="info-field"><span class="badge">' + processResult.field_count + '</span></div>' +
                '</div>' +
                '<div class="form-group">' +
                    '<label>Tiempo:</label>' +
                    '<div class="info-field"><span class="badge">' + processResult.processing_time + 's</span></div>' +
                '</div>' +
                (processResult.countries_processed ? '<div class="form-group">' +
                    '<label>Paises:</label>' +
                    '<div class="info-field"><span class="badge">' + processResult.countries_processed.join(', ') + '</span></div>' +
                '</div>' : '') +
            '</div>' +
            '<a href="' + API_BASE + '/download/' + downloadId + '"' +
            '   class="btn btn-primary" download' +
            '   style="text-align: center; text-decoration: none; width: 100%; display: block;">' +
            '   Descargar Golden Record (ZIP)' +
            '</a>' +
            '<p style="font-size: 12px; color: var(--color-gray-dark); margin-top: var(--spacing-sm); text-align: center;">' +
            'El ZIP contiene: Golden Record CSV, Metadata JSON y Field Report XLSX' +
            '</p>';

        resultCard.style.display = 'block';
        statusDiv.style.display = 'none';
    }
});
