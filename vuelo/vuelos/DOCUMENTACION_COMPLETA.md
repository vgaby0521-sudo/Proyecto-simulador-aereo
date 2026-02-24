# 📚 DOCUMENTACIÓN COMPLETA DEL PROYECTO
## Simulador de Tráfico Aéreo Distribuido

---

## 🏗️ ARQUITECTURA GENERAL

El proyecto es un **sistema distribuido** compuesto por **5 módulos independientes** que se comunican mediante **sockets TCP** y **mensajes JSON**. Cada módulo corre en su propio **contenedor Docker** y se orquesta mediante **Docker Compose**.

### Diagrama de Comunicación:
```
┌─────────────────┐
│ M1_COORDINADOR  │ ← Servidor Central (Puerto 5555)
│  (Servidor)     │
└────────┬────────┘
         │
         ├───► M2_SIMULADOR (Genera vuelos)
         ├───► M3_BASE_DATOS (Almacena datos)
         ├───► M4_MAPA (Visualización web - Puerto 5000)
         └───► M5_CONTROL (Panel de control)
```

---

## 📦 MÓDULO 1: M1_COORDINADOR.PY

### **Rol:** Servidor Central / Coordinador
### **Puerto:** 5555
### **Tecnología:** Python con sockets TCP

### **Funcionalidades Principales:**

1. **Gestión de Conexiones**
   - Acepta conexiones de todos los módulos
   - Mantiene registro de clientes activos
   - Maneja desconexiones y reconexiones automáticas
   - Usa `threading.Lock()` para sincronización

2. **Enrutamiento de Mensajes**
   - **Broadcast**: Envía mensajes a todos los módulos (excepto el origen)
   - **Envío dirigido**: Envía mensajes a módulos específicos
   - **Round Robin**: Distribución equitativa de carga (preparado)

3. **Tipos de Mensajes que Procesa:**
   - `vuelo_nuevo` → Reenvía a todos + guarda en BD
   - `vuelo_update` → Reenvía actualizaciones de posición
   - `vuelo_completado` → Notifica llegada y actualiza BD
   - `comando` → Ejecuta comandos del panel de control
   - `comando_atc` → Reenvía comandos ATC al simulador
   - `solicitar_estadisticas` → Solicita stats a BD
   - `estadisticas` → Reenvía stats al mapa

4. **Monitoreo del Sistema**
   - Cada 30 segundos muestra:
     - Clientes activos
     - Vuelos activos
     - Mensajes enviados/recibidos
     - Mensajes por segundo
     - Lista de módulos conectados

### **Código Clave:**
```python
# Manejo de timeouts (no son errores)
except socket.timeout:
    continue  # Timeout esperado

# Guardar vuelo cuando despega
elif tipo == 'vuelo_nuevo':
    self.broadcast(mensaje, excluir=origen)
    self.enviar_a_modulo('m3_base_datos', {
        'tipo': 'guardar_vuelo',
        'vuelo': mensaje.get('vuelo')
    })
```

---

## ✈️ MÓDULO 2: M2_SIMULADOR.PY

### **Rol:** Generador y Simulador de Vuelos
### **Tecnología:** Python con cálculos matemáticos avanzados

### **Funcionalidades Principales:**

1. **Generación de Vuelos**
   - **84 aeropuertos** en todo el mundo (América, Europa, Asia, Oceanía, África, Medio Oriente)
   - Genera vuelos con:
     - ID único (ej: FL1234)
     - Origen y destino aleatorios
     - Distancia calculada con **Fórmula de Haversine**
     - Rumbo calculado con **Bearing**
     - Velocidad realista (700-950 km/h)
     - Altitud (30,000-40,000 pies)
     - Combustible calculado
     - **Hora de salida** (timestamp real)
     - **Hora estimada de llegada** (calculada)
     - **Imagen de avión** (URL de avión real aleatoria)
     - **Trayectoria** inicializada

2. **Cálculos Matemáticos Implementados:**

   **a) Fórmula de Haversine** (distancia entre puntos geográficos):
   ```python
   d = 2R · arcsin(√(sin²(Δφ/2) + cos(φ₁)cos(φ₂)sin²(Δλ/2)))
   ```
   - Considera la curvatura de la Tierra
   - R = 6371 km (radio terrestre)

   **b) Cálculo de Rumbo (Bearing)**:
   ```python
   θ = arctan2(sin(Δλ)cos(φ₂), cos(φ₁)sin(φ₂) - sin(φ₁)cos(φ₂)cos(Δλ))
   ```
   - Dirección de navegación en grados (0-360°)

   **c) Interpolación Esférica (Slerp)**:
   ```python
   P(t) = sin((1-t)Ω)/sinΩ · P₀ + sin(tΩ)/sinΩ · P₁
   ```
   - Movimiento suave sobre superficie esférica
   - Genera trayectorias curvas realistas

   **d) Tiempo Estimado de Llegada (ETA)**:
   ```python
   ETA = Distancia_restante / Velocidad_actual
   ```

