// URL pública del backend FastAPI desplegado en EC2 (sin barra final).
// Cambiar por la IP pública de la instancia antes de subir a S3.
window.APP_CONFIG = {
  API_BASE_URL: "http://<ip-publica-ec2>:8000",
};
