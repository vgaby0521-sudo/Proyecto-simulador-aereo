# 🛰️ Simulador de Tráfico Aéreo Distribuido

**Proyecto Final - Sistemas Operativos**

Sistema distribuido que simula control de tráfico aéreo en tiempo real usando 5 máquinas cooperantes.

## 👥 Equipo

- Valentina Martínez
- Ana Gabriela Varon
- Hary Ortiz
- Juan Pérez
- Osnaider Narváez

**Docente:** Roger Guzmán

---

## 🏗️ Arquitectura del Sistema

El sistema está compuesto por 5 módulos independientes que se comunican mediante sockets TCP:

| Máquina | Módulo | Rol | Puerto |
|---------|--------|-----|--------|
| **M1** | `m1_coordinador.py` | Servidor Central / Coordinador | 5555 |
| **M2** | `m2_simulador.py` | Simulador de Vuelos | - |
| **M3** | `m3_base_datos.py` | Registro Persistente | - |
| **M4** | `m4_mapa.py` | Visualizador Web | 5000 |
| **M5** | `m5_control.py` | Panel de Control | - |

---

## ✨ Características Implementadas

### Conceptos de Sistemas Operativos

✅ **Comunicación entre Procesos (IPC)**
- Sockets TCP para comunicación en red
- Mensajes JSON estructurados

✅ **Concurrencia**
- Multithreading en cada módulo
- Manejo simultáneo de múltiples conexiones

✅ **Balanceo de Carga**
- Algoritmo Round Robin para distribución equitativa
- Reparto de actualizaciones entre nodos

✅ **Tolerancia a Fallos**
- Reconexión automática de módulos
- Failover cuando un nodo falla
- Detección de desconexiones

✅ **Sincronización**
- Lock threading para recursos compartidos
- IDs globales para evitar duplicados
- Orden garantizado de mensajes

✅ **Contenerización**
- Cada módulo en contenedor Docker aislado
- Orquestación con Docker Compose
- Red privada para comunicación

### Cálculos Matemáticos Avanzados

