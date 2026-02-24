"""
M3 - BASE DE DATOS
Almacena todos los vuelos completados en formato JSONL
"""
import socket
import json
import os
import time
from datetime import datetime
import threading

class BaseDatos:
    def __init__(self, coordinador_host='localhost', coordinador_port=5555):
        host_env = os.getenv('COORDINADOR_HOST')
        port_env = os.getenv('COORDINADOR_PORT')
        self.coordinador_host = host_env.strip() if host_env else coordinador_host
        self.coordinador_port = int(port_env) if port_env else coordinador_port
        self.socket = None
        base_dir = '/data' if os.path.exists('/.dockerenv') else os.path.join(os.getcwd(), 'data')
        self.archivo_datos = os.path.join(base_dir, 'vuelos_guardados.jsonl')
        self.running = True
        self.lock = threading.Lock()
        self.vuelos_guardados = 0
        
        os.makedirs(os.path.dirname(self.archivo_datos), exist_ok=True)
        
        if not os.path.exists(self.archivo_datos):
            with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                pass
            print(f"📄 Archivo de base de datos creado: {self.archivo_datos}")
        else:
            try:
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    self.vuelos_guardados = sum(1 for line in f if line.strip())
                print(f"📊 Vuelos ya registrados: {self.vuelos_guardados}")
            except:
                pass
        
    def conectar(self):
        """Conecta con el coordinador"""
        while self.running:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.coordinador_host, self.coordinador_port))
                
                # Enviar identificación
                info = {
                    'nombre': 'm3_base_datos',
                    'tipo': 'base_datos',
                    'version': '1.0'
                }
                self.socket.send(json.dumps(info).encode('utf-8'))
                
                # Esperar confirmación
                respuesta = self.socket.recv(1024).decode('utf-8')
                confirmacion = json.loads(respuesta)
                
                if confirmacion['status'] == 'OK':
                    print(f"💾 [M3-BASE_DATOS] Conectado al coordinador")
                    print(f"   Archivo: {self.archivo_datos}")
                    return True
                    
            except Exception as e:
                print(f"❌ Error conectando al coordinador: {e}")
                print("   Reintentando en 5 segundos...")
                time.sleep(5)  # Tolerancia a fallos: reintento cada 5 segundos
        
        return False
    
    def guardar_vuelo(self, vuelo):
        """Guarda un vuelo en el archivo JSONL"""
        try:
            with self.lock:
                # Agregar timestamp de guardado
                registro = {
                    **vuelo,
                    'guardado_en': datetime.now().isoformat(),
                    'timestamp_unix': time.time()
                }
                
                # Escribir en formato JSONL (una línea JSON por registro)
                with open(self.archivo_datos, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(registro, ensure_ascii=False) + '\n')
                    f.flush()  # Forzar escritura inmediata
                    os.fsync(f.fileno())  # Sincronizar con disco
                
                self.vuelos_guardados += 1
                
            print(f"💾 ✅ Vuelo {vuelo['id']} guardado exitosamente (Total: {self.vuelos_guardados})")
            print(f"   {vuelo['origen']['code']} → {vuelo['destino']['code']} | {vuelo['distancia_total']:.0f} km")
            print(f"   Archivo: {self.archivo_datos}")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando vuelo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def actualizar_hora_llegada(self, vuelo_id, hora_llegada):
        """Actualiza solo la hora de llegada de un vuelo existente"""
        try:
            if not os.path.exists(self.archivo_datos):
                print(f"⚠️  No se puede actualizar: archivo no existe")
                return False
            
            # Leer todas las líneas
            lineas = []
            actualizado = False
            
            with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                for linea in f:
                    if linea.strip():
                        try:
                            vuelo = json.loads(linea)
                            if vuelo.get('id') == vuelo_id:
                                vuelo['hora_llegada'] = hora_llegada
                                vuelo['actualizado_en'] = datetime.now().isoformat()
                                actualizado = True
                            lineas.append(json.dumps(vuelo, ensure_ascii=False))
                        except:
                            lineas.append(linea.strip())
            
            # Reescribir archivo con la actualización
            if actualizado:
                with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                    for linea in lineas:
                        f.write(linea + '\n')
                    f.flush()
                    os.fsync(f.fileno())
                print(f"✅ Hora de llegada actualizada para vuelo {vuelo_id}")
                return True
            else:
                print(f"⚠️  Vuelo {vuelo_id} no encontrado para actualizar")
                return False
                
        except Exception as e:
            print(f"❌ Error actualizando hora de llegada: {e}")
            return False
    
    def obtener_estadisticas(self):
        """Calcula estadísticas de vuelos guardados"""
        try:
            if not os.path.exists(self.archivo_datos):
                return {
                    'total_vuelos': 0,
                    'distancia_total': 0,
                    'promedio_velocidad': 0
                }
            
            total_vuelos = 0
            distancia_total = 0
            velocidad_total = 0
            rutas = {}
            
            with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                for linea in f:
                    if linea.strip():
                        try:
                            vuelo = json.loads(linea)
                            total_vuelos += 1
                            distancia_total += vuelo.get('distancia_total', 0)
                            velocidad_total += vuelo.get('velocidad', 0)
                            
                            # Contar rutas
                            ruta = f"{vuelo['origen']['code']}-{vuelo['destino']['code']}"
                            rutas[ruta] = rutas.get(ruta, 0) + 1
                        except:
                            pass
            
            return {
                'total_vuelos': total_vuelos,
                'distancia_total': round(distancia_total, 2),
                'promedio_velocidad': round(velocidad_total / total_vuelos if total_vuelos > 0 else 0, 2),
                'rutas_populares': sorted(rutas.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
        except Exception as e:
            print(f"❌ Error calculando estadísticas: {e}")
            return None

    def compactar_archivo(self):
        try:
            if not os.path.exists(self.archivo_datos):
                return
            registros = {}
            with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                for linea in f:
                    if linea.strip():
                        try:
                            v = json.loads(linea)
                            vid = v.get('id')
                            ts = v.get('timestamp_unix') or 0
                            if vid:
                                if vid not in registros or ts >= (registros[vid].get('timestamp_unix') or 0):
                                    registros[vid] = v
                        except:
                            pass
            with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                for v in registros.values():
                    f.write(json.dumps(v, ensure_ascii=False) + '\n')
                f.flush()
                os.fsync(f.fileno())
            self.vuelos_guardados = len(registros)
            print(f"🧹 Compactación realizada: {self.vuelos_guardados} vuelos únicos")
        except Exception as e:
            print(f"❌ Error en compactación: {e}")
    
    def recibir_mensajes(self):
        """Recibe mensajes del coordinador"""
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(8192)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    linea, buffer = buffer.split('\n', 1)
                    if linea.strip():
                        try:
                            mensaje = json.loads(linea)
                            tipo = mensaje.get('tipo')
                            
                            if tipo == 'guardar_vuelo':
                                # Registrar vuelo cuando aparece (con todos los atributos)
                                vuelo = mensaje.get('vuelo')
                                if vuelo:
                                    print(f"📥 Registrando nuevo vuelo {vuelo.get('id')} en BD")
                                    resultado = self.guardar_vuelo(vuelo)
                                    if resultado:
                                        print(f"   ✅ Vuelo registrado exitosamente en BD")
                            elif tipo == 'vuelo_update':
                                # Guardar cada actualización para tener historial en JSONL
                                vuelo = mensaje.get('vuelo')
                                if vuelo:
                                    self.guardar_vuelo(vuelo)
                            
                            elif tipo == 'vuelo_completado':
                                # Solo actualizar hora de llegada del vuelo existente
                                vuelo = mensaje.get('vuelo')
                                if vuelo:
                                    vuelo_id = vuelo.get('id')
                                    hora_llegada = vuelo.get('hora_llegada') or vuelo.get('fin')
                                    print(f"📥 Actualizando hora de llegada para vuelo {vuelo_id}")
                                    # Actualizar solo la hora de llegada en el archivo
                                    self.actualizar_hora_llegada(vuelo_id, hora_llegada)
                            
                            elif tipo == 'obtener_estadisticas':
                                stats = self.obtener_estadisticas()
                                if stats:
                                    respuesta = {
                                        'tipo': 'estadisticas',
                                        'datos': stats
                                    }
                                    # Enviar respuesta al coordinador para que la reenvíe al solicitante
                                    self.socket.send((json.dumps(respuesta) + '\n').encode('utf-8'))
                            elif tipo == 'reset_estado':
                                print("♻️  Reset de estado recibido en M3: reiniciando base de datos")
                                self.resetear_base()
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Error JSON: {e}")
                        
            except Exception as e:
                print(f"❌ Error recibiendo mensajes: {e}")
                break
        
        print("🔄 Intentando reconectar...")
        time.sleep(5)  # Tolerancia a fallos: esperar antes de reconectar
        if self.running:
            try:
                self.conectar()
                self.recibir_mensajes()
            except Exception as e:
                print(f"❌ Error en reconexión: {e}")
                # Reintentar después de otro intervalo
                if self.running:
                    threading.Thread(target=self.recibir_mensajes, daemon=True).start()

    def mostrar_estadisticas_periodicas(self):
        """Muestra estadísticas cada cierto tiempo"""
        while self.running:
            time.sleep(30)
            stats = self.obtener_estadisticas()
            if stats:
                print(f"\n📊 ESTADÍSTICAS DE VUELOS")
                print(f"   Total vuelos guardados: {stats['total_vuelos']}")
                print(f"   Distancia acumulada: {stats['distancia_total']:,.0f} km")
                print(f"   Velocidad promedio: {stats['promedio_velocidad']} km/h")
                if stats['rutas_populares']:
                    print(f"   Rutas más frecuentes:")
                    for ruta, count in stats['rutas_populares']:
                        print(f"     • {ruta}: {count} vuelos")
                print("="*60)
    
    def iniciar(self):
        """Inicia la base de datos"""
        if not self.conectar():
            return
        self.resetear_base()
        
        # Thread para estadísticas periódicas
        threading.Thread(target=self.mostrar_estadisticas_periodicas, daemon=True).start()
        
        # Loop principal
        try:
            self.recibir_mensajes()
        except KeyboardInterrupt:
            print("\n👋 Cerrando base de datos...")
            self.running = False
            self.resetear_base()

    def resetear_base(self):
        try:
            with self.lock:
                with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                    f.write('')
                    f.flush()
                    os.fsync(f.fileno())
                self.vuelos_guardados = 0
            print("🗑️ BD reiniciada: 0 vuelos")
        except Exception as e:
            print(f"❌ Error reiniciando BD: {e}")

if __name__ == "__main__":
    bd = BaseDatos()
    bd.iniciar()
