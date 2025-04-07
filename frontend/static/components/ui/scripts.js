document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('blog-form');
    const responseMessage = document.getElementById('response-message');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.querySelector('.progress-bar .progress');

    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            responseMessage.textContent = ''; // Limpiar mensajes previos

            // Mostrar barra de progreso
            progressContainer.classList.remove('hidden');
            progressBar.style.width = '0%'; // Reiniciar progreso

            const blogUrl = document.getElementById('blog-url').value;

            // Simular progreso inicial antes de la solicitud
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                progressBar.style.width = `${progress}%`;
                if (progress >= 90) clearInterval(interval); // Detener en 90% hasta que termine la solicitud
            }, 500);

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: blogUrl }),
                });

                const result = await response.json();

                if (response.ok) {
                    progressBar.style.width = '100%'; // Completar progreso
                    responseMessage.innerHTML = `
                        <p>Libro generado con éxito. <a href="${result.download_url}" target="_blank">Descargar aquí</a></p>
                    `;
                } else {
                    responseMessage.textContent = result.error || 'Error al generar el libro.';
                }
            } catch (error) {
                responseMessage.textContent = 'Error al conectar con el servidor.';
                console.error('Error:', error);
            } finally {
                clearInterval(interval); // Asegurarse de detener el progreso simulado
                progressBar.style.width = '100%'; // Completar progreso visualmente
                setTimeout(() => {
                    progressContainer.classList.add('hidden'); // Ocultar barra de progreso después de un tiempo
                }, 2000);
            }
        });
    }
});