3. **Actualización de Vuelos**
   - Cada 200ms (DT = 0.2s) actualiza:
     - Posición (lat/lon) usando Slerp
     - Progreso (0.0 a 1.0)
     - Consumo de combustible
     - Distancia restante
     - ETA actualizado
     - Trayectoria (últimos 1000 puntos)

4. **Simulación Avanzada**
   - **Factor de tiempo**: 1 segundo real = 60 segundos simulados
   - **Efectos de viento**: Afecta velocidad según dirección
   - **Emergencias aleatorias**: 0.1% probabilidad
   - **Clima dinámico**: Cambios aleatorios de viento/tormentas

5. **Gestión de Vuelos**
   - **Mínimo**: 50 vuelos al iniciar
   - **Máximo**: Configurable (50-50,000)
   - Genera nuevos vuelos hasta alcanzar el máximo
   - Elimina vuelos completados automáticamente

6. **Comandos ATC que Recibe**
   - `cambiar_altitud`: Modifica altitud en pies
   - `cambiar_velocidad`: Modifica velocidad en km/h
   - `emergencia`: Declara emergencia en vuelo

### **Estructura de un Vuelo:**
```python
vuelo = {
    'id': 'FL1234',
    'origen': {'code': 'JFK', 'nombre': 'Nueva York JFK', 'lat': 40.64, 'lon': -73.77},
    'destino': {'code': 'LAX', 'nombre': 'Los Ángeles', 'lat': 33.94, 'lon': -118.40},
    'distancia_total': 3944.0,  # km
    'rumbo': 270.5,  # grados
    'velocidad': 850,  # km/h
    'altitud': 35000,  # pies
    'progreso': 0.35,  # 0.0 a 1.0
    'lat_actual': 40.5,
    'lon_actual': -100.2,
    'combustible': 45000.0,  # litros
    'hora_salida': '2025-11-20T10:30:00',
    'hora_llegada_estimada': '2025-11-20T15:15:00',
    'imagen_avion': 'https://upload.wikimedia.org/...',
    'trayectoria': [[lat1, lon1], [lat2, lon2], ...],
    'activo': True,
    'emergencia': False
}
```

---

## 💾 MÓDULO 3: M3_BASE_DATOS.PY

### **Rol:** Almacenamiento Persistente
### **Tecnología:** Python con archivos JSONL (JSON Lines)

### **Funcionalidades Principales:**

1. **Almacenamiento de Vuelos**
   - **Formato**: JSONL (una línea JSON por vuelo)
   - **Ubicación**: `/data/vuelos_guardados.jsonl`
   - **Persistencia**: Volumen Docker montado en `./data/`

2. **Operaciones:**
   - **Guardar vuelo**: Cuando despega (con todos los atributos)
   - **Actualizar hora de llegada**: Cuando aterriza
   - **Calcular estadísticas**: Total vuelos, distancia, velocidad promedio, rutas populares

3. **Mensajes que Recibe:**
   - `guardar_vuelo`: Guarda vuelo completo al despegar
   - `vuelo_completado`: Actualiza hora de llegada real
   - `obtener_estadisticas`: Calcula y retorna estadísticas

4. **Estadísticas Calculadas:**
   ```python
   {
       'total_vuelos': 150,
       'distancia_total': 1250000.5,  # km
       'promedio_velocidad': 823.15,  # km/h
       'rutas_populares': [
           ('JFK-LAX', 25),
           ('LHR-FRA', 18),
           ...
       ]
   }
   ```

5. **Tolerancia a Fallos**
   - Reconexión automática cada 5 segundos
   - Sincronización con disco (`os.fsync()`)
   - Thread-safe con `threading.Lock()`

### **Ejemplo de Registro en JSONL:**
```json
{"id":"FL1234","origen":{"code":"JFK","nombre":"Nueva York JFK","lat":40.64,"lon":-73.77},"destino":{"code":"LAX","nombre":"Los Ángeles","lat":33.94,"lon":-118.40},"distancia_total":3944.0,"velocidad":850,"altitud":35000,"hora_salida":"2025-11-20T10:30:00","hora_llegada_estimada":"2025-11-20T15:15:00","guardado_en":"2025-11-20T10:30:05","timestamp_unix":1732096205.0}
```

