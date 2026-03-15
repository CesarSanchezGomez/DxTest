document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    var API_BASE = '/api/dxsentinel';

    var splitForm = document.getElementById('splitForm');
    var splitBtn = document.getElementById('splitBtn');
    var statusDiv = document.getElementById('status');
    var resultCard = document.getElementById('resultCard');
    var resultInfo = document.getElementById('resultInfo');

    var csvFileId = null;
    var metadataFileId = null;

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

    function updateSplitButton() {
        splitBtn.disabled = !(csvFileId && metadataFileId);
    }

    // ── API calls ────────────────────────────────────────────────────────

    async function uploadSplitFile(file) {
        var formData = new FormData();
        formData.append('file', file);

        var response = await fetch(API_BASE + '/split/upload', {
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

    async function processSplit(csvId, metaId) {
        var response = await fetch(API_BASE + '/split/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ csv_file_id: csvId, metadata_file_id: metaId }),
            credentials: 'include'
        });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Split failed');
        }
        var result = await response.json();
        if (!result.success) throw new Error(result.message || 'Split failed');
        return result;
    }

    async function deleteFile(fileId) {
        if (!fileId) return;
        try {
            await fetch(API_BASE + '/upload/' + fileId, { method: 'DELETE', credentials: 'include' });
        } catch (e) { /* ignore */ }
    }

    // ── File handlers ────────────────────────────────────────────────────

    document.getElementById('csvFile').addEventListener('change', async function (e) {
        var file = e.target.files[0];
        var display = document.getElementById('csvFileName');

        if (!file) {
            display.textContent = 'Ningun archivo seleccionado';
            display.style.color = '';
            if (csvFileId) { await deleteFile(csvFileId); csvFileId = null; }
            updateSplitButton();
            return;
        }

        if (!file.name.toLowerCase().endsWith('.csv')) {
            display.textContent = 'El archivo debe ser CSV';
            display.style.color = 'var(--color-error)';
            e.target.value = '';
            showToast('Solo se aceptan archivos CSV', 'error');
            return;
        }

        display.textContent = 'Subiendo ' + file.name + '...';
        display.style.color = '';

        try {
            if (csvFileId) await deleteFile(csvFileId);
            csvFileId = await uploadSplitFile(file);
            display.textContent = file.name;
            display.style.color = 'var(--color-success)';
            showToast('CSV cargado correctamente', 'success');
        } catch (error) {
            display.textContent = error.message;
            display.style.color = 'var(--color-error)';
            csvFileId = null;
            e.target.value = '';
            showToast(error.message, 'error');
        }
        updateSplitButton();
    });

    document.getElementById('metadataFile').addEventListener('change', async function (e) {
        var file = e.target.files[0];
        var display = document.getElementById('metadataFileName');

        if (!file) {
            display.textContent = 'Ningun archivo seleccionado';
            display.style.color = '';
            if (metadataFileId) { await deleteFile(metadataFileId); metadataFileId = null; }
            updateSplitButton();
            return;
        }

        if (!file.name.toLowerCase().endsWith('.json')) {
            display.textContent = 'El archivo debe ser JSON';
            display.style.color = 'var(--color-error)';
            e.target.value = '';
            showToast('Solo se aceptan archivos JSON', 'error');
            return;
        }

        display.textContent = 'Subiendo ' + file.name + '...';
        display.style.color = '';

        try {
            if (metadataFileId) await deleteFile(metadataFileId);
            metadataFileId = await uploadSplitFile(file);
            display.textContent = file.name;
            display.style.color = 'var(--color-success)';
            showToast('Metadata cargado correctamente', 'success');
        } catch (error) {
            display.textContent = error.message;
            display.style.color = 'var(--color-error)';
            metadataFileId = null;
            e.target.value = '';
            showToast(error.message, 'error');
        }
        updateSplitButton();
    });

    // ── Form submit ──────────────────────────────────────────────────────

    splitForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        if (!csvFileId || !metadataFileId) {
            showToast('Sube ambos archivos (CSV y JSON)', 'error');
            return;
        }

        splitBtn.disabled = true;
        var originalText = splitBtn.textContent;
        splitBtn.textContent = 'Procesando...';

        try {
            showLoader(true, 'Dividiendo Golden Record en templates...');
            var result = await processSplit(csvFileId, metadataFileId);
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
            updateSplitButton();
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
});
