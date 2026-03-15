document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    var API_BASE = '/api/dxsentinel';

    var projectSelect = document.getElementById('projectSelect');
    var versionSelect = document.getElementById('versionSelect');
    var versionHelper = document.getElementById('versionHelper');
    var splitBtn = document.getElementById('splitBtn');
    var statusDiv = document.getElementById('status');
    var resultCard = document.getElementById('resultCard');
    var resultInfo = document.getElementById('resultInfo');

    var projects = [];
    var versions = [];
    var selectedVersionId = null;

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

    function setStatus(message, type) {
        statusDiv.style.display = 'block';
        statusDiv.className = 'toast ' + (type || 'info');
        statusDiv.style.marginBottom = 'var(--spacing-md)';
        statusDiv.innerHTML = message;
    }

    // ── Load projects ────────────────────────────────────────────────────

    async function loadProjects() {
        try {
            var response = await fetch(API_BASE + '/projects', { credentials: 'include' });
            var data = await response.json();
            projects = data.projects || [];

            projectSelect.innerHTML = '';
            if (projects.length === 0) {
                projectSelect.innerHTML = '<option value="">No hay proyectos disponibles</option>';
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
        splitBtn.disabled = true;
        selectedVersionId = null;

        try {
            var url = API_BASE + '/versions/' + encodeURIComponent(project.instance_number) + '/' + encodeURIComponent(project.client_name);
            var response = await fetch(url, { credentials: 'include' });
            var data = await response.json();
            versions = data.versions || [];

            versionSelect.innerHTML = '';
            if (versions.length === 0) {
                versionSelect.innerHTML = '<option value="">No hay versiones</option>';
                if (versionHelper) { versionHelper.textContent = 'Genera un Golden Record primero'; versionHelper.style.color = 'var(--color-gray-dark)'; }
                return;
            }

            versions.forEach(function (v, i) {
                var opt = document.createElement('option');
                opt.value = i;
                var countries = v.country_codes ? ' [' + v.country_codes.join(', ') + ']' : '';
                opt.textContent = 'v' + v.version_number + ' - ' + v.language_code + countries + ' (' + (v.field_count || 0) + ' campos)';
                versionSelect.appendChild(opt);
            });

            versionSelect.disabled = false;
            selectedVersionId = versions[0].id;
            splitBtn.disabled = false;

            if (versionHelper) {
                versionHelper.textContent = versions.length + ' version(es) disponible(s)';
                versionHelper.style.color = 'var(--color-success)';
            }
        } catch (e) {
            versionSelect.innerHTML = '<option value="">Error cargando versiones</option>';
            showToast('Error cargando versiones', 'error');
        }
    }

    // ── Event listeners ──────────────────────────────────────────────────

    projectSelect.addEventListener('change', function () {
        var idx = parseInt(this.value, 10);
        if (isNaN(idx)) {
            versionSelect.innerHTML = '<option value="">Selecciona un proyecto primero</option>';
            versionSelect.disabled = true;
            splitBtn.disabled = true;
            selectedVersionId = null;
            if (versionHelper) versionHelper.textContent = '';
            return;
        }
        loadVersions(projects[idx]);
    });

    versionSelect.addEventListener('change', function () {
        var idx = parseInt(this.value, 10);
        if (!isNaN(idx) && versions[idx]) {
            selectedVersionId = versions[idx].id;
            splitBtn.disabled = false;
        } else {
            selectedVersionId = null;
            splitBtn.disabled = true;
        }
    });

    // ── Split ────────────────────────────────────────────────────────────

    splitBtn.addEventListener('click', async function () {
        if (!selectedVersionId) {
            showToast('Selecciona una version', 'error');
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
                body: JSON.stringify({ version_id: selectedVersionId }),
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
            setStatus('Error: ' + error.message, 'error');
            showToast(error.message, 'error');
        } finally {
            splitBtn.disabled = false;
            splitBtn.textContent = originalText;
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
