document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    var NON_EXCLUDABLE_ENTITIES = [
        'personInfo', 'personalInfo', 'employmentInfo', 'jobInfo', 'compInfo'
    ];

    var API_BASE = '/api/dxsentinel';

    var uploadForm = document.getElementById('uploadForm');
    var statusDiv = document.getElementById('status');
    var resultCard = document.getElementById('resultCard');
    var resultInfo = document.getElementById('resultInfo');
    var countryModal = document.getElementById('countryModal');
    var openCountryModalBtn = document.getElementById('openCountryModal');
    var closeCountryModalBtn = document.getElementById('closeCountryModal');
    var cancelCountryBtn = document.getElementById('cancelCountrySelection');
    var confirmCountryBtn = document.getElementById('confirmCountrySelection');
    var countryCheckboxesDiv = document.getElementById('countryCheckboxes');
    var selectAllCountriesBtn = document.getElementById('selectAllCountries');
    var deselectAllCountriesBtn = document.getElementById('deselectAllCountries');
    var selectedCountriesCountLabel = document.getElementById('selectedCountriesCount');
    var selectedCountriesPreview = document.getElementById('selectedCountriesPreview');
    var countrySearch = document.getElementById('countrySearch');
    var languageSelect = document.getElementById('languageCode');
    var languageHelper = document.getElementById('languageHelper');

    var entityModal = document.getElementById('entityModal');
    var openEntityModalBtn = document.getElementById('openEntityModal');
    var closeEntityModalBtn = document.getElementById('closeEntityModal');
    var cancelEntityBtn = document.getElementById('cancelEntitySelection');
    var confirmEntityBtn = document.getElementById('confirmEntitySelection');
    var entityCheckboxesDiv = document.getElementById('entityCheckboxes');
    var selectAllEntitiesBtn = document.getElementById('selectAllEntities');
    var deselectAllEntitiesBtn = document.getElementById('deselectAllEntities');
    var selectedEntitiesCountLabel = document.getElementById('selectedEntitiesCount');
    var selectedEntitiesPreview = document.getElementById('selectedEntitiesPreview');
    var entitySearch = document.getElementById('entitySearch');
    var entityHelper = document.getElementById('entityHelper');

    var csfFileId = null;
    var uploadedMainFileId = null;
    var selectedCountries = [];
    var selectedLanguage = 'en-US';
    var availableEntities = [];
    var excludedEntities = [];

    var XML_VALIDATORS = {
        sdm: function (c) { return c.includes('<succession-data-model'); },
        csf_sdm: function (c) { return c.includes('<country-specific-fields') && c.includes('<format-group'); }
    };

    // ─── Utilidades ─────────────────────────────────────────────────────

    function showToast(message, type) {
        var container = document.getElementById('toast-container') || createToastContainer();
        var toast = document.createElement('div');
        toast.className = 'toast ' + (type || 'success');
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(function () { toast.remove(); }, 5000);
    }

    function createToastContainer() {
        var container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
        return container;
    }

    function showLoader(show, message) {
        var loader = document.querySelector('.loader');
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
            var reader = new FileReader();
            reader.onload = function (e) {
                var content = e.target.result;
                var validator = XML_VALIDATORS[expectedType];
                if (!validator) { reject(new Error('Tipo de validacion desconocido')); return; }
                if (!validator(content)) {
                    var msgs = {
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
        var formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);

        var response = await fetch(API_BASE + '/upload', {
            method: 'POST', body: formData, credentials: 'include'
        });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Upload failed');
        }
        var result = await response.json();
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
        var response = await fetch(API_BASE + '/languages/' + fileId, {
            method: 'GET', credentials: 'include'
        });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Error al extraer idiomas');
        }
        var result = await response.json();
        if (!result.success) throw new Error(result.message || 'Error al extraer idiomas');
        return result.languages;
    }

    async function extractEntitiesFromSDM(fileId) {
        var response = await fetch(API_BASE + '/entities/' + fileId, {
            method: 'GET', credentials: 'include'
        });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Error al extraer entidades');
        }
        var result = await response.json();
        if (!result.success) throw new Error(result.message || 'Error al extraer entidades');
        return result.entities;
    }

    async function extractCountriesFromCSF(fileId) {
        var response = await fetch(API_BASE + '/countries/' + fileId, {
            method: 'GET', credentials: 'include'
        });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Error al extraer paises');
        }
        var result = await response.json();
        if (!result.success) throw new Error(result.message || 'Error al extraer paises');
        return result.countries;
    }

    async function processFiles(mainFileId, csfId, languageCode, countryCodes, excludedEnts) {
        var payload = {
            main_file_id: mainFileId,
            csf_file_id: csfId || null,
            language_code: languageCode,
            country_codes: countryCodes && countryCodes.length > 0 ? countryCodes : null,
            excluded_entities: excludedEnts && excludedEnts.length > 0 ? excludedEnts : null
        };

        var response = await fetch(API_BASE + '/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        });

        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Processing failed');
        }
        var result = await response.json();
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
            var option = document.createElement('option');
            option.value = lang;
            option.textContent = lang;
            if (lang === selectedLanguage) option.selected = true;
            languageSelect.appendChild(option);
        });
        languageSelect.disabled = false;
    }

    // ─── Entity modal ───────────────────────────────────────────────────

    function openEntityModalFn() {
        entityModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(function () { entitySearch.focus(); }, 100);
    }

    function closeEntityModalFn() {
        entityModal.classList.remove('active');
        document.body.style.overflow = '';
        entitySearch.value = '';
        filterEntities('');
    }

    function updateEntityCount() {
        var allCb = entityCheckboxesDiv.querySelectorAll('input[type="checkbox"]');
        var count = Array.from(allCb).filter(function (cb) { return cb.checked; }).length;
        selectedEntitiesCountLabel.textContent = count + ' / ' + allCb.length + ' seleccionados';
    }

    function updateEntityPreview() {
        var total = availableEntities.length;
        var includedCount = total - excludedEntities.length;

        if (excludedEntities.length === 0) {
            selectedEntitiesPreview.textContent = 'Todas las entidades incluidas (' + total + ')';
            selectedEntitiesPreview.style.color = 'var(--color-success)';
        } else {
            selectedEntitiesPreview.textContent = includedCount + ' de ' + total + ' entidades incluidas';
            selectedEntitiesPreview.style.color = 'var(--color-warning, var(--color-gray-dark))';
        }
    }

    function filterEntities(searchTerm) {
        var term = searchTerm.toLowerCase().trim();
        var items = entityCheckboxesDiv.querySelectorAll('.checkbox-item');
        items.forEach(function (item) {
            var cb = item.querySelector('input[type="checkbox"]');
            item.style.display = cb.value.toLowerCase().includes(term) ? 'flex' : 'none';
        });
        updateEntityCount();
    }

    function populateEntityCheckboxes(entities) {
        entityCheckboxesDiv.innerHTML = '';
        entities.forEach(function (entity) {
            var itemDiv = document.createElement('div');
            itemDiv.className = 'checkbox-item';

            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = 'entity_' + entity;
            checkbox.value = entity;
            checkbox.checked = !excludedEntities.includes(entity);
            checkbox.addEventListener('change', updateEntityCount);

            var isLocked = NON_EXCLUDABLE_ENTITIES.indexOf(entity) !== -1;
            if (isLocked) {
                checkbox.checked = true;
                checkbox.disabled = true;
            }

            var label = document.createElement('label');
            label.htmlFor = 'entity_' + entity;
            label.textContent = entity;
            if (isLocked) {
                label.style.fontStyle = 'italic';
            }

            itemDiv.addEventListener('click', function (e) {
                if (isLocked) return;
                if (e.target !== checkbox) {
                    checkbox.checked = !checkbox.checked;
                    updateEntityCount();
                }
            });

            itemDiv.appendChild(checkbox);
            itemDiv.appendChild(label);
            entityCheckboxesDiv.appendChild(itemDiv);
        });
        updateEntityCount();
    }

    function getExcludedEntitiesFromModal() {
        var allCb = entityCheckboxesDiv.querySelectorAll('input[type="checkbox"]');
        return Array.from(allCb)
            .filter(function (cb) { return !cb.checked && !cb.disabled; })
            .map(function (cb) { return cb.value; });
    }

    function resetEntitySelection() {
        availableEntities = [];
        excludedEntities = [];
        entityCheckboxesDiv.innerHTML = '';
        openEntityModalBtn.disabled = true;
        selectedEntitiesPreview.textContent = 'Todas las entidades incluidas';
        selectedEntitiesPreview.style.color = 'var(--color-gray-dark)';
        if (entityHelper) {
            entityHelper.textContent = 'Se activara al subir SDM';
            entityHelper.style.color = 'var(--color-gray-dark)';
        }
    }

    // ─── Entity event listeners ─────────────────────────────────────────

    entitySearch.addEventListener('input', function (e) { filterEntities(e.target.value); });
    openEntityModalBtn.addEventListener('click', openEntityModalFn);
    closeEntityModalBtn.addEventListener('click', closeEntityModalFn);
    cancelEntityBtn.addEventListener('click', closeEntityModalFn);

    confirmEntityBtn.addEventListener('click', function () {
        excludedEntities = getExcludedEntitiesFromModal();
        updateEntityPreview();
        closeEntityModalFn();
        var included = availableEntities.length - excludedEntities.length;
        showToast(included + ' de ' + availableEntities.length + ' entidades incluidas', 'success');
    });

    selectAllEntitiesBtn.addEventListener('click', function () {
        entityCheckboxesDiv.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
            if (!cb.disabled) cb.checked = true;
        });
        updateEntityCount();
    });

    deselectAllEntitiesBtn.addEventListener('click', function () {
        entityCheckboxesDiv.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
            if (!cb.disabled) cb.checked = false;
        });
        updateEntityCount();
    });

    entityModal.addEventListener('click', function (e) { if (e.target === entityModal) closeEntityModalFn(); });

    // ─── Country modal ──────────────────────────────────────────────────

    function openCountryModalFn() {
        countryModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(function () { countrySearch.focus(); }, 100);
    }

    function closeCountryModalFn() {
        countryModal.classList.remove('active');
        document.body.style.overflow = '';
        countrySearch.value = '';
        filterCountries('');
    }

    function updateSelectedCount() {
        var allCb = countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]');
        var count = Array.from(allCb).filter(function (cb) { return cb.checked; }).length;
        selectedCountriesCountLabel.textContent = count + ' seleccionados';
    }

    function updatePreview() {
        if (selectedCountries.length === 0) {
            selectedCountriesPreview.textContent = 'Ningun pais seleccionado';
            selectedCountriesPreview.style.color = 'var(--color-gray-dark)';
        } else {
            var preview = selectedCountries.length <= 3
                ? selectedCountries.join(', ')
                : selectedCountries.slice(0, 3).join(', ') + ' +' + (selectedCountries.length - 3) + ' mas';
            selectedCountriesPreview.textContent = selectedCountries.length + ' seleccionados: ' + preview;
            selectedCountriesPreview.style.color = 'var(--color-success)';
        }
    }

    function filterCountries(searchTerm) {
        var term = searchTerm.toLowerCase().trim();
        var items = countryCheckboxesDiv.querySelectorAll('.checkbox-item');
        items.forEach(function (item) {
            var cb = item.querySelector('input[type="checkbox"]');
            item.style.display = cb.value.toLowerCase().includes(term) ? 'flex' : 'none';
        });
        updateSelectedCount();
    }

    function populateCountryCheckboxes(countries) {
        countryCheckboxesDiv.innerHTML = '';
        countries.forEach(function (country) {
            var itemDiv = document.createElement('div');
            itemDiv.className = 'checkbox-item';

            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = 'country_' + country;
            checkbox.value = country;
            checkbox.checked = selectedCountries.includes(country);
            checkbox.addEventListener('change', updateSelectedCount);

            var label = document.createElement('label');
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
        var cbs = countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(cbs).map(function (cb) { return cb.value; });
    }

    function resetCountrySelection() {
        selectedCountries = [];
        csfFileId = null;
        countryCheckboxesDiv.innerHTML = '';
        openCountryModalBtn.disabled = true;
        selectedCountriesPreview.textContent = 'Ningun pais seleccionado';
        selectedCountriesPreview.style.color = 'var(--color-gray-dark)';
        var helper = document.getElementById('countryCodeHelper');
        if (helper) {
            helper.textContent = 'Se activara al subir CSF';
            helper.style.color = 'var(--color-gray-dark)';
        }
    }

    // ─── Country event listeners ────────────────────────────────────────

    countrySearch.addEventListener('input', function (e) { filterCountries(e.target.value); });
    openCountryModalBtn.addEventListener('click', openCountryModalFn);
    closeCountryModalBtn.addEventListener('click', closeCountryModalFn);
    cancelCountryBtn.addEventListener('click', closeCountryModalFn);

    confirmCountryBtn.addEventListener('click', function () {
        selectedCountries = getSelectedCountriesFromModal();
        updatePreview();
        closeCountryModalFn();
        if (selectedCountries.length > 0) {
            showToast(selectedCountries.length + (selectedCountries.length === 1 ? ' pais seleccionado' : ' paises seleccionados'), 'success');
        }
    });

    selectAllCountriesBtn.addEventListener('click', function () {
        countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = true; });
        updateSelectedCount();
    });

    deselectAllCountriesBtn.addEventListener('click', function () {
        countryCheckboxesDiv.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = false; });
        updateSelectedCount();
    });

    countryModal.addEventListener('click', function (e) { if (e.target === countryModal) closeCountryModalFn(); });

    // ─── File change handlers ───────────────────────────────────────────

    document.getElementById('mainFile').addEventListener('change', async function (e) {
        var file = e.target.files[0];
        var display = document.getElementById('mainFileName');

        if (!file) {
            display.textContent = 'Ningun archivo seleccionado';
            if (uploadedMainFileId) { await deleteServerFile(uploadedMainFileId); uploadedMainFileId = null; }
            resetLanguageSelection();
            resetEntitySelection();
            return;
        }

        display.textContent = 'Validando ' + file.name + '...';

        try {
            await validateXMLFile(file, 'sdm');
            display.textContent = file.name;
            display.style.color = 'var(--color-success)';

            showLoader(true, 'Extrayendo idiomas y entidades del SDM...');
            uploadedMainFileId = await uploadFile(file, 'sdm');

            var languages = await extractLanguagesFromSDM(uploadedMainFileId);
            var entities = await extractEntitiesFromSDM(uploadedMainFileId);
            showLoader(false);

            populateLanguageSelect(languages);
            if (languages.length === 1) selectedLanguage = languages[0];

            if (languageHelper) {
                languageHelper.textContent = languages.length + (languages.length === 1 ? ' idioma encontrado' : ' idiomas encontrados');
                languageHelper.style.color = 'var(--color-success)';
            }

            availableEntities = entities;
            excludedEntities = [];
            populateEntityCheckboxes(entities);
            updateEntityPreview();
            openEntityModalBtn.disabled = false;

            if (entityHelper) {
                entityHelper.textContent = entities.length + (entities.length === 1 ? ' entidad encontrada' : ' entidades encontradas');
                entityHelper.style.color = 'var(--color-success)';
            }

            showToast(languages.length + ' idioma(s) y ' + entities.length + ' entidad(es) encontrada(s)', 'success');
        } catch (error) {
            display.textContent = error.message;
            display.style.color = 'var(--color-error)';
            e.target.value = '';
            showLoader(false);
            resetLanguageSelection();
            resetEntitySelection();
            showToast(error.message, 'error');
        }
    });

    document.getElementById('csfFile').addEventListener('change', async function (e) {
        var file = e.target.files[0];
        var display = document.getElementById('csfFileName');

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
            var countries = await extractCountriesFromCSF(csfFileId);
            showLoader(false);

            openCountryModalBtn.disabled = false;
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

        var submitBtn = document.querySelector('button[type="submit"]');
        var mainFile = document.getElementById('mainFile').files[0];
        var languageCode = languageSelect.value;

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
            var excludedToSend = excludedEntities.length > 0 ? excludedEntities : null;
            var result = await processFiles(uploadedMainFileId, csfFileId, languageCode, countriesToSend, excludedToSend);
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