---

## 🗺️ MÓDULO 4: M4_MAPA.PY

### **Rol:** Visualizador Web Interactivo
### **Puerto:** 5000
### **Tecnología:** Flask + Flask-SocketIO + Leaflet.js

### **Funcionalidades Principales:**

1. **Servidor Web Flask**
   - Ruta `/`: Sirve `templates/index.html`
   - WebSocket con Socket.IO para comunicación en tiempo real

2. **Comunicación Bidireccional:**
   - **Recibe del coordinador:**
     - `vuelo_nuevo` → Emite a clientes web
     - `vuelo_update` → Actualiza posición en mapa
     - `vuelo_completado` → Elimina vuelo del mapa
     - `estadisticas` → Muestra estadísticas
   
   - **Recibe de clientes web:**
     - `solicitar_vuelos` → Envía vuelos actuales
     - `pedir_estadisticas` → Solicita stats a BD
     - `comando_atc` → Reenvía al coordinador

3. **Eventos Socket.IO:**
   - `connect`: Cliente conectado
   - `disconnect`: Cliente desconectado
   - `nuevo_vuelo`: Nuevo vuelo en mapa
   - `actualizar_vuelo`: Actualización de posición
   - `vuelos_iniciales`: Lista de vuelos al conectar
   - `estadisticas_actualizadas`: Stats actualizadas

### **Frontend (templates/index.html):**

1. **Tecnologías:**
   - **Leaflet.js**: Mapa interactivo
   - **Socket.IO Client**: Comunicación WebSocket
   - **CSS3**: Diseño moderno y responsive
   - **JavaScript ES6+**: Lógica del cliente

2. **Características del Mapa:**
   - Mapa mundial con tiles de OpenStreetMap
   - Marcadores de aviones con iconos personalizados
   - **Trayectorias visibles** (polilíneas)
   - Actualización en tiempo real
   - Zoom y pan interactivos

3. **Panel de Información de Vuelo:**
   - **Imagen de avión real** (URL de Wikipedia)
   - **Hora de salida** formateada
   - **Hora estimada de llegada** formateada
   - Estado (En Vuelo / Emergencia)
   - Altitud, velocidad, combustible
   - Distancia total y recorrida
   - Rumbo y progreso
   - **Barra de progreso animada**

4. **Funcionalidades Interactivas:**
   - Click en avión → Muestra detalles
   - Búsqueda de vuelos por ID
   - Estadísticas en tiempo real
   - Notificaciones de eventos
   - Contador de vuelos activos/completados

5. **Estilos CSS:**
   - Diseño oscuro moderno
   - Animaciones suaves
   - Responsive design
   - Tarjetas de información destacadas

---

## 🎮 MÓDULO 5: M5_CONTROL.PY

### **Rol:** Panel de Control Interactivo
### **Tecnología:** Python con entrada de consola

### **Funcionalidades Principales:**

1. **Comandos Disponibles:**
   - `pausa` → Pausa la simulación
   - `reanudar` → Reanuda la simulación
   - `max <número>` → Establece máximo de vuelos (50-50,000)
   - `atc <id> alt <n>` → Cambia altitud de vuelo
   - `atc <id> vel <n>` → Cambia velocidad de vuelo
   - `atc <id> mayday` → Declara emergencia
   - `salir` → Cierra el panel
   - `ayuda` → Muestra menú de comandos

2. **Interfaz:**
   - Menú interactivo en consola
   - Validación de comandos
   - Mensajes de confirmación
   - Manejo de errores

3. **Comunicación:**
   - Envía comandos al coordinador
   - El coordinador reenvía al simulador
   - Feedback inmediato

---

## 🐳 DOCKER Y ORQUESTACIÓN

### **docker-compose.yml:**

```yaml
services:
  m1_coordinador:  # Servidor central
  m2_simulador:    # Generador de vuelos
  m3_base_datos:   # Almacenamiento
  m4_mapa:         # Visualización web
  m5_control:      # Panel de control

networks:
  trafico_aereo:   # Red privada Docker
```

### **Características:**
- **Red privada**: Todos los módulos en la misma red
- **Volúmenes**: Datos persistentes en `./data/`
- **Puertos expuestos**: 5000 (mapa), 5555 (coordinador)
- **Restart policy**: `unless-stopped` (reinicio automático)
- **Dependencias**: M2, M3, M4, M5 dependen de M1

