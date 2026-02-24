# 🛰️ Simulador de Tráfico Aéreo Distribuido

**Proyecto Final - Sistemas Operativos**

Sistema distribuido que simula control de tráfico aéreo en tiempo real usando 5 módulos cooperantes, implementado en Python con comunicación vía Sockets TCP.

## 👥 Equipo

- **Valentina Martínez**
- **Ana Gabriela Varon**
- **Hary Ortiz**
- **Juan Pérez**
- **Osnaider Narváez**

**Docente:** Roger Guzmán  
**Año:** 2025

---

## 🏗️ Arquitectura del Sistema

El sistema está compuesto por 5 módulos independientes que se comunican mediante sockets TCP:

| Máquina | Módulo | Rol | Puerto | Descripción |
|---------|--------|-----|--------|-------------|
| **M1** | `m1_coordinador.py` | Servidor Central | 5555 | Gestiona conexiones y enruta mensajes (Round Robin). |
| **M2** | `m2_simulador.py` | Simulador | - | Genera vuelos, calcula trayectorias y física. |
| **M3** | `m3_base_datos.py` | Base de Datos | - | Persistencia de vuelos en JSONL. |
| **M4** | `m4_mapa.py` | Visualizador | 5000 | Servidor Web (Flask) con mapa en tiempo real. |
| **M5** | `m5_control.py` | Control | - | CLI para gestionar la simulación. |

---

## ✨ Características Principales

### Conceptos de Sistemas Operativos
- **Comunicación entre Procesos (IPC):** Uso de Sockets TCP y mensajes JSON.
- **Concurrencia:** Multithreading para manejo simultáneo de conexiones y tareas.
- **Balanceo de Carga:** Distribución Round Robin de tareas.
- **Tolerancia a Fallos:** Reconexión automática y manejo de excepciones.
- **Sincronización:** Uso de `threading.Lock` para recursos compartidos.

### Funcionalidades de Simulación
- **Física Realista:** Cálculos de distancia (Haversine), rumbo (Bearing) y trayectorias curvas (Slerp).
- **Tiempo Real:** Actualización fluida de posiciones y estados.
- **Persistencia:** Guardado automático de historial de vuelos.
- **Interfaz Web:** Visualización interactiva con actualizaciones en vivo (SocketIO).

---

## 🚀 Guía de Ejecución

### Opción A: Usando Docker (Recomendada)

Si tienes Docker y Docker Compose instalados:

```bash
# Construir e iniciar el sistema
docker-compose up --build
```

Para detenerlo:
```bash
docker-compose down
```

### Opción B: Ejecución Manual (Sin Docker)

Si prefieres ejecutarlo localmente en tu máquina:

**1. Requisitos Previos**
- Python 3.8+
- Instalar dependencias:
  ```bash
  pip install flask flask-socketio
  ```

**2. Iniciar los Módulos (en terminales separadas)**

Orden recomendado de inicio:

**Terminal 1 (Coordinador):**
```bash
python m1_coordinador.py
```

**Terminal 2 (Base de Datos):**
```bash
python m3_base_datos.py
```

**Terminal 3 (Visualizador):**
```bash
python m4_mapa.py
```
> 🌍 **Accede al mapa en:** http://localhost:5000

**Terminal 4 (Simulador):**
```bash
python m2_simulador.py
```

**Terminal 5 (Panel de Control):**
```bash
python m5_control.py
```

---

## 🎮 Manual de Uso

### Visualizador Web
Abre **http://localhost:5000** en tu navegador para ver:
- Vuelos activos en el mapa.
- Trayectorias y actualizaciones en tiempo real.
- Tabla de vuelos con estado actual.

### Panel de Control (CLI)
Desde la terminal donde corre `m5_control.py`, usa estos comandos:

- `pausa`: Detiene temporalmente la simulación.
- `reanudar`: Continúa la simulación.
- `max <n>`: Cambia el límite de vuelos simultáneos (ej: `max 100`).
- `atc <id> alt <pies>`: Cambia la altitud de un vuelo (ej: `atc FL1234 alt 35000`).
- `atc <id> mayday`: Declara emergencia en un vuelo.
- `salir`: Cierra el panel de control.

---

## 📁 Estructura del Proyecto
