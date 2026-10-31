// Lógica de la interfaz: valida la URL, llama a la API en EC2 con fetch()
// y muestra el enlace corto. El UUID lo genera siempre el backend.
const API_BASE_URL = (window.APP_CONFIG?.API_BASE_URL || "").replace(/\/$/, "");

const form = document.getElementById("shorten-form");
const urlInput = document.getElementById("url-input");
const submitBtn = document.getElementById("submit-btn");
const errorBox = document.getElementById("error");
const resultBox = document.getElementById("result");
const shortUrlInput = document.getElementById("short-url");
const shortCodeEl = document.getElementById("short-code");
const openLink = document.getElementById("open-link");
const copyBtn = document.getElementById("copy-btn");
const copyStatus = document.getElementById("copy-status");

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearMessages() {
  errorBox.hidden = true;
  copyStatus.hidden = true;
}

function isValidUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessages();

  const originalUrl = urlInput.value.trim();
  if (!isValidUrl(originalUrl)) {
    showError("Ingresa una URL válida que empiece con http:// o https://");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Acortando...";

  try {
    const response = await fetch(`${API_BASE_URL}/shorten`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_url: originalUrl }),
    });

    if (!response.ok) {
      if (response.status === 422) {
        throw new Error("El backend rechazó la URL por no ser válida.");
      }
      throw new Error(`El backend respondió con un error (${response.status}).`);
    }

    const data = await response.json();
    shortUrlInput.value = data.short_url;
    shortCodeEl.textContent = data.short_code;
    openLink.href = data.short_url;
    resultBox.hidden = false;
  } catch (error) {
    resultBox.hidden = true;
    if (error instanceof TypeError) {
      // fetch lanza TypeError cuando no hay respuesta (servidor caído, CORS, red)
      showError("No se pudo conectar con el backend. Verifica que la API en EC2 esté en ejecución.");
    } else {
      showError(error.message);
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Acortar";
  }
});

// navigator.clipboard solo funciona en HTTPS; el sitio estático de S3 usa HTTP,
// así que se incluye un respaldo con execCommand.
async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  shortUrlInput.select();
  shortUrlInput.setSelectionRange(0, text.length);
  if (!document.execCommand("copy")) {
    throw new Error("copy failed");
  }
}

copyBtn.addEventListener("click", async () => {
  try {
    await copyText(shortUrlInput.value);
    copyStatus.hidden = false;
    setTimeout(() => (copyStatus.hidden = true), 2000);
  } catch {
    showError("No se pudo copiar automáticamente. Selecciona el enlace y cópialo manualmente.");
  }
});