### **Dockerfiles:**
- **Dockerfile.m1-m5**: Imágenes Python 3.11-slim
- **Dockerfile.m4**: Instala Flask y Flask-SocketIO
- **Dockerfile.m3**: Crea directorio `/data`

---

## 🔄 FLUJO DE COMUNICACIÓN

### **1. Inicio del Sistema:**
```
M1 inicia → Escucha en puerto 5555
M2 conecta → Se registra como 'simulador'
M3 conecta → Se registra como 'base_datos'
M4 conecta → Se registra como 'visualizador'
M5 conecta → Se registra como 'panel_control'
```

### **2. Generación de Vuelo:**
```
M2 genera vuelo → Envía 'vuelo_nuevo' a M1
M1 recibe → Broadcast a todos (excepto M2)
M1 también → Envía 'guardar_vuelo' a M3
M3 recibe → Guarda en JSONL
M4 recibe → Emite a clientes web vía Socket.IO
Cliente web → Muestra vuelo en mapa
```

### **3. Actualización de Vuelo:**
```
M2 actualiza posición → Envía 'vuelo_update' a M1
M1 recibe → Broadcast a todos
M4 recibe → Emite 'actualizar_vuelo' vía Socket.IO
Cliente web → Actualiza marcador y trayectoria
```

### **4. Completar Vuelo:**
```
M2 detecta progreso = 1.0 → Envía 'vuelo_completado' a M1
M1 recibe → Envía a M3 (actualizar hora llegada)
M1 también → Broadcast a todos
M4 recibe → Emite 'vuelo_completado' vía Socket.IO
Cliente web → Elimina vuelo del mapa
```

### **5. Solicitar Estadísticas:**
```
Cliente web → Socket.IO 'pedir_estadisticas'
M4 recibe → Envía 'solicitar_estadisticas' a M1
M1 recibe → Reenvía a M3
M3 calcula → Envía 'estadisticas' a M1
M1 recibe → Reenvía a M4
M4 recibe → Emite 'estadisticas_actualizadas' vía Socket.IO
Cliente web → Muestra estadísticas
```

---

## 📊 CONCEPTOS DE SISTEMAS OPERATIVOS IMPLEMENTADOS

### **1. Comunicación entre Procesos (IPC)**
- ✅ Sockets TCP para comunicación en red
- ✅ Mensajes JSON estructurados
- ✅ Protocolo de mensajería definido

### **2. Concurrencia**
- ✅ Multithreading en cada módulo
- ✅ `threading.Lock()` para sincronización
- ✅ Manejo simultáneo de conexiones

### **3. Balanceo de Carga**
- ✅ Round Robin preparado (índice rotativo)
- ✅ Distribución equitativa de mensajes
- ✅ Detección de nodos activos

### **4. Tolerancia a Fallos**
- ✅ Reconexión automática (cada 5 segundos)
- ✅ Manejo de desconexiones
- ✅ Continuidad del servicio

### **5. Sincronización**
- ✅ Locks para recursos compartidos
- ✅ IDs globales únicos
- ✅ Orden garantizado de mensajes

### **6. Contenerización**
- ✅ Cada módulo en contenedor Docker
- ✅ Aislamiento de procesos
- ✅ Orquestación con Docker Compose

---

## 🎯 FUNCIONALIDADES ESPECÍFICAS IMPLEMENTADAS

### ✅ **1. Guardado Automático de Vuelos**
- Cada vuelo se guarda en BD **inmediatamente al despegar**
- Incluye todos los atributos y cálculos
- Hora de salida y llegada estimada guardadas

### ✅ **2. Trayectorias Visibles**
- Trayectoria completa dibujada en mapa
- Actualización dinámica en tiempo real
- Polilíneas de Leaflet.js

### ✅ **3. Estadísticas Funcionales**
- Total de vuelos guardados
- Distancia acumulada
- Velocidad promedio
- Rutas más populares (top 5)

### ✅ **4. Simulador con Mínimo 50 Vuelos**
- Inicia con mínimo 50 vuelos activos
- Máximo configurable: 50-50,000
- Generación automática hasta alcanzar máximo