📐 **Fórmula de Haversine**
\`\`\`
d = 2R · arctan2(√a, √(1-a))
\`\`\`
Calcula distancia real entre aeropuertos considerando curvatura terrestre.

📐 **Cálculo de Rumbo (Bearing)**
\`\`\`
θ = arctan2(sin(Δλ)cos(φ₂), cos(φ₁)sin(φ₂) - sin(φ₁)cos(φ₂)cos(Δλ))
\`\`\`
Determina dirección de navegación.

📐 **Interpolación Esférica (Slerp)**
\`\`\`
P(t) = sin((1-t)Ω)/sinΩ · P₀ + sin(tΩ)/sinΩ · P₁
\`\`\`
Movimiento suave sobre la superficie terrestre.

📐 **Tiempo Estimado de Llegada (ETA)**
\`\`\`
ETA = Distancia_restante / Velocidad_actual
\`\`\`

---

## 🚀 Cómo Ejecutar el Proyecto

### Requisitos Previos

- **Docker** instalado ([Descargar Docker](https://www.docker.com/products/docker-desktop/))
- **Docker Compose** instalado (incluido con Docker Desktop)
- Al menos **4 GB de RAM** disponibles
- Puertos **5000** y **5555** libres

### Verificar Docker

\`\`\`bash
docker --version
docker-compose --version
\`\`\`

---

## 📦 Instalación y Ejecución

### Paso 1: Descargar el Proyecto

\`\`\`bash
# Si tienes el código en un ZIP, descomprímelo
unzip simulador-trafico-aereo.zip
cd simulador-trafico-aereo

# O clona desde Git (si aplica)
git clone <url-repositorio>
cd simulador-trafico-aereo
\`\`\`

### Paso 2: Construir y Ejecutar

\`\`\`bash
# Construir e iniciar todos los contenedores
docker-compose up --build
\`\`\`

Este comando:
1. ✅ Construye las imágenes Docker para cada módulo
2. ✅ Crea la red privada `trafico_aereo`
3. ✅ Inicia los 5 contenedores en orden
4. ✅ Muestra logs en tiempo real

### Paso 3: Acceder a los Servicios

Una vez iniciado, verás logs similares a:

\`\`\`
m1_coordinador | 🛰️  [M1-COORDINADOR] Servidor iniciado en 0.0.0.0:5555
m2_simulador   | ✈️  [M2-SIMULADOR] Conectado al coordinador
m3_base_datos  | 💾 [M3-BASE_DATOS] Conectado al coordinador
m4_mapa        | 🗺️  [M4-MAPA] Conectado al coordinador
m4_mapa        | 🚀 Iniciando servidor web...
m5_control     | 🎮 [M5-CONTROL] Conectado al coordinador
\`\`\`

#### 🗺️ Ver el Mapa en Tiempo Real

Abre tu navegador en:
\`\`\`
http://localhost:5000
\`\`\`

Verás:
- ✈️ Vuelos moviéndose en tiempo real
- 📊 Contador de vuelos activos
- 🛬 Notificaciones de llegadas
- 🌍 Trayectorias trazadas

#### 🎮 Usar el Panel de Control

En otra terminal:

\`\`\`bash
docker attach m5_control
\`\`\`

Comandos disponibles:
\`\`\`
pausa          - Pausar simulación
reanudar       - Reanudar simulación
max <número>   - Establecer máximo de vuelos (ej: max 15)
salir          - Cerrar panel
\`\`\`

**Para desconectar sin cerrar:** `Ctrl+P` seguido de `Ctrl+Q`

#### 💾 Ver Datos Guardados

Los vuelos completados se guardan en:
\`\`\`bash
cat data/vuelos_guardados.jsonl
\`\`\`

Cada línea es un vuelo en formato JSON.

---

## 🛠️ Comandos Útiles

### Ver Logs de un Módulo Específico

\`\`\`bash
# Ver logs del coordinador
docker logs -f m1_coordinador

# Ver logs del simulador
docker logs -f m2_simulador

# Ver logs de la base de datos
docker logs -f m3_base_datos
\`\`\`

### Detener el Sistema

\`\`\`bash
# Detener todos los contenedores
docker-compose down

# Detener y eliminar volúmenes (limpia datos)
docker-compose down -v
\`\`\`

### Reiniciar un Módulo Individual

\`\`\`bash
# Reiniciar solo el simulador
docker-compose restart m2_simulador

# Reiniciar el mapa
docker-compose restart m4_mapa
\`\`\`

### Ver Estado de Contenedores

\`\`\`bash
docker-compose ps
\`\`\`

### Limpiar Todo

\`\`\`bash
# Detener y eliminar contenedores
docker-compose down

# Eliminar imágenes construidas
docker-compose down --rmi all

# Eliminar todo (contenedores, imágenes, volúmenes)
docker system prune -a --volumes
\`\`\`

---

## 🧪 Pruebas de Tolerancia a Fallos

### Simular Fallo de un Módulo

\`\`\`bash
# Detener el simulador
docker stop m2_simulador

# El sistema debe continuar funcionando
# Los vuelos existentes siguen moviéndose

# Reiniciar el simulador
docker start m2_simulador
# Se reconecta automáticamente
\`\`\`

### Simular Fallo del Coordinador

\`\`\`bash
# Detener coordinador
docker stop m1_coordinador

# Los módulos intentan reconectar cada 5 segundos
# Logs mostrarán: "Reintentando en 5 segundos..."

# Reiniciar coordinador
docker start m1_coordinador
# Todos se reconectan automáticamente
\`\`\`

---

## 📁 Estructura del Proyecto

\`\`\`
simulador-trafico-aereo/
├── m1_coordinador.py        # Servidor central
├── m2_simulador.py          # Generador de vuelos
├── m3_base_datos.py         # Almacenamiento
├── m4_mapa.py               # Servidor Flask
├── m5_control.py            # Panel de control
├── templates/
│   └── index.html           # Interfaz web
├── Dockerfile.m1            # Imagen para M1
├── Dockerfile.m2            # Imagen para M2
├── Dockerfile.m3            # Imagen para M3
├── Dockerfile.m4            # Imagen para M4
├── Dockerfile.m5            # Imagen para M5
├── docker-compose.yml       # Orquestación
├── data/                    # Volumen persistente
│   └── vuelos_guardados.jsonl
└── README.md                # Esta documentación
\`\`\`

---

## 🔍 Verificación de Funcionalidades

### ✅ Checklist de Pruebas

- [ ] Los 5 contenedores inician correctamente
- [ ] El mapa muestra vuelos en movimiento
- [ ] Los comandos del panel de control funcionan
- [ ] Los vuelos se guardan en `data/vuelos_guardados.jsonl`
- [ ] Las estadísticas se actualizan en tiempo real
- [ ] El sistema se recupera al reiniciar un módulo
- [ ] El balanceo Round Robin distribuye mensajes
- [ ] Las trayectorias son curvas realistas (Slerp)
- [ ] Los cálculos de distancia son correctos (Haversine)

---

## 🎓 Conceptos Demostrados

### 1. Procesos e IPC
- Cada contenedor = proceso aislado
- Comunicación mediante sockets TCP
- Intercambio de mensajes JSON

### 2. Concurrencia
- Threads para manejo de conexiones
- Locks para proteger datos compartidos
- Operaciones paralelas

### 3. Sistemas Distribuidos
- 5 nodos independientes cooperando
- Coordinación centralizada
- Sin punto único de falla

### 4. Balanceo de Carga
- Round Robin para distribución equitativa
- Detección de nodos activos
- Reasignación dinámica

### 5. Tolerancia a Fallos
- Reconexión automática
- Failover entre nodos
- Continuidad del servicio

---

## 🐛 Solución de Problemas

### Error: "Puerto 5000 ya en uso"

\`\`\`bash
# Cambiar puerto en docker-compose.yml
# Línea de m4_mapa:
ports:
  - "8000:5000"  # Usar puerto 8000 en su lugar
\`\`\`

### Error: "Cannot connect to Docker daemon"

\`\`\`bash
# Iniciar Docker Desktop
# O en Linux:
sudo systemctl start docker
\`\`\`

### Los contenedores no se conectan

\`\`\`bash
# Verificar red
docker network ls
docker network inspect trafico_aereo

# Recrear red
docker-compose down
docker-compose up --build
\`\`\`

### Ver más detalles de errores

\`\`\`bash
# Logs detallados
docker-compose logs --tail=100

# Inspeccionar contenedor
docker inspect m1_coordinador
\`\`\`

---

## 📊 Métricas y Monitoreo

### Ver estadísticas en tiempo real

El coordinador muestra cada 10 segundos:
\`\`\`
📊 ESTADO DEL SISTEMA
   Clientes activos: 4
   Mensajes enviados: 1523
   Mensajes recibidos: 1089
   Módulos conectados:
     • m2_simulador (simulador)
     • m3_base_datos (base_datos)
     • m4_mapa (visualizador)
     • m5_control (panel_control)
\`\`\`

### Estadísticas de vuelos

La base de datos muestra cada 30 segundos:
\`\`\`
📊 ESTADÍSTICAS DE VUELOS
   Total vuelos: 47
   Distancia total: 156892.34 km
   Velocidad promedio: 823.15 km/h
\`\`\`

---

## 🎯 Objetivos Cumplidos

✅ Sistema distribuido con 5 máquinas cooperantes
✅ Comunicación mediante sockets TCP
✅ Concurrencia con multithreading
✅ Balanceo de carga Round Robin
✅ Tolerancia a fallos con reconexión automática
✅ Cálculos matemáticos complejos (Haversine, Bearing, Slerp, ETA)
✅ Visualización en tiempo real con Flask/SocketIO
✅ Contenerización con Docker
✅ Panel de control interactivo
✅ Almacenamiento persistente

---

## 📞 Soporte

Para preguntas sobre el proyecto:
- Revisar logs: `docker-compose logs`
- Verificar conectividad: `docker network inspect trafico_aereo`
- Reiniciar sistema: `docker-compose restart`

---

## 📄 Licencia

Proyecto académico para Sistemas Operativos - Universidad [Nombre]

**Grupo N**  
**Docente:** Roger Guzmán  
**Año:** 2025

---

## 🎉 ¡Listo para Ejecutar!

\`\`\`bash
docker-compose up --build
\`\`\`

Luego abre: **http://localhost:5000**

¡Disfruta del simulador! ✈️🌍
