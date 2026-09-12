# 🛡️ GuardianLicense — Asymmetric Software Licensing Engine

Un motor moderno de licenciamiento de software basado en **criptografía asimétrica Ed25519**. Diseñado para permitir a desarrolladores y empresas emitir licencias inviolables atadas a hardware, permitiendo que el software cliente verifique la autenticidad de forma offline sin comprometer nunca la clave privada del servidor.

---

## 🏛️ Arquitectura del Patrón

```
┌─────────────────────────┐                     ┌─────────────────────────┐
│     Servidor Emisor     │                     │     Cliente / SDK       │
│  (Clave Privada Ed25519)│                     │  (Clave Pública Ed25519)│
└───────────┬─────────────┘                     └────────────▲────────────┘
            │                                                │
            │ 1. Genera payload (dispositivo, vencimiento)  │ 3. Valida firma
            │ 2. Firma digitalmente con clave privada        │    y expiración
            ▼                                                │    sin conexión
     [ Licencia Firmada ] ───────────────────────────────────┘
```

### Principios de Diseño
1. **Verificación Asimétrica Offline:** El cliente solo necesita la clave pública integrada para verificar que la licencia no ha sido alterada.
2. **Imposibilidad de Falsificación:** Incluso si un usuario desensambla el software cliente, solo obtendrá la clave pública, la cual es matemáticamente incapaz de generar nuevas firmas.
3. **Payload Canónico:** Normalización estricta de JSON (`sort_keys=True`) para garantizar que la representación de bytes a firmar sea unívoca e invariable.

---

## 📂 Estructura del Proyecto

```text
guardian-license/
├── README.md
├── server/
│   ├── crypto.py      # Generación Ed25519, serialización canónica y firma
│   ├── models.py      # Esquemas de datos Pydantic para emisión
│   └── main.py        # API REST FastAPI para emisión de licencias
├── client-sdk/
│   └── verifier.py    # Verificador ligero offline para integrar en clientes
└── examples/
    └── demo_verify.py # Flujo end-to-end con pruebas positivas y de alteración
```

---

## 🚀 Inicio Rápido

### 1. Requisitos
```bash
pip install cryptography fastapi pydantic uvicorn
```

### 2. Ejecutar Demostración End-to-End
```bash
python examples/demo_verify.py
```

---

## ⚙️ Ciclo de Vida de Claves y Consideraciones de Producción

> [!NOTE]
> **Limitación conocida del entorno demo:**
> En este repositorio, el servidor genera un par de claves Ed25519 nuevo en memoria al arrancar (`generate_keypair()`). Esto se diseñó intencionalmente para permitir la ejecución inmediata del demo sin requerir configuración previa de archivos de entorno o bases de datos. 
> 
> Como consecuencia, si el proceso del servidor se reinicia, la clave pública cambia y las licencias emitidas en ejecuciones anteriores serán invalidadas.
> 
> **Implementación en Producción:**
> * **Persistencia de Clave Privada:** La clave privada del servidor debe generarse una sola vez y resguardarse en un servicio de gestión de secretos (e.g., AWS Secrets Manager, HashiCorp Vault) o en variables de entorno cifradas (`.env`), nunca en memoria volátil ni hardcodeada en el repositorio.
> * **Distribución de Clave Pública:** La clave pública permanece constante y se compila/empaqueta directamente dentro del binario del software cliente o SDK de verificación.

