"""
M4 - VISUALIZADOR CON FLASK Y SOCKETIO
Muestra vuelos en tiempo real en un mapa interactivo
"""
import socket
import json
import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os
import math
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simulador_trafico_aereo_2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class VisualizadorMapa:
    def __init__(self, coordinador_host='localhost', coordinador_port=5555):
        hosts_env = os.getenv('COORDINADOR_HOSTS')
        host_env = os.getenv('COORDINADOR_HOST')
        port_env = os.getenv('COORDINADOR_PORT')
        self.coordinador_port = int(port_env) if port_env else coordinador_port
        self.hosts = [h.strip() for h in hosts_env.split(',')] if hosts_env else [host_env.strip() if host_env else coordinador_host]
        self.coordinador_host = self.hosts[0]
        self.socket_coord = None
        self.running = True
        self.vuelos_activos = {}
        self.lock = threading.Lock()
        self.simulador_offline = False
        self.FACTOR_TIEMPO = 180
        self.DT = 0.2
        self.ultima_actualizacion = {}
        
    def conectar(self):
        while self.running:
            for host in self.hosts:
                try:
                    self.socket_coord = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket_coord.connect((host, self.coordinador_port))
                    info = {
                        'nombre': 'm4_mapa',
                        'tipo': 'visualizador',
                        'version': '1.0'
                    }
                    self.socket_coord.send(json.dumps(info).encode('utf-8'))
                    respuesta_raw = self.socket_coord.recv(1024).decode('utf-8')
                    respuesta_linea = respuesta_raw.split('\n', 1)[0].strip()
                    confirmacion = json.loads(respuesta_linea)
                    if confirmacion['status'] == 'OK':
                        with self.lock:
                            self.vuelos_activos = {}
                        self.coordinador_host = host
                        print(f"🗺️  [M4-MAPA] Conectado al coordinador en {host}:{self.coordinador_port}")
                        print(f"   Acceso web: http://localhost:5000")
                        return True
                except Exception as e:
                    print(f"❌ Error conectando a {host}:{self.coordinador_port}: {e}")
            print("   Reintentando en 5 segundos...")
            time.sleep(5)
        return False
    
    def recibir_actualizaciones(self):
        """Recibe actualizaciones de vuelos del coordinador"""
        buffer = ""
        while self.running:
            try:
                data = self.socket_coord.recv(8192)
                if not data:
                    print("⚠️  Conexión cerrada por el coordinador")
                    break
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    linea, buffer = buffer.split('\n', 1)
                    if linea.strip():
                        try:
                            mensaje = json.loads(linea)
                            self.procesar_mensaje(mensaje)
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Error JSON en línea: {linea[:100]}")
                        
            except Exception as e:
                print(f"❌ Error recibiendo actualizaciones: {e}")
                break
        
        print("🔄 Intentando reconectar...")
        time.sleep(5)  # Tolerancia a fallos: esperar antes de reconectar
        if self.running:
            try:
                self.conectar()
                threading.Thread(target=self.recibir_actualizaciones, daemon=True).start()
            except Exception as e:
                print(f"❌ Error en reconexión: {e}")
                # Reintentar después de otro intervalo
                if self.running:
                    threading.Thread(target=self.recibir_actualizaciones, daemon=True).start()

    def procesar_mensaje(self, mensaje):
        """Procesa un mensaje recibido"""
        tipo = mensaje.get('tipo')
        
        if tipo == 'vuelo_nuevo':
            vuelo = mensaje.get('vuelo')
            if vuelo:
                with self.lock:
                    self.vuelos_activos[vuelo['id']] = vuelo
                    if not vuelo.get('lat_actual') or not vuelo.get('lon_actual'):
                        vuelo['lat_actual'] = vuelo['origen']['lat']
                        vuelo['lon_actual'] = vuelo['origen']['lon']
                    vuelo['trayectoria'] = (vuelo.get('trayectoria') or []) + [[vuelo['lat_actual'], vuelo['lon_actual']]]
                    self.ultima_actualizacion[vuelo['id']] = time.time()
                print(f"✈️  Nuevo vuelo en mapa: {vuelo['id']}")
                # Emitir a todos los clientes web
                socketio.emit('nuevo_vuelo', vuelo, namespace='/')
        
        elif tipo == 'vuelo_update':
            vuelo = mensaje.get('vuelo')
            if vuelo:
                vuelo_id = vuelo['id']
                with self.lock:
                    if vuelo_id in self.vuelos_activos:
                        self.vuelos_activos[vuelo_id] = vuelo
                        v = self.vuelos_activos[vuelo_id]
                        if not v.get('lat_actual') or not v.get('lon_actual'):
                            t = v.get('progreso') or 0.0
                            lat, lon = self.slerp(
                                v['origen']['lat'], v['origen']['lon'],
                                v['destino']['lat'], v['destino']['lon'],
                                t
                            )
                            v['lat_actual'] = lat
                            v['lon_actual'] = lon
                        v['trayectoria'] = (v.get('trayectoria') or []) + [[v['lat_actual'], v['lon_actual']]]
                        self.ultima_actualizacion[vuelo_id] = time.time()
                # Emitir actualización
                socketio.emit('actualizar_vuelo', vuelo, namespace='/')
        
        elif tipo == 'vuelo_completado':
            vuelo = mensaje.get('vuelo')
            if vuelo:
                vuelo_id = vuelo['id']
                with self.lock:
                    if vuelo_id in self.vuelos_activos:
                        del self.vuelos_activos[vuelo_id]
                # Notificar llegada
                socketio.emit('vuelo_completado', vuelo, namespace='/')
                print(f"🛬 Vuelo completado: {vuelo_id}")
        
        elif tipo == 'estadisticas':
            datos = mensaje.get('datos')
            if datos:
                print(f"📊 Estadísticas recibidas: {datos.get('total_vuelos', 0)} vuelos totales")
                socketio.emit('estadisticas_actualizadas', datos, namespace='/')
        elif tipo == 'simulador_offline':
            self.simulador_offline = True
            threading.Thread(target=self.loop_local, daemon=True).start()
        elif tipo == 'simulador_online':
            self.simulador_offline = False
        elif tipo == 'guardar_vuelo_backup':
            try:
                payload = mensaje.get('payload')
                ruta = os.path.join('data', 'vuelos_backup.jsonl')
                with open(ruta, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(payload) + '\n')
            except Exception as e:
                print(f"❌ Error guardando backup: {e}")
        elif tipo == 'reset_estado':
            print("♻️  Reset de estado recibido en M4: limpiando vuelos del frontend")
            with self.lock:
                self.vuelos_activos = {}
            socketio.emit('vuelos_iniciales', [], namespace='/')

    def emitir_actualizaciones_periodicas(self):
        while self.running:
            try:
                with self.lock:
                    vuelos = list(self.vuelos_activos.values())
                for vuelo in vuelos:
                    ahora = time.time()
                    ultima = self.ultima_actualizacion.get(vuelo['id'], 0)
                    if ahora - ultima > self.DT * 2:
                        if vuelo.get('activo'):
                            velocidad_real = vuelo.get('velocidad', 800)
                            distancia_tick = velocidad_real * (self.DT / 3600.0) * self.FACTOR_TIEMPO
                            total = max(vuelo.get('distancia_total', 1), 1)
                            incremento = distancia_tick / total
                            vuelo['progreso'] = min(1.0, vuelo.get('progreso', 0.0) + incremento)
                            if vuelo['progreso'] >= 1.0:
                                vuelo['progreso'] = 1.0
                                vuelo['activo'] = False
                                vuelo['lat_actual'] = vuelo['destino']['lat']
                                vuelo['lon_actual'] = vuelo['destino']['lon']
                                vuelo['fin'] = datetime.now().isoformat()
                            else:
                                lat, lon = self.slerp(
                                    vuelo['origen']['lat'], vuelo['origen']['lon'],
                                    vuelo['destino']['lat'], vuelo['destino']['lon'],
                                    vuelo['progreso']
                                )
                                vuelo['lat_actual'] = lat
                                vuelo['lon_actual'] = lon
                                vuelo['trayectoria'] = (vuelo.get('trayectoria') or []) + [[lat, lon]]
                    socketio.emit('actualizar_vuelo', vuelo, namespace='/')
                time.sleep(self.DT)
            except Exception:
                time.sleep(self.DT)

    def haversine(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return 6371.0 * c

    def slerp(self, lat1, lon1, lat2, lon2, t):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        x1 = math.cos(lat1) * math.cos(lon1)
        y1 = math.cos(lat1) * math.sin(lon1)
        z1 = math.sin(lat1)
        x2 = math.cos(lat2) * math.cos(lon2)
        y2 = math.cos(lat2) * math.sin(lon2)
        z2 = math.sin(lat2)
        dot = x1*x2 + y1*y2 + z1*z2
        omega = math.acos(max(-1, min(1, dot)))
        if omega < 0.001:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            z = z1 + t * (z2 - z1)
        else:
            sin_omega = math.sin(omega)
            a = math.sin((1-t) * omega) / sin_omega
            b = math.sin(t * omega) / sin_omega
            x = a * x1 + b * x2
            y = a * y1 + b * y2
            z = a * z1 + b * z2
        lat = math.atan2(z, math.sqrt(x*x + y*y))
        lon = math.atan2(y, x)
        return math.degrees(lat), math.degrees(lon)

    def loop_local(self):
        while self.running and self.simulador_offline:
            with self.lock:
                vuelos = list(self.vuelos_activos.values())
            for vuelo in vuelos:
                if vuelo.get('activo'):
                    velocidad_real = vuelo.get('velocidad', 800)
                    distancia_tick = velocidad_real * (self.DT / 3600.0) * self.FACTOR_TIEMPO
                    total = max(vuelo.get('distancia_total', 1), 1)
                    incremento = distancia_tick / total
                    vuelo['progreso'] = min(1.0, vuelo.get('progreso', 0.0) + incremento)
                    if vuelo['progreso'] >= 1.0:
                        vuelo['progreso'] = 1.0
                        vuelo['activo'] = False
                        vuelo['lat_actual'] = vuelo['destino']['lat']
                        vuelo['lon_actual'] = vuelo['destino']['lon']
                        vuelo['fin'] = datetime.now().isoformat()
                    else:
                        lat, lon = self.slerp(
                            vuelo['origen']['lat'], vuelo['origen']['lon'],
                            vuelo['destino']['lat'], vuelo['destino']['lon'],
                            vuelo['progreso']
                        )
                        vuelo['lat_actual'] = lat
                        vuelo['lon_actual'] = lon
                        vuelo['trayectoria'] = (vuelo.get('trayectoria') or []) + [[lat, lon]]
                    socketio.emit('actualizar_vuelo', vuelo, namespace='/')
            time.sleep(self.DT)
    
    def solicitar_estadisticas_periodicas(self):
        """Solicita estadísticas periódicamente"""
        while self.running:
            time.sleep(10)  # Cada 10 segundos
            try:
                mensaje = {'tipo': 'solicitar_estadisticas'}
                self.socket_coord.send((json.dumps(mensaje) + '\n').encode('utf-8'))
            except:
                pass
    
    def iniciar(self):
        """Inicia el visualizador"""
        if not self.conectar():
            return
        
        # Thread para recibir actualizaciones
        threading.Thread(target=self.recibir_actualizaciones, daemon=True).start()
        
        # Thread para solicitar estadísticas periódicamente
        threading.Thread(target=self.solicitar_estadisticas_periodicas, daemon=True).start()

        # Thread para emitir actualizaciones periódicas a clientes web
        threading.Thread(target=self.emitir_actualizaciones_periodicas, daemon=True).start()

# Instancia global
visualizador = VisualizadorMapa()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return 'ok'

@socketio.on('connect')
def handle_connect():
    """Cliente web conectado"""
    print(f"🌐 Cliente web conectado")
    # Enviar vuelos actuales
    with visualizador.lock:
        vuelos = list(visualizador.vuelos_activos.values())
    emit('vuelos_iniciales', vuelos)

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente web desconectado"""
    print(f"🌐 Cliente web desconectado")

@socketio.on('solicitar_vuelos')
def handle_solicitar_vuelos():
    """Envía todos los vuelos actuales"""
    with visualizador.lock:
        vuelos = list(visualizador.vuelos_activos.values())
    emit('vuelos_iniciales', vuelos)

@socketio.on('comando_atc')
def handle_comando_atc(data):
    """Recibe comandos ATC del cliente web"""
    print(f"🎮 Comando ATC recibido: {data}")
    # Enviar al coordinador
    mensaje = {
        'tipo': 'comando_atc',
        'vuelo_id': data.get('vuelo_id'),
        'accion': data.get('accion'),
        'valor': data.get('valor')
    }
    try:
        visualizador.socket_coord.send((json.dumps(mensaje) + '\n').encode('utf-8'))
    except Exception as e:
        print(f"❌ Error enviando comando ATC: {e}")

    

@socketio.on('crear_vuelo_manual')
def handle_crear_vuelo_manual(data):
    try:
        mensaje = {
            'tipo': 'crear_vuelo_manual',
            'id': data.get('id'),
            'origen': data.get('origen'),
            'destino': data.get('destino'),
            'velocidad': data.get('velocidad')
        }
        visualizador.socket_coord.send((json.dumps(mensaje) + '\n').encode('utf-8'))
        emit('crear_vuelo_ack', {'ok': True})
    except Exception as e:
        print(f"❌ Error enviando creación de vuelo: {e}")
        emit('crear_vuelo_ack', {'ok': False, 'error': str(e)})

@socketio.on('pedir_estadisticas')
def handle_pedir_estadisticas():
    """Solicita estadísticas a la base de datos"""
    print("📊 Solicitando estadísticas...")
    mensaje = {'tipo': 'solicitar_estadisticas'}
    try:
        visualizador.socket_coord.send((json.dumps(mensaje) + '\n').encode('utf-8'))
    except Exception as e:
        print(f"❌ Error solicitando estadísticas: {e}")

if __name__ == "__main__":
    # Iniciar visualizador en thread separado
    threading.Thread(target=visualizador.iniciar, daemon=True).start()
    
    # Esperar un poco para conectar
    time.sleep(2)
    
    # Iniciar Flask
    print("🚀 Iniciando servidor web...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
