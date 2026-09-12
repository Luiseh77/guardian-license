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
│   ├── crypto.py                # Generación Ed25519, serialización canónica y firma
│   ├── models.py                # Esquemas de datos Pydantic para emisión y sesiones
│   ├── sessions.py              # Almacén de sesiones en memoria y control de heartbeat
│   └── main.py                  # API REST FastAPI (licencias y endpoints de sesión)
├── client-sdk/
│   ├── verifier.py              # Verificador ligero offline para integrar en clientes
│   ├── hardware_id.py           # Huella digital de dispositivo (MAC, disco, hostname + SHA-256)
│   └── session.py               # Supervisor de sesión y bloqueo por expiración (Lockout)
└── examples/
    ├── demo_verify.py           # Flujo criptográfico (emisión, verificación y manipulación)
    ├── demo_hardware_binding.py # Prueba de vinculación de hardware y bloqueo de copias
    └── demo_session_lifecycle.py# Demostración de heartbeat y bloqueo por expiración
```

---

## 🚀 Inicio Rápido

### 1. Requisitos
```bash
pip install cryptography fastapi pydantic uvicorn
```

### 2. Ejecutar Demostraciones
```bash
# Prueba 1: Núcleo Criptográfico (Firma y Verificación)
python examples/demo_verify.py

# Prueba 2: Vinculación a Dispositivo (Hardware Binding)
python examples/demo_hardware_binding.py

# Prueba 3: Sesiones y Bloqueo por Expiración (Heartbeat Lifecycle)
python examples/demo_session_lifecycle.py
```

---

## 🔒 Vinculación a Dispositivo (Hardware Binding)

### ¿Qué es y por qué se utiliza?
La firma digital asimétrica garantiza que una licencia es legítima y no ha sido adulterada. Sin embargo, por sí sola **no impide que un usuario legítimo copie el archivo de licencia y lo distribuya a 50 computadoras diferentes**.

El **Hardware Binding** resuelve este problema atando criptográficamente la validez de la licencia a la identidad física de una máquina específica (`device_id`):

1. **Recolección de Parámetros:** El SDK del cliente extrae identificadores del equipo (dirección MAC, número de serie de disco/placa y hostname).
2. **Generación de Huella (Hash):** Se calcula un hash unívoco SHA-256 de los componentes combinados en formato `DEV-XXXXXXXX-XXXXXXXX-XXXXXXXX`.
3. **Inclusión en el Payload:** El servidor firma el `device_id` como parte inseparable del payload de la licencia.
4. **Validación Local:** Al iniciar, el cliente regenera su propia huella y la compara con la del payload firmado. Si difieren, la ejecución se bloquea inmediatamente, incluso si la firma criptográfica es 100% auténtica.

### Limitaciones Conocidas y Mitigación en Producción
* **Modificaciones Legítimas de Hardware:** Si un usuario reemplaza componentes de su equipo (por ejemplo, cambia el disco duro o la tarjeta de red), la huella calculada cambiará y la licencia dejará de coincidir.
* **Mecanismos de Producción:**
  * **Flujos de Re-activación:** En sistemas comerciales reales se implementa un endpoint de transferencia de licencias que permite a los usuarios revocar la máquina anterior y emitir una nueva para el nuevo hardware (con límites por año).
  * **Algoritmos de Tolerancia (Fuzzy Matching):** En lugar de un hash estricto único, algunos motores comerciales calculan hashes por componente individual (CPU, BIOS, Placa, Disco) y permiten la validación si al menos 3 de los 4 componentes coinciden.
  *(Estos flujos de re-activación y coincidencia difusa quedan fuera del alcance de este demo educativo).*

---

## ⏱️ Sesiones de Corta Duración y Bloqueo por Expiración

### ¿Qué problema resuelve?
Una licencia de largo plazo (ej. anual o perpetua) permite validar el software de forma offline, pero introduce un problema crítico de negocio: **¿qué ocurre si el cliente cancela su suscripción o comete fraude al segundo mes?**

Si la validación fuera puramente offline, el software seguiría funcionando libremente hasta que expire el año completo. Las **sesiones de corta duración** resuelven esto introduciendo supervisión activa en tiempo real:

1. **Inicio de Sesión:** Tras validar la licencia local, el software solicita al servidor un token de sesión efímero (ej. 5 a 15 minutos de validez).
2. **Ciclo de Heartbeat:** El cliente ejecuta un hilo en segundo plano que envía una señal periódica (*heartbeat*) antes de que expire la sesión, extendiendo la validez.
3. **Bloqueo Inmediato (Lockout):** Si el servidor revoca la sesión o el cliente pierde la conexión y no logra renovar antes del límite, el `SessionManager` activa un bloqueo de ejecución (`SessionExpiredError`), impidiendo que el usuario continúe utilizando las funciones protegidas.
4. **Rechazo de Renovación Tardía:** Si llega un heartbeat posterior a la expiración, el servidor lo rechaza de plano, obligando a una re-autenticación completa.

### Trade-off y Manejo de Tolerancia Offline
* **Trade-off:** Requiere que el software cliente tenga conexión periódica al servidor para mantener la sesión viva.
* **Mitigación en Producción (Período de Gracia):** Para evitar bloquear a un usuario legítimo por una caída temporal de su red local, los sistemas de producción implementan una **tolerancia de gracia offline** (ej. permitir 24 o 48 horas de operación desconectada antes de exigir un heartbeat forzoso). *(Este mecanismo de tolerancia extendida queda fuera del alcance de este demo educativo).*

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

