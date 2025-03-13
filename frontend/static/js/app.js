document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generateForm');
    const status = document.getElementById('status');
    const downloadSection = document.getElementById('downloadSection');
    
    const showLoading = () => {
        status.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Generando tu libro...</p>
                <div class="progress-bar">
                    <div class="progress"></div>
                </div>
            </div>
        `;
    };
    
    const showSuccess = (data) => {
        status.innerHTML = `
            <div class="alert-success fade-in">
                <i class="bi bi-check-circle-fill"></i>
                ¡Libro generado con éxito!
            </div>
        `;
        
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = data.download_url;
        downloadLink.download = data.filename;
        downloadSection.hidden = false;
    };
    
    const showError = (message) => {
        status.innerHTML = `
            <div class="alert-error fade-in">
                <i class="bi bi-x-circle-fill"></i>
                ${message}
            </div>
        `;
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const urlInput = document.getElementById('blogUrl');
        
        if (!urlInput.value) {
            showError('Por favor ingresa una URL válida');
            return;
        }
        
        showLoading();
        downloadSection.hidden = true;
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: urlInput.value })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error en el servidor');
            }
            
            const data = await response.json();
            showSuccess(data);
            
        } catch (error) {
            showError(error.message);
            console.error('Error:', error);
        }
    });
});