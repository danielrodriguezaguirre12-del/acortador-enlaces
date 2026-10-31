# Acortador de enlaces en AWS

Aplicación web que acorta URLs usando **Amazon S3** (interfaz), **Amazon EC2** (API FastAPI) y **Amazon DynamoDB** (persistencia). El identificador de cada enlace es un UUID generado en el backend.

```
Navegador ──► S3 (HTML/CSS/JS) ──fetch()──► EC2: FastAPI :8000 ──Boto3 (rol IAM)──► DynamoDB
     ▲                                            │
     └──────── 307 Temporary Redirect ◄───────────┘  (GET /{short_code})
```

## Estructura

```
acortador-enlaces/
├── backend/
│   ├── app/
│   │   ├── config.py     # Variables de entorno
│   │   ├── db.py         # Acceso a DynamoDB con Boto3
│   │   ├── schemas.py    # Modelos de entrada/salida (Pydantic)
│   │   └── main.py       # Endpoints y CORS
│   ├── requirements.txt
│   └── .env.example
├── frontend/             # Se sube a S3
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── config.js         # URL de la API en EC2
└── deploy/
    ├── acortador.service        # Servicio systemd
    ├── iam-policy-dynamodb.json # Política mínima del rol de EC2
    └── s3-bucket-policy.json    # Lectura pública del sitio
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/shorten` | Recibe `{"original_url": "..."}`, genera el UUID, lo guarda en DynamoDB y devuelve `short_code`, `original_url` y `short_url`. |
| GET | `/{short_code}` | Busca el UUID en DynamoDB y responde **307** hacia la URL original. **404** si no existe. |
| GET | `/urls/{short_code}` | Devuelve en JSON `short_code`, `original_url` y `created_at`. **404** si no existe. |
| GET | `/health` | Comprobación de estado. |

La documentación interactiva queda en `http://<ip-ec2>:8000/docs`.

## Desarrollo local

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # ajustar valores
uvicorn app.main:app --reload --port 8000
```

En local Boto3 usa las credenciales de `aws configure`. En EC2 usa el rol IAM; **no hay claves en el código ni en el repositorio**.

## Despliegue

### 1. DynamoDB
- Tabla: `short_links`
- Clave de partición: `short_code` (String)
- Modo de capacidad: bajo demanda

### 2. Rol IAM para EC2
1. IAM → Roles → Crear rol → Servicio de AWS → **EC2**.
2. Agregar una política en línea con el contenido de `deploy/iam-policy-dynamodb.json` (reemplazar `<ID-DE-CUENTA>`). Solo permite `PutItem` y `GetItem` sobre la tabla.
3. Nombre sugerido: `acortador-ec2-role`.

### 3. EC2
1. Lanzar una instancia **Amazon Linux 2023** (t2.micro / t3.micro), asociando el rol `acortador-ec2-role` en *Detalles avanzados → Perfil de instancia de IAM*.
2. Security Group:
   - TCP **8000** desde `0.0.0.0/0` (API).
   - TCP **22** solo desde **Mi IP** (SSH).
3. Conectarse por SSH y ejecutar:

```bash
sudo dnf install -y python3 python3-pip git
git clone https://github.com/danielrodriguezaguirre12-del/acortador-enlaces.git
cd acortador-enlaces/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

sudo tee /etc/acortador.env > /dev/null <<'EOF'
AWS_REGION=us-east-1
TABLE_NAME=short_links
BASE_URL=http://<ip-publica-ec2>:8000
ALLOWED_ORIGINS=http://<nombre-bucket>.s3-website-us-east-1.amazonaws.com
EOF

sudo cp ../deploy/acortador.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now acortador
sudo systemctl status acortador
```

> La IP pública cambia si la instancia se detiene; para que sea fija se puede asociar una Elastic IP.

### 4. S3 (interfaz)
1. Editar `frontend/config.js` con la IP pública de EC2.
2. Crear el bucket, desactivar *Bloquear todo el acceso público*.
3. Propiedades → **Alojamiento de sitios web estáticos** → habilitar, documento de índice `index.html`.
4. Permisos → política del bucket: `deploy/s3-bucket-policy.json` (reemplazar `<nombre-bucket>`).
5. Subir `index.html`, `styles.css`, `app.js` y `config.js`.
6. Abrir el endpoint `http://<nombre-bucket>.s3-website-us-east-1.amazonaws.com`.

> El endpoint de sitio web de S3 solo ofrece HTTP; por eso la API también se consume por HTTP (sin contenido mixto). Para HTTPS se usaría CloudFront.

## Pruebas

```bash
API=http://<ip-publica-ec2>:8000

# Crear enlace
curl -s -X POST $API/shorten -H "Content-Type: application/json" \
     -d '{"original_url":"https://www.example.com/articulos/arquitectura-cloud"}'

# Redirección real (ver cabecera Location y código 307)
curl -i $API/<short_code>

# Información del enlace
curl -s $API/urls/<short_code>

# UUID inexistente → 404
curl -i $API/00000000-0000-0000-0000-000000000000

# Persistencia tras reinicio
sudo systemctl restart acortador && curl -i $API/<short_code>
```

En la consola de DynamoDB (*Explorar elementos*) se puede comprobar cada registro guardado.