### ✅ **5. Panel de Información Mejorado**
- Foto de avión real (URLs de Wikipedia)
- Hora de salida formateada
- Hora estimada de llegada formateada
- Diseño moderno con tarjetas destacadas

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
operating-systems-project/
├── m1_coordinador.py      # Servidor central
├── m2_simulador.py         # Simulador de vuelos
├── m3_base_datos.py        # Base de datos
├── m4_mapa.py              # Servidor Flask
├── m5_control.py           # Panel de control
├── docker-compose.yml      # Orquestación
├── Dockerfile.m1-m5        # Imágenes Docker
├── templates/
│   └── index.html          # Frontend web
├── data/
│   └── vuelos_guardados.jsonl  # Datos persistentes
└── README.md               # Documentación
```

---

## 🚀 CÓMO FUNCIONA TODO JUNTO

1. **Inicio:**
   ```bash
   docker-compose up --build
   ```
   - Construye imágenes
   - Crea red privada
   - Inicia 5 contenedores

2. **M1 (Coordinador)** inicia primero y escucha en puerto 5555

3. **M2, M3, M4, M5** se conectan automáticamente

4. **M2** genera 50 vuelos iniciales y los envía a M1

5. **M1** reenvía a M3 (guardar) y M4 (mostrar)

6. **M4** emite vía Socket.IO a clientes web

7. **Cliente web** abre http://localhost:5000 y ve vuelos en tiempo real

8. **M2** actualiza posiciones cada 200ms

9. **M4** actualiza mapa en tiempo real

10. **M3** guarda vuelos y calcula estadísticas

11. **M5** permite controlar la simulación

---

## 🔧 CONFIGURACIÓN Y PARÁMETROS

### **Parámetros del Simulador:**
- `FACTOR_TIEMPO = 60`: 1 segundo real = 60 segundos simulados
- `DT = 0.2`: Tick de simulación (200ms)
- `RADIO_TIERRA = 6371.0`: Radio terrestre en km
- `max_vuelos`: 50-50,000 (configurable)

### **Aeropuertos:**
- 84 aeropuertos en 6 continentes
- Códigos IATA reales
- Coordenadas GPS precisas

### **Velocidades:**
- Rango: 700-950 km/h
- Basadas en velocidades reales de aviones comerciales

### **Altitudes:**
- Rango: 30,000-40,000 pies
- Típicas de vuelos comerciales

---

## 📈 MÉTRICAS Y MONITOREO

### **M1 (Coordinador) muestra cada 30s:**
- Clientes activos
- Vuelos activos
- Mensajes enviados/recibidos
- Mensajes por segundo
- Lista de módulos

### **M3 (Base de Datos) muestra cada 30s:**
- Total vuelos guardados
- Distancia acumulada
- Velocidad promedio
- Rutas populares

---

## 🎨 INTERFAZ WEB

### **Características:**
- Mapa mundial interactivo
- Marcadores de aviones animados
- Trayectorias visibles
- Panel lateral con detalles
- Estadísticas en tiempo real
- Búsqueda de vuelos
- Diseño responsive

### **Colores y Estilos:**
- Tema oscuro moderno
- Azul para vuelos normales
- Rojo para emergencias
- Amarillo para hora de salida
- Verde para hora de llegada

---

## 🐛 MANEJO DE ERRORES

### **Tolerancia a Fallos:**
- Reconexión automática cada 5 segundos
- Manejo de timeouts (no son errores)
- Validación de datos JSON
- Try-catch en operaciones críticas

### **Logs:**
- Emojis para fácil identificación
- Timestamps en mensajes importantes
- Errores claramente marcados
- Información de debug

---

## 📝 RESUMEN TÉCNICO

**Lenguaje:** Python 3.11  
**Comunicación:** Sockets TCP + JSON  
**Web:** Flask + Flask-SocketIO  
**Frontend:** HTML5 + CSS3 + JavaScript + Leaflet.js  
**Contenerización:** Docker + Docker Compose  
**Almacenamiento:** JSONL (JSON Lines)  
**Matemáticas:** Haversine, Bearing, Slerp, ETA  
**Concurrencia:** Threading  
**Sincronización:** Locks  
**Tolerancia a Fallos:** Reconexión automática  

---

## ✅ CHECKLIST DE FUNCIONALIDADES

- [x] 5 módulos independientes comunicándose
- [x] Guardado automático de vuelos al despegar
- [x] Trayectorias visibles en mapa
- [x] Estadísticas funcionales
- [x] Mínimo 50 vuelos al iniciar
- [x] Panel con foto de avión real
- [x] Hora de salida y llegada estimada
- [x] Cálculos matemáticos avanzados
- [x] Tolerancia a fallos
- [x] Interfaz web moderna
- [x] Panel de control interactivo
- [x] Contenerización completa

---

**¡El proyecto está completo y funcional!** 🎉

