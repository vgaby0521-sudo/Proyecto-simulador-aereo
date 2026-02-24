"""
M1 - COORDINADOR / SERVIDOR CENTRAL
Administra conexiones, enruta mensajes con Round Robin y failover
"""
import socket
import threading
import json
import time
from datetime import datetime

class Coordinador:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.clientes = {}
        self.clientes_activos = []
        self.lock = threading.Lock()
        self.round_robin_index = 0
        self.running = True
        
        self.mensajes_enviados = 0
        self.mensajes_recibidos = 0
        self.vuelos_activos = 0
        self.mensajes_por_segundo = 0
        self.ultimo_conteo = time.time()
        self.buffer_db = []

    def iniciar(self):
        """Inicia el servidor coordinador"""
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((self.host, self.port))
        servidor.listen(10)
        servidor.settimeout(1.0)  # Timeout para permitir verificación de running
        
        print(f"🛰️  [M1-COORDINADOR] Servidor iniciado en {self.host}:{self.port}")
        print("="*60)
        
        threading.Thread(target=self.monitor_estado, daemon=True).start()
        
        while self.running:
            try:
                cliente_socket, direccion = servidor.accept()
                print(f"✅ Nueva conexión desde {direccion}")
                threading.Thread(
                    target=self.manejar_cliente,
                    args=(cliente_socket, direccion),
                    daemon=True
                ).start()
            except socket.timeout:
                # Timeout esperado cuando no hay conexiones - no es un error
                continue
            except OSError as e:
                # Error del socket (puede ser que se cerró)
                if self.running:
                    print(f"⚠️  Error de socket: {e}")
                break
            except Exception as e:
                # Otros errores inesperados
                if self.running:
                    print(f"❌ Error aceptando conexión: {e}")
    
    def manejar_cliente(self, cliente_socket, direccion):
        """Maneja la comunicación con un cliente conectado"""
        nombre_cliente = None
        
        try:
            data = cliente_socket.recv(1024).decode('utf-8')
            info = json.loads(data)
            nombre_cliente = info.get('nombre', f'cliente_{direccion[1]}')
            tipo = info.get('tipo', 'desconocido')
            
            with self.lock:
                self.clientes[nombre_cliente] = {
                    'socket': cliente_socket,
                    'tipo': tipo,
                    'direccion': direccion,
                    'conectado_desde': datetime.now().isoformat()
                }
                self.clientes_activos.append(nombre_cliente)
            
            print(f"🔗 [{nombre_cliente}] registrado como '{tipo}'")
            
            respuesta = {
                'status': 'OK',
                'mensaje': f'Bienvenido {nombre_cliente}',
                'timestamp': time.time()
            }
            cliente_socket.send((json.dumps(respuesta) + '\n').encode('utf-8'))
            try:
                cliente_socket.send((json.dumps({'tipo': 'reset_estado'}) + '\n').encode('utf-8'))
            except:
                pass
            if tipo == 'simulador':
                try:
                    self.broadcast({'tipo': 'simulador_online'})
                except:
                    pass
            if tipo == 'visualizador':
                try:
                    self.enviar_a_modulo('m2_simulador', {'tipo': 'comando', 'accion': 'resync'})
                except:
                    pass
            
            buffer = ""
            while self.running:
                data = cliente_socket.recv(8192)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                # Procesar todos los mensajes completos en el buffer
                while '\n' in buffer:
                    linea, buffer = buffer.split('\n', 1)
                    if linea.strip():
                        try:
                            mensaje = json.loads(linea)
                            self.mensajes_recibidos += 1
                            self.procesar_mensaje(nombre_cliente, mensaje)
                        except json.JSONDecodeError:
                            print(f"⚠️  JSON inválido de {nombre_cliente}: {linea[:100]}")
                    
        except Exception as e:
            print(f"❌ Error con {nombre_cliente}: {e}")
        finally:
            self.desconectar_cliente(nombre_cliente)
    
    def procesar_mensaje(self, origen, mensaje):
        """Procesa y enruta mensajes según el tipo"""
        tipo = mensaje.get('tipo')
        
        if tipo == 'vuelo_update':
            if 'vuelos_activos' in mensaje:
                self.vuelos_activos = mensaje['vuelos_activos']
            self.broadcast(mensaje, excluir=origen)
            
        elif tipo == 'vuelo_nuevo':
            self.broadcast(mensaje, excluir=origen)
            # También guardar en BD cuando despega
            self.enviar_a_modulo('m3_base_datos', {
                'tipo': 'guardar_vuelo',
                'vuelo': mensaje.get('vuelo')
            })
            
        elif tipo == 'comando':
            self.ejecutar_comando(mensaje)
            
        elif tipo == 'guardar_vuelo':
            self.enviar_a_modulo('m3_base_datos', mensaje)
            
        elif tipo == 'vuelo_completado':
            self.enviar_a_modulo('m3_base_datos', mensaje)
            self.broadcast(mensaje, excluir=origen)
            
        elif tipo == 'ping':
            self.enviar_a_modulo(origen, {'tipo': 'pong', 'timestamp': time.time()})
            
        elif tipo == 'comando_atc':
            # Reenviar comando ATC al simulador
            print(f"🎮 Comando ATC recibido para {mensaje.get('vuelo_id')}: {mensaje.get('accion')}")
            self.enviar_a_modulo('m2_simulador', mensaje)
        
        elif tipo == 'crear_vuelo_manual':
            self.enviar_a_modulo('m2_simulador', mensaje)
            
        elif tipo == 'solicitar_estadisticas':
            # Reenviar solicitud a base de datos
            self.enviar_a_modulo('m3_base_datos', {'tipo': 'obtener_estadisticas', 'origen': origen})
            
        elif tipo == 'estadisticas':
            # Reenviar respuesta de estadísticas al solicitante (mapa)
            self.enviar_a_modulo('m4_mapa', mensaje)
    
    def broadcast(self, mensaje, excluir=None):
        """Envía mensaje a todos los clientes activos"""
        with self.lock:
            clientes = list(self.clientes_activos)
        
        for nombre in clientes:
            if nombre != excluir:
                self.enviar_a_modulo(nombre, mensaje)
    
    def enviar_a_modulo(self, nombre_modulo, mensaje):
        """Envía mensaje a un módulo específico"""
        try:
            with self.lock:
                if nombre_modulo not in self.clientes:
                    return False
                
                cliente_socket = self.clientes[nombre_modulo]['socket']
            
            data = (json.dumps(mensaje) + '\n').encode('utf-8')
            cliente_socket.send(data)
            self.mensajes_enviados += 1
            return True
            
        except Exception as e:
            print(f"❌ Error enviando a {nombre_modulo}: {e}")
            self.desconectar_cliente(nombre_modulo)
            if nombre_modulo == 'm3_base_datos':
                try:
                    self.buffer_db.append(mensaje)
                    self.enviar_a_modulo('m4_mapa', {'tipo': 'guardar_vuelo_backup', 'payload': mensaje})
                except:
                    pass
            return False
    
    def ejecutar_comando(self, mensaje):
        """Ejecuta comandos del panel de control"""
        comando = mensaje.get('comando')
        print(f"🎮 Ejecutando comando: {comando}")
        
        if comando == 'pausa':
            self.broadcast({'tipo': 'comando', 'accion': 'pausar'})
        elif comando == 'reanudar':
            self.broadcast({'tipo': 'comando', 'accion': 'reanudar'})
        elif comando == 'max_vuelos':
            max_vuelos = mensaje.get('valor', 10)
            print(f"🔧 Configurando máximo de vuelos: {max_vuelos}")
            self.enviar_a_modulo('m2_simulador', {
                'tipo': 'configuracion',
                'max_vuelos': max_vuelos
            })
    
    def desconectar_cliente(self, nombre_cliente):
        """Desconecta y limpia recursos de un cliente"""
        if not nombre_cliente:
            return
            
        with self.lock:
            if nombre_cliente in self.clientes:
                try:
                    self.clientes[nombre_cliente]['socket'].close()
                except:
                    pass
                del self.clientes[nombre_cliente]
            
            if nombre_cliente in self.clientes_activos:
                self.clientes_activos.remove(nombre_cliente)
        
        print(f"🔌 [{nombre_cliente}] desconectado")
        if nombre_cliente == 'm2_simulador':
            try:
                self.broadcast({'tipo': 'simulador_offline'})
            except:
                pass
    
    def monitor_estado(self):
        """Monitorea y reporta el estado del sistema"""
        while self.running:
            time.sleep(30)
            
            ahora = time.time()
            tiempo_transcurrido = ahora - self.ultimo_conteo
            if tiempo_transcurrido > 0:
                self.mensajes_por_segundo = (self.mensajes_enviados + self.mensajes_recibidos) / tiempo_transcurrido
            
            with self.lock:
                print(f"\n📊 ESTADO DEL SISTEMA")
                print(f"   Clientes activos: {len(self.clientes_activos)}")
                print(f"   Vuelos activos: {self.vuelos_activos}")
                print(f"   Mensajes enviados: {self.mensajes_enviados}")
                print(f"   Mensajes recibidos: {self.mensajes_recibidos}")
                print(f"   Mensajes/segundo: {self.mensajes_por_segundo:.2f}")
                
                if self.clientes_activos:
                    print(f"   Módulos conectados:")
                    for nombre in self.clientes_activos:
                        tipo = self.clientes[nombre]['tipo']
                        print(f"     • {nombre} ({tipo})")
                print("="*60)
            
            try:
                if 'm3_base_datos' in self.clientes and self.buffer_db:
                    pendientes = list(self.buffer_db)
                    self.buffer_db = []
                    for msg in pendientes:
                        ok = self.enviar_a_modulo('m3_base_datos', msg)
                        if not ok:
                            self.buffer_db.append(msg)
                            break
            except:
                pass
            self.mensajes_enviados = 0
            self.mensajes_recibidos = 0
            self.ultimo_conteo = ahora

if __name__ == "__main__":
    coordinador = Coordinador()
    try:
        coordinador.iniciar()
    except KeyboardInterrupt:
        print("\n👋 Cerrando coordinador...")
        coordinador.running = False
