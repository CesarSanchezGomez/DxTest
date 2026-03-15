document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    var API_BASE = '/api/dxsentinel';

    var projectSelect = document.getElementById('projectSelect');
    var versionSelect = document.getElementById('versionSelect');
    var versionHelper = document.getElementById('versionHelper');
    var csvFile = document.getElementById('csvFile');
    var csvFileName = document.getElementById('csvFileName');
    var validateBtn = document.getElementById('validateBtn');
    var splitBtn = document.getElementById('splitBtn');
    var statusDiv = document.getElementById('status');
    var resultCard = document.getElementById('resultCard');
    var resultInfo = document.getElementById('resultInfo');
    var validationCard = document.getElementById('validationCard');
    var validationContent = document.getElementById('validationContent');

    var projects = [];
    var versions = [];
    var selectedVersionId = null;
    var uploadedCsvFileId = null;
    var validationPassed = false; // true si validacion permite split

    // ── Utilidades ───────────────────────────────────────────────────────

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

    function updateButtons() {
        validateBtn.disabled = !(selectedVersionId && uploadedCsvFileId);
        splitBtn.disabled = !(selectedVersionId && uploadedCsvFileId && validationPassed);
    }

    function resetValidation() {
        validationPassed = false;
        validationCard.style.display = 'none';
        validationContent.innerHTML = '';
        resultCard.style.display = 'none';
        updateButtons();
    }

    // ── Load projects ────────────────────────────────────────────────────

    async function loadProjects() {
        try {
            var response = await fetch(API_BASE + '/projects', { credentials: 'include' });
            var data = await response.json();
            projects = data.projects || [];

            projectSelect.innerHTML = '';
            if (projects.length === 0) {
                projectSelect.innerHTML = '<option value="">No hay proyectos - genera un Golden Record primero</option>';
                return;
            }

            var defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = 'Selecciona un proyecto...';
            projectSelect.appendChild(defaultOpt);

            projects.forEach(function (p, i) {
                var opt = document.createElement('option');
                opt.value = i;
                opt.textContent = p.instance_number + ' - ' + p.client_name + ' (' + p.total_versions + ' versiones)';
                projectSelect.appendChild(opt);
            });
        } catch (e) {
            projectSelect.innerHTML = '<option value="">Error cargando proyectos</option>';
            showToast('Error cargando proyectos', 'error');
        }
    }

    // ── Load versions ────────────────────────────────────────────────────

    async function loadVersions(project) {
        versionSelect.innerHTML = '<option value="">Cargando versiones...</option>';
        versionSelect.disabled = true;
        selectedVersionId = null;
        csvFile.disabled = true;
        resetValidation();

        try {
            var url = API_BASE + '/versions/' + encodeURIComponent(project.instance_number) + '/' + encodeURIComponent(project.client_name);
            var response = await fetch(url, { credentials: 'include' });
            var data = await response.json();
            versions = data.versions || [];

            versionSelect.innerHTML = '';
            if (versions.length === 0) {
                versionSelect.innerHTML = '<option value="">No hay versiones</option>';
                if (versionHelper) { versionHelper.textContent = 'Genera un Golden Record primero'; }
                return;
            }

            versions.forEach(function (v, i) {
                var opt = document.createElement('option');
                opt.value = i;
                var countries = v.country_codes ? ' [' + v.country_codes.join(', ') + ']' : '';
                opt.textContent = 'v' + v.version_number + ' - ' + v.language_code + countries;
                versionSelect.appendChild(opt);
            });

            versionSelect.disabled = false;
            selectedVersionId = versions[0].id;
            csvFile.disabled = false;
            csvFileName.textContent = 'Ningun archivo seleccionado';

            if (versionHelper) {
                versionHelper.textContent = versions.length + ' version(es) disponible(s)';
                versionHelper.style.color = 'var(--color-success)';
            }

            updateButtons();
        } catch (e) {
            versionSelect.innerHTML = '<option value="">Error cargando versiones</option>';
            showToast('Error cargando versiones', 'error');
        }
    }

    // ── Upload CSV ───────────────────────────────────────────────────────

    async function uploadCsvFile(file) {
        var formData = new FormData();
        formData.append('file', file);

        var response = await fetch(API_BASE + '/split/upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Upload failed');
        }

        return await response.json();
    }

    // ── Event listeners ──────────────────────────────────────────────────

    projectSelect.addEventListener('change', function () {
        var idx = parseInt(this.value, 10);
        if (isNaN(idx)) {
            versionSelect.innerHTML = '<option value="">Selecciona un proyecto primero</option>';
            versionSelect.disabled = true;
            csvFile.disabled = true;
            selectedVersionId = null;
            if (versionHelper) versionHelper.textContent = 'La version determina la metadata para el split';
            resetValidation();
            return;
        }
        loadVersions(projects[idx]);
    });

    versionSelect.addEventListener('change', function () {
        var idx = parseInt(this.value, 10);
        if (!isNaN(idx) && versions[idx]) {
            selectedVersionId = versions[idx].id;
            csvFile.disabled = false;
        } else {
            selectedVersionId = null;
            csvFile.disabled = true;
        }
        resetValidation();
    });

    csvFile.addEventListener('change', async function () {
        var file = this.files[0];
        if (!file) {
            uploadedCsvFileId = null;
            csvFileName.textContent = 'Ningun archivo seleccionado';
            resetValidation();
            return;
        }

        if (!file.name.toLowerCase().endsWith('.csv')) {
            showToast('Solo se aceptan archivos CSV', 'error');
            this.value = '';
            return;
        }

        csvFileName.textContent = 'Subiendo ' + file.name + '...';
        csvFileName.style.color = 'var(--color-gray-dark)';

        try {
            var result = await uploadCsvFile(file);
            uploadedCsvFileId = result.file_id;
            csvFileName.textContent = file.name;
            csvFileName.style.color = 'var(--color-success)';
            resetValidation();
        } catch (e) {
            csvFileName.textContent = 'Error subiendo archivo';
            csvFileName.style.color = 'var(--color-error)';
            uploadedCsvFileId = null;
            showToast(e.message, 'error');
            resetValidation();
        }
    });

    // ── Validate ─────────────────────────────────────────────────────────

    validateBtn.addEventListener('click', async function () {
        if (!selectedVersionId || !uploadedCsvFileId) {
            showToast('Selecciona una version y sube el Golden Record', 'error');
            return;
        }

        validateBtn.disabled = true;
        var originalText = validateBtn.textContent;
        validateBtn.textContent = 'Validando...';

        try {
            showLoader(true, 'Validando Golden Record...');

            var response = await fetch(API_BASE + '/split/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    version_id: selectedVersionId,
                    csv_file_id: uploadedCsvFileId
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                var err = await response.json();
                throw new Error(err.detail || 'Validacion fallida');
            }

            var result = await response.json();
            showLoader(false);
            displayValidation(result);

        } catch (error) {
            console.error(error);
            showLoader(false);
            showToast(error.message, 'error');
        } finally {
            validateBtn.disabled = false;
            validateBtn.textContent = originalText;
            updateButtons();
        }
    });

    function displayValidation(result) {
        var summary = result.summary || {};
        var errorsByEntity = result.errors_by_entity || {};
        validationPassed = result.can_split;

        // Summary badges
        var html = '<div class="validation-summary">';
        if (summary.fatal > 0) {
            html += '<span class="badge badge-fatal">FATAL: ' + summary.fatal + '</span>';
        }
        if (summary.error > 0) {
            html += '<span class="badge badge-error">ERROR: ' + summary.error + '</span>';
        }
        if (summary.warning > 0) {
            html += '<span class="badge badge-warning">WARNING: ' + summary.warning + '</span>';
        }
        if (summary.total === 0) {
            html += '<span class="badge badge-ok">Sin problemas</span>';
        }
        html += '<span style="margin-left: auto; font-weight: 400;">' + result.message + '</span>';
        html += '</div>';

        // Issues grouped by entity
        var entities = Object.keys(errorsByEntity);
        if (entities.length > 0) {
            html += '<div class="validation-issues">';

            for (var e = 0; e < entities.length; e++) {
                var entityId = entities[e];
                var entityIssues = errorsByEntity[entityId];

                html += '<div class="entity-section">';
                html += '<div class="entity-header">';
                html += '<span>' + entityId + '</span>';
                html += '<span class="entity-count">' + entityIssues.length + ' error(es)</span>';
                html += '</div>';
                html += '<table>';
                html += '<thead><tr>';
                html += '<th>Fila</th><th>Campo</th><th>Severidad</th><th>Error</th><th>Valor</th><th>Person ID</th>';
                html += '</tr></thead><tbody>';

                for (var i = 0; i < entityIssues.length; i++) {
                    var issue = entityIssues[i];
                    var sevClass = 'sev-' + issue.severity;
                    var rowDisplay = issue.row_index != null ? issue.row_index : '-';
                    var valueDisplay = issue.value ? '<span class="val-value">' + escapeHtml(issue.value) + '</span>' : '-';
                    var pidDisplay = issue.person_id || '-';

                    html += '<tr>';
                    html += '<td>' + rowDisplay + '</td>';
                    html += '<td>' + (issue.field_id || '-') + '</td>';
                    html += '<td class="' + sevClass + '">' + issue.severity.toUpperCase() + '</td>';
                    html += '<td>' + issue.message + '</td>';
                    html += '<td>' + valueDisplay + '</td>';
                    html += '<td>' + pidDisplay + '</td>';
                    html += '</tr>';
                }

                html += '</tbody></table></div>';
            }

            html += '</div>';
        }

        validationContent.innerHTML = html;
        validationCard.style.display = 'block';

        // Feedback
        if (validationPassed) {
            showToast(result.message, 'success');
        } else {
            showToast(result.message, 'error');
        }

        updateButtons();
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Split ────────────────────────────────────────────────────────────

    splitBtn.addEventListener('click', async function () {
        if (!selectedVersionId || !uploadedCsvFileId || !validationPassed) {
            showToast('Valida primero el Golden Record', 'error');
            return;
        }

        splitBtn.disabled = true;
        var originalText = splitBtn.textContent;
        splitBtn.textContent = 'Procesando...';

        try {
            showLoader(true, 'Dividiendo Golden Record en templates...');

            var response = await fetch(API_BASE + '/split/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    version_id: selectedVersionId,
                    csv_file_id: uploadedCsvFileId
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                var err = await response.json();
                throw new Error(err.detail || 'Split failed');
            }

            var result = await response.json();
            if (!result.success) throw new Error(result.message || 'Split failed');

            showLoader(false);
            displayResult(result);
        } catch (error) {
            console.error(error);
            showLoader(false);
            showToast(error.message, 'error');
        } finally {
            splitBtn.disabled = false;
            splitBtn.textContent = originalText;
            updateButtons();
        }
    });

    // ── Display result ───────────────────────────────────────────────────

    function displayResult(result) {
        resultInfo.innerHTML =
            '<div class="form-grid-3" style="margin-bottom: var(--spacing-md);">' +
                '<div class="form-group">' +
                    '<label>Templates:</label>' +
                    '<div class="info-field"><span class="badge">' + result.template_count + '</span></div>' +
                '</div>' +
                '<div class="form-group">' +
                    '<label>Tiempo:</label>' +
                    '<div class="info-field"><span class="badge">' + result.processing_time + 's</span></div>' +
                '</div>' +
            '</div>' +
            '<a href="' + API_BASE + '/split/download/' + result.download_id + '"' +
            '   class="btn btn-primary" download' +
            '   style="text-align: center; text-decoration: none; width: 100%; display: block;">' +
            '   Descargar Templates (ZIP)' +
            '</a>' +
            '<p style="font-size: 12px; color: var(--color-gray-dark); margin-top: var(--spacing-sm); text-align: center;">' +
            'El ZIP contiene un CSV por entidad + BasicUserInformation.csv' +
            '</p>';

        resultCard.style.display = 'block';
        statusDiv.style.display = 'none';
    }

    // ── Init ─────────────────────────────────────────────────────────────
    loadProjects();
});
