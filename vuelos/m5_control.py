"""
M5 - PANEL DE CONTROL
Permite pausar, reanudar y configurar la simulación
"""
import socket
import json
import time
import threading
import os
import random

class PanelControl:
    def __init__(self, coordinador_host='localhost', coordinador_port=5555):
        host_env = os.getenv('COORDINADOR_HOST')
        port_env = os.getenv('COORDINADOR_PORT')
        self.coordinador_host = host_env.strip() if host_env else coordinador_host
        self.coordinador_port = int(port_env) if port_env else coordinador_port
        self.socket = None
        self.running = True
        
    def conectar(self):
        """Conecta con el coordinador"""
        while self.running:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.coordinador_host, self.coordinador_port))
                
                # Enviar identificación
                info = {
                    'nombre': 'm5_control',
                    'tipo': 'panel_control',
                    'version': '1.0'
                }
                self.socket.send(json.dumps(info).encode('utf-8'))
                
                # Esperar confirmación
                respuesta = self.socket.recv(1024).decode('utf-8')
                confirmacion = json.loads(respuesta)
                
                if confirmacion['status'] == 'OK':
                    print(f"🎮 [M5-CONTROL] Conectado al coordinador")
                    return True
                    
            except Exception as e:
                print(f"❌ Error conectando al coordinador: {e}")
                print("   Reintentando en 5 segundos...")
                time.sleep(5)  # Tolerancia a fallos: reintento cada 5 segundos
        
        return False
    
    def enviar_comando(self, comando, **kwargs):
        """Envía un comando al coordinador"""
        try:
            mensaje = {
                'tipo': 'comando',
                'comando': comando,
                **kwargs
            }
            self.socket.send(json.dumps(mensaje).encode('utf-8'))
            print(f"✅ Comando '{comando}' enviado")
            return True
        except Exception as e:
            print(f"❌ Error enviando comando: {e}")
            return False
    
    def mostrar_menu(self):
        """Muestra el menú de comandos"""
        print("\n" + "="*60)
        print("🎮 PANEL DE CONTROL - SIMULADOR DE TRÁFICO AÉREO")
        print("="*60)
        print("Comandos disponibles:")
        print("  pausa        - Pausar la simulación")
        print("  reanudar     - Reanudar la simulación")
        print("  max <n>      - Máximo de vuelos simultáneos (50-50,000)")
        print("  atc <id> alt <n>  - Cambiar altitud de vuelo (pies)")
        print("  atc <id> vel <n>  - Cambiar velocidad de vuelo (km/h)")
        print("  atc <id> mayday   - Declarar emergencia en vuelo")
        print("  salir        - Cerrar el panel de control")
        print("="*60)
    
    def loop_interactivo(self):
        """Loop interactivo para recibir comandos del usuario"""
        self.mostrar_menu()
        
        while self.running:
            try:
                comando_input = input("\n🎮 Comando: ").strip().lower()
                
                if not comando_input:
                    continue
                
                partes = comando_input.split()
                comando = partes[0]
                
                if comando == 'pausa':
                    self.enviar_comando('pausa')
                    print("⏸️  Simulación pausada")
                
                elif comando == 'reanudar':
                    self.enviar_comando('reanudar')
                    print("▶️  Simulación reanudada")
                
                elif comando == 'max':
                    if len(partes) < 2:
                        print("❌ Uso: max <número> | max random | max aleatorio")
                        print("   Ejemplo: max 1000")
                        print("   Rango permitido: 50 - 50,000 vuelos")
                        continue
                    arg = partes[1]
                    if arg in ['random', 'aleatorio']:
                        max_vuelos = random.randint(50, 50000)
                        self.enviar_comando('max_vuelos', valor=max_vuelos)
                        print(f"✅ Máximo de vuelos ALEATORIO establecido a {max_vuelos:,}")
                        print("   El simulador generará vuelos hasta alcanzar este nuevo límite")
                    else:
                        try:
                            max_vuelos = int(arg)
                            if max_vuelos < 50 or max_vuelos > 50000:
                                print("❌ El número debe estar entre 50 y 50,000")
                                print("   Ejemplos válidos:")
                                print("     • max 100    (100 vuelos)")
                                print("     • max 1000   (1,000 vuelos)")
                                print("     • max 10000  (10,000 vuelos)")
                                print("     • max 50000  (50,000 vuelos - máximo)")
                                continue
                            self.enviar_comando('max_vuelos', valor=max_vuelos)
                            print(f"✅ Máximo de vuelos establecido a {max_vuelos:,}")
                            print("   El simulador comenzará a generar vuelos hasta alcanzar este límite")
                        except ValueError:
                            print("❌ Número inválido")
                            print("   Debes ingresar un número entero entre 50 y 50,000")
                
                elif comando == 'atc':
                    if len(partes) < 3:
                        print("❌ Uso: atc <id_vuelo> <accion> [valor]")
                        continue
                    
                    vuelo_id = partes[1].upper()
                    accion = partes[2]
                    
                    if accion == 'alt' and len(partes) >= 4:
                        try:
                            altitud = int(partes[3])
                            self.enviar_comando('comando_atc', vuelo_id=vuelo_id, accion='cambiar_altitud', valor=altitud)
                        except:
                            print("❌ Altitud inválida")
                    
                    elif accion == 'vel' and len(partes) >= 4:
                        try:
                            velocidad = int(partes[3])
                            self.enviar_comando('comando_atc', vuelo_id=vuelo_id, accion='cambiar_velocidad', valor=velocidad)
                        except:
                            print("❌ Velocidad inválida")
                            
                    elif accion == 'mayday':
                        self.enviar_comando('comando_atc', vuelo_id=vuelo_id, accion='emergencia')
                    
                    else:
                        print("❌ Acción ATC no reconocida")

                elif comando == 'salir':
                    print("👋 Cerrando panel de control...")
                    self.running = False
                    break
                
                elif comando == 'ayuda' or comando == 'help':
                    self.mostrar_menu()
                
                else:
                    print(f"❌ Comando '{comando}' no reconocido. Escribe 'ayuda' para ver comandos.")
                    
            except KeyboardInterrupt:
                print("\n👋 Cerrando panel de control...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def iniciar(self):
        """Inicia el panel de control"""
        if not self.conectar():
            return
        
        print("\n✅ Panel de control listo")
        print("   Escribe 'ayuda' para ver los comandos disponibles")
        print(f"   Rango de vuelos: 50 - 50,000 simultáneos")
        
        try:
            self.loop_interactivo()
        except KeyboardInterrupt:
            print("\n👋 Cerrando panel de control...")
            self.running = False

if __name__ == "__main__":
    panel = PanelControl()
    panel.iniciar()
