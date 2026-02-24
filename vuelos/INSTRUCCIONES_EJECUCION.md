# 🚀 GUÍA RÁPIDA DE EJECUCIÓN

## Para el Profesor o Evaluador

### Requisitos
- Docker Desktop instalado y ejecutándose
- Puertos 5000 y 5555 disponibles

### Ejecución en 3 Pasos

#### 1️⃣ Iniciar el Sistema
\`\`\`bash
docker-compose up --build
\`\`\`

Espera a ver estos mensajes:
\`\`\`
✓ m1_coordinador | 🛰️ Servidor iniciado
✓ m2_simulador   | ✈️ Conectado al coordinador
✓ m3_base_datos  | 💾 Conectado al coordinador
✓ m4_mapa        | 🗺️ Acceso web: http://localhost:5000
✓ m5_control     | 🎮 Panel de control listo
\`\`\`

#### 2️⃣ Ver la Simulación
Abre tu navegador en:
\`\`\`
http://localhost:5000
\`\`\`

Verás:
- Vuelos moviéndose en tiempo real sobre el mapa
- Trayectorias curvas (usando Slerp)
- Estadísticas actualizándose
- Notificaciones de llegadas

#### 3️⃣ Probar el Panel de Control
En otra terminal:
\`\`\`bash
docker attach m5_control
\`\`\`

Prueba comandos:
\`\`\`
pausa       # Detiene la simulación
reanudar    # Continúa la simulación
max 20      # Aumenta vuelos simultáneos
salir       # Cierra el panel
\`\`\`

Para salir sin cerrar: `Ctrl+P` + `Ctrl+Q`

---

## Verificación de Conceptos

### ✅ Concurrencia
Cada módulo usa threads independientes. Ver logs:
\`\`\`bash
docker logs m1_coordinador
\`\`\`

### ✅ Balanceo Round Robin
El coordinador distribuye mensajes equitativamente entre nodos.

### ✅ Tolerancia a Fallos
Prueba detener un módulo:
\`\`\`bash
docker stop m2_simulador
# El sistema continúa funcionando
docker start m2_simulador
# Se reconecta automáticamente
\`\`\`

### ✅ Cálculos Matemáticos
- **Haversine**: Distancia real entre aeropuertos
- **Bearing**: Rumbo de navegación
- **Slerp**: Trayectorias curvas suaves
- **ETA**: Tiempo estimado dinámico

Todos visibles en los popups del mapa.

### ✅ Datos Persistentes
\`\`\`bash
cat data/vuelos_guardados.jsonl
\`\`\`

---

## Detener el Sistema
\`\`\`bash
docker-compose down
\`\`\`

---

## Troubleshooting Rápido

**Error: Puerto ocupado**
\`\`\`bash
# Cambiar puerto 5000 a 8000 en docker-compose.yml
\`\`\`

**No conecta**
\`\`\`bash
docker-compose down
docker-compose up --build
\`\`\`

**Ver logs específicos**
\`\`\`bash
docker logs -f <nombre_contenedor>
\`\`\`

---

## Tiempo Estimado
- Construcción inicial: ~2-3 minutos
- Ejecución: Inmediata
- Evaluación completa: ~10-15 minutos

---

**¡Sistema listo para demostración y evaluación!** 🎓
