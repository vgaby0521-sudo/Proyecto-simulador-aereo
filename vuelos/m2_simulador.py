"""
M2 - SIMULADOR DE VUELOS
Genera vuelos con cálculos de Haversine, Bearing, Slerp y ETA
"""
import socket
import json
import time
import math
import random
import threading
from datetime import datetime, timedelta
import os

class SimuladorVuelos:
    def __init__(self, coordinador_host='localhost', coordinador_port=5555):
        hosts_env = os.getenv('COORDINADOR_HOSTS')
        host_env = os.getenv('COORDINADOR_HOST')
        port_env = os.getenv('COORDINADOR_PORT')
        self.coordinador_port = int(port_env) if port_env else coordinador_port
        self.hosts = [h.strip() for h in hosts_env.split(',')] if hosts_env else [host_env.strip() if host_env else coordinador_host]
        self.coordinador_host = self.hosts[0]
        self.socket = None
        self.vuelos_activos = {}
        self.max_vuelos = 50  # Mínimo 50 vuelos al iniciar
        self.pausado = False
        self.running = True
        self.lock = threading.Lock()
        
        # Radio de la Tierra en km
        self.RADIO_TIERRA = 6371.0
        
        self.FACTOR_TIEMPO = 60  # 1 real second = 60 simulated seconds
        self.DT = 0.2  # Tick duration in seconds (200ms)
        
        # Variables de entorno para simulación avanzada
        self.clima_global = {
            'viento_velocidad': 0,  # km/h
            'viento_direccion': 0,  # grados
            'tormenta_activa': False
        }
        
        self.aeropuertos = {
            # América del Norte
            'JFK': (40.6413, -73.7781, 'Nueva York JFK'),
            'LAX': (33.9416, -118.4085, 'Los Ángeles'),
            'MIA': (25.7959, -80.2870, 'Miami'),
            'ORD': (41.9742, -87.9073, 'Chicago O\'Hare'),
            'ATL': (33.6407, -84.4277, 'Atlanta'),
            'DFW': (32.8998, -97.0403, 'Dallas Fort Worth'),
            'SFO': (37.6213, -122.3790, 'San Francisco'),
            'SEA': (47.4502, -122.3088, 'Seattle'),
            'BOS': (42.3656, -71.0096, 'Boston'),
            'DEN': (39.8561, -104.6737, 'Denver'),
            'LAS': (36.0840, -115.1537, 'Las Vegas'),
            'YYZ': (43.6777, -79.6248, 'Toronto'),
            'YVR': (49.1967, -123.1815, 'Vancouver'),
            'MEX': (19.4363, -99.0721, 'Ciudad de México'),
            'CUN': (21.0365, -86.8771, 'Cancún'),
            
            # América del Sur
            'BOG': (4.7016, -74.1469, 'Bogotá'),
            'MDE': (6.1645, -75.4233, 'Medellín'),
            'CLO': (3.5432, -76.3816, 'Cali'),
            'CTG': (10.4424, -75.5130, 'Cartagena'),
            'BAQ': (10.8896, -74.7806, 'Barranquilla'),
            'LIM': (-12.0219, -77.1143, 'Lima'),
            'GRU': (-23.4356, -46.4731, 'São Paulo'),
            'GIG': (-22.8099, -43.2505, 'Rio de Janeiro'),
            'EZE': (-34.8222, -58.5358, 'Buenos Aires'),
            'SCL': (-33.3930, -70.7858, 'Santiago'),
            'UIO': (-0.1417, -78.4881, 'Quito'),
            
            # Europa
            'LHR': (51.4700, -0.4543, 'Londres Heathrow'),
            'CDG': (49.0097, 2.5479, 'París Charles de Gaulle'),
            'FRA': (50.0379, 8.5622, 'Frankfurt'),
            'AMS': (52.3105, 4.7683, 'Ámsterdam'),
            'MAD': (40.4983, -3.5676, 'Madrid'),
            'BCN': (41.2974, 2.0833, 'Barcelona'),
            'FCO': (41.8003, 12.2389, 'Roma Fiumicino'),
            'MXP': (45.6306, 8.7281, 'Milán Malpensa'),
            'MUC': (48.3537, 11.7750, 'Múnich'),
            'ZRH': (47.4582, 8.5556, 'Zúrich'),
            'VIE': (48.1103, 16.5697, 'Viena'),
            'LIS': (38.7742, -9.1342, 'Lisboa'),
            'CPH': (55.6181, 12.6508, 'Copenhague'),
            'OSL': (60.1939, 11.1004, 'Oslo'),
            'STO': (59.6519, 17.9186, 'Estocolmo'),
            'HEL': (60.3172, 24.9633, 'Helsinki'),
            'ATH': (37.9364, 23.9475, 'Atenas'),
            'IST': (41.2753, 28.7519, 'Estambul'),
            'SVO': (55.9726, 37.4146, 'Moscú Sheremetyevo'),
            
            # Asia
            'DXB': (25.2532, 55.3657, 'Dubái'),
            'DOH': (25.2731, 51.6080, 'Doha'),
            'BOM': (19.0896, 72.8656, 'Mumbai'),
            'DEL': (28.5562, 77.1000, 'Nueva Delhi'),
            'BLR': (13.1986, 77.7066, 'Bangalore'),
            'BKK': (13.6900, 100.7501, 'Bangkok'),
            'SIN': (1.3644, 103.9915, 'Singapur'),
            'KUL': (2.7456, 101.7072, 'Kuala Lumpur'),
            'CGK': (-6.1275, 106.6537, 'Yakarta'),
            'MNL': (14.5086, 121.0194, 'Manila'),
            'HKG': (22.3080, 113.9185, 'Hong Kong'),
            'PEK': (40.0799, 116.6031, 'Beijing'),
            'PVG': (31.1443, 121.8083, 'Shanghái Pudong'),
            'CAN': (23.3924, 113.2988, 'Guangzhou'),
            'ICN': (37.4602, 126.4407, 'Seúl Incheon'),
            'NRT': (35.7720, 140.3929, 'Tokio Narita'),
            'HND': (35.5494, 139.7798, 'Tokio Haneda'),
            'KIX': (34.4347, 135.2440, 'Osaka'),
            'TPE': (25.0797, 121.2342, 'Taipei'),
            
            # Oceanía
            'SYD': (-33.9399, 151.1753, 'Sídney'),
            'MEL': (-37.6690, 144.8410, 'Melbourne'),
            'BNE': (-27.3942, 153.1218, 'Brisbane'),
            'PER': (-31.9385, 115.9672, 'Perth'),
            'AKL': (-37.0082, 174.7850, 'Auckland'),
            'CHC': (-43.4894, 172.5320, 'Christchurch'),
            
            # África
            'JNB': (-26.1392, 28.2460, 'Johannesburgo'),
            'CPT': (-33.9715, 18.6021, 'Ciudad del Cabo'),
            'CAI': (30.1219, 31.4056, 'El Cairo'),
            'LOS': (6.5774, 3.3212, 'Lagos'),
            'NBO': (-1.3192, 36.9278, 'Nairobi'),
            'ADD': (8.9806, 38.7994, 'Addis Abeba'),
            'CMN': (33.3676, -7.5900, 'Casablanca'),
            'ALG': (36.6910, 3.2154, 'Argel'),
            
            # Medio Oriente
            'TLV': (32.0114, 34.8867, 'Tel Aviv'),
            'AMM': (31.7226, 35.9932, 'Ammán'),
            'RUH': (24.9577, 46.6988, 'Riad'),
            'JED': (21.6796, 39.1564, 'Jeddah'),
            'KWI': (29.2267, 47.9689, 'Kuwait'),
            'BAH': (26.2708, 50.6336, 'Baréin'),
        }
        
    def conectar(self):
        while self.running:
            for host in self.hosts:
                try:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.connect((host, self.coordinador_port))
                    info = {
                        'nombre': 'm2_simulador',
                        'tipo': 'simulador',
                        'version': '1.0'
                    }
                    self.socket.send(json.dumps(info).encode('utf-8'))
                    respuesta_raw = self.socket.recv(1024).decode('utf-8')
                    respuesta_linea = respuesta_raw.split('\n', 1)[0].strip()
                    confirmacion = json.loads(respuesta_linea)
                    if confirmacion['status'] == 'OK':
                        self.coordinador_host = host
                        print(f"✈️  [M2-SIMULADOR] Conectado al coordinador en {host}:{self.coordinador_port}")
                        return True
                except Exception as e:
                    print(f"❌ Error conectando a {host}:{self.coordinador_port}: {e}")
            print("   Reintentando en 5 segundos...")
            time.sleep(5)
        return False
    
    def haversine(self, lat1, lon1, lat2, lon2):
        """
        Calcula la distancia entre dos puntos usando la fórmula de Haversine
        d = 2R * arctan2(√a, √(1-a))
        donde a = sin²(Δφ/2) + cos(φ₁) * cos(φ₂) * sin²(Δλ/2)
        """
        # Convertir a radianes
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Diferencias
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Fórmula de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distancia = self.RADIO_TIERRA * c
        return distancia
    
    def calcular_bearing(self, lat1, lon1, lat2, lon2):
        """
        Calcula el rumbo inicial entre dos puntos
        θ = arctan2(sin(Δλ)cos(φ₂), cos(φ₁)sin(φ₂) - sin(φ₁)cos(φ₂)cos(Δλ))
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def slerp(self, lat1, lon1, lat2, lon2, t):
        """
        Interpolación esférica (Slerp) para calcular posición intermedia
        P(t) = sin((1-t)Ω)/sinΩ * P₀ + sin(tΩ)/sinΩ * P₁
        """
        # Convertir a radianes
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Convertir a coordenadas cartesianas
        x1 = math.cos(lat1) * math.cos(lon1)
        y1 = math.cos(lat1) * math.sin(lon1)
        z1 = math.sin(lat1)
        
        x2 = math.cos(lat2) * math.cos(lon2)
        y2 = math.cos(lat2) * math.sin(lon2)
        z2 = math.sin(lat2)
        
        # Producto punto para calcular ángulo omega
        dot = x1*x2 + y1*y2 + z1*z2
        omega = math.acos(max(-1, min(1, dot)))
        
        if omega < 0.001:  # Puntos muy cercanos
            # Interpolación lineal
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            z = z1 + t * (z2 - z1)
        else:
            # Slerp
            sin_omega = math.sin(omega)
            a = math.sin((1-t) * omega) / sin_omega
            b = math.sin(t * omega) / sin_omega
            
            x = a * x1 + b * x2
            y = a * y1 + b * y2
            z = a * z1 + b * z2
        
        # Convertir de vuelta a lat/lon
        lat = math.atan2(z, math.sqrt(x*x + y*y))
        lon = math.atan2(y, x)
        
        return math.degrees(lat), math.degrees(lon)
    
    def calcular_eta(self, distancia_restante, velocidad):
        """
        Calcula el tiempo estimado de llegada
        ETA = distancia_restante / velocidad
        """
        if velocidad == 0:
            return None
        
        horas = distancia_restante / velocidad
        eta = datetime.now() + timedelta(hours=horas)
        return eta
    
    def generar_vuelo(self):
        """Genera un nuevo vuelo con datos realistas"""
        # Seleccionar origen y destino aleatorios
        aeropuertos = list(self.aeropuertos.keys())
        origen_code = random.choice(aeropuertos)
        destino_code = random.choice([a for a in aeropuertos if a != origen_code])
        
        origen = self.aeropuertos[origen_code]
        destino = self.aeropuertos[destino_code]
        
        # Calcular distancia y rumbo
        distancia_total = self.haversine(origen[0], origen[1], destino[0], destino[1])
        rumbo = self.calcular_bearing(origen[0], origen[1], destino[0], destino[1])
        
        # Velocidad aleatoria entre 700-900 km/h
        velocidad = random.randint(700, 900)
        
        # Crear ID único
        vuelo_id = f"FL{random.randint(1000, 9999)}"
        
        combustible = distancia_total * 1.2  # 20% reserva
        
        # Calcular hora de salida y hora estimada de llegada
        hora_salida = datetime.now()
        tiempo_vuelo_horas = distancia_total / velocidad
        hora_llegada_estimada = hora_salida + timedelta(hours=tiempo_vuelo_horas)
        
        # Seleccionar imagen de avión aleatoria (URLs de aviones reales)
        aviones_imagenes = [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Boeing_737-800_%28American_Airlines%29.jpg/320px-Boeing_737-800_%28American_Airlines%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Airbus_A320-211_Airbus_Industries_F-WWBA_%28cn_001%29_%281988%29.jpg/320px-Airbus_A320-211_Airbus_Industries_F-WWBA_%28cn_001%29_%281988%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Boeing_777-300ER_%28Emirates%29.jpg/320px-Boeing_777-300ER_%28Emirates%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Airbus_A350-900_%28Qatar_Airways%29.jpg/320px-Airbus_A350-900_%28Qatar_Airways%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Boeing_787-9_Dreamliner_%28ANA%29.jpg/320px-Boeing_787-9_Dreamliner_%28ANA%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Airbus_A380-800_%28Emirates%29.jpg/320px-Airbus_A380-800_%28Emirates%29.jpg'
        ]
        imagen_avion = random.choice(aviones_imagenes)
        
        vuelo = {
            'id': vuelo_id,
            'origen': {'code': origen_code, 'nombre': origen[2], 'lat': origen[0], 'lon': origen[1]},
            'destino': {'code': destino_code, 'nombre': destino[2], 'lat': destino[0], 'lon': destino[1]},
            'distancia_total': round(distancia_total, 2),
            'rumbo': round(rumbo, 2),
            'velocidad': velocidad,
            'velocidad_base': velocidad,  # Para recordar la original
            'altitud': random.randint(30000, 40000),  # Pies
            'progreso': 0.0,  # 0 a 1
            'lat_actual': origen[0],
            'lon_actual': origen[1],
            'activo': True,
            'emergencia': False,
            'combustible': round(combustible, 2),
            'hora_salida': hora_salida.isoformat(),  # Hora de salida
            'hora_llegada_estimada': hora_llegada_estimada.isoformat(),  # Hora estimada de llegada
            'inicio': hora_salida.isoformat(),  # Mantener compatibilidad
            'imagen_avion': imagen_avion,  # Imagen de avión real
            'trayectoria': [[origen[0], origen[1]]]  # Inicializar con posición de origen
        }
        
        return vuelo
    
    def generar_vuelo_desde(self, vuelo_id, origen_code, destino_code, velocidad):
        if origen_code not in self.aeropuertos or destino_code not in self.aeropuertos:
            return None
        origen = self.aeropuertos[origen_code]
        destino = self.aeropuertos[destino_code]
        distancia_total = self.haversine(origen[0], origen[1], destino[0], destino[1])
        rumbo = self.calcular_bearing(origen[0], origen[1], destino[0], destino[1])
        combustible = distancia_total * 1.2
        hora_salida = datetime.now()
        tiempo_vuelo_horas = distancia_total / max(velocidad, 1)
        hora_llegada_estimada = hora_salida + timedelta(hours=tiempo_vuelo_horas)
        aviones_imagenes = [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Boeing_737-800_%28American_Airlines%29.jpg/320px-Boeing_737-800_%28American_Airlines%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Airbus_A320-211_Airbus_Industries_F-WWBA_%28cn_001%29_%281988%29.jpg/320px-Airbus_A320-211_Airbus_Industries_F-WWBA_%28cn_001%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Boeing_777-300ER_%28Emirates%29.jpg/320px-Boeing_777-300ER_%28Emirates%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Airbus_A350-900_%28Qatar_Airways%29.jpg/320px-Airbus_A350-900_%28Qatar_Airways%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Boeing_787-9_Dreamliner_%28ANA%29.jpg/320px-Boeing_787-9_Dreamliner_%28ANA%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Airbus_A380-800_%28Emirates%29.jpg/320px-Airbus_A380-800_%28Emirates%29.jpg'
        ]
        imagen_avion = random.choice(aviones_imagenes)
        vuelo = {
            'id': vuelo_id,
            'origen': {'code': origen_code, 'nombre': origen[2], 'lat': origen[0], 'lon': origen[1]},
            'destino': {'code': destino_code, 'nombre': destino[2], 'lat': destino[0], 'lon': destino[1]},
            'distancia_total': round(distancia_total, 2),
            'rumbo': round(rumbo, 2),
            'velocidad': int(velocidad),
            'velocidad_base': int(velocidad),
            'altitud': random.randint(30000, 40000),
            'progreso': 0.0,
            'lat_actual': origen[0],
            'lon_actual': origen[1],
            'activo': True,
            'emergencia': False,
            'combustible': round(combustible, 2),
            'hora_salida': hora_salida.isoformat(),
            'hora_llegada_estimada': hora_llegada_estimada.isoformat(),
            'inicio': hora_salida.isoformat(),
            'imagen_avion': imagen_avion,
            'trayectoria': [[origen[0], origen[1]]]
        }
        return vuelo
    
    def actualizar_vuelo(self, vuelo):
        """Actualiza la posición de un vuelo"""
        if not vuelo['activo']:
            return vuelo
        
        velocidad_real = vuelo['velocidad']
        
        # Efecto del viento (simplificado)
        if self.clima_global['viento_velocidad'] > 0:
            # Si el viento está a favor (+/- 45 grados del rumbo), aumenta velocidad
            diferencia_angulo = abs(vuelo['rumbo'] - self.clima_global['viento_direccion'])
            if diferencia_angulo < 45:
                velocidad_real += self.clima_global['viento_velocidad'] * 0.5
            elif diferencia_angulo > 135:
                velocidad_real -= self.clima_global['viento_velocidad'] * 0.5
        
        # Evento aleatorio: Emergencia (1% probabilidad)
        if not vuelo.get('emergencia') and random.random() < 0.001:
            vuelo['emergencia'] = True
            vuelo['velocidad'] = vuelo['velocidad'] * 0.8  # Reducir velocidad
            vuelo['altitud'] = vuelo['altitud'] - 10000    # Descender
            print(f"🚨 MAYDAY: Vuelo {vuelo['id']} declara emergencia!")

        # Consumo de combustible
        consumo = velocidad_real * (self.DT / 3600.0) * self.FACTOR_TIEMPO  # Litros por tick (simulado)
        vuelo['combustible'] -= consumo
        
        if vuelo['combustible'] <= 0 and vuelo['activo']:
            print(f"⛽ Vuelo {vuelo['id']} se quedó sin combustible!")
            vuelo['emergencia'] = True
            
        # Distance to cover in this tick (km)
        distancia_tick = velocidad_real * (self.DT / 3600.0) * self.FACTOR_TIEMPO
        
        # Calculate progress increment based on total distance
        if vuelo['distancia_total'] > 0:
            incremento = distancia_tick / vuelo['distancia_total']
        else:
            incremento = 1.0  # Should not happen for valid flights
            
        vuelo['progreso'] += incremento
        
        if vuelo['progreso'] >= 1.0:
            # Vuelo completado
            vuelo['progreso'] = 1.0
            vuelo['activo'] = False
            vuelo['lat_actual'] = vuelo['destino']['lat']
            vuelo['lon_actual'] = vuelo['destino']['lon']
            hora_llegada_real = datetime.now()
            vuelo['fin'] = hora_llegada_real.isoformat()
            vuelo['hora_llegada'] = hora_llegada_real.isoformat()  # Hora real de llegada
            
            # Agregar punto final a la trayectoria
            vuelo['trayectoria'].append([vuelo['destino']['lat'], vuelo['destino']['lon']])
            
            print(f"🛬 Vuelo {vuelo['id']} ha llegado a {vuelo['destino']['nombre']}")
            
            # Enviar mensaje de llegada
            self.enviar_mensaje({
                'tipo': 'vuelo_completado',
                'vuelo': vuelo
            })
        else:
            lat, lon = self.slerp(
                vuelo['origen']['lat'], vuelo['origen']['lon'],
                vuelo['destino']['lat'], vuelo['destino']['lon'],
                vuelo['progreso']
            )
            
            vuelo['lat_actual'] = lat
            vuelo['lon_actual'] = lon
            
            # Calcular distancia restante y ETA
            distancia_restante = self.haversine(
                lat, lon,
                vuelo['destino']['lat'], vuelo['destino']['lon']
            )
            eta = self.calcular_eta(distancia_restante, velocidad_real)
            
            vuelo['distancia_restante'] = round(distancia_restante, 2)
            vuelo['eta'] = eta.isoformat() if eta else None
            vuelo['hora_llegada_estimada'] = eta.isoformat() if eta else vuelo.get('hora_llegada_estimada')
            
            # Actualizar trayectoria (limitar a últimos 1000 puntos para rendimiento)
            vuelo['trayectoria'].append([lat, lon])
            if len(vuelo['trayectoria']) > 1000:
                vuelo['trayectoria'] = vuelo['trayectoria'][-1000:]
            
            if random.random() < 0.05:  # Solo 5% de actualizaciones muestran log
                print(f"📍 {vuelo['id']}: {vuelo['progreso']:.1%} - {vuelo['origen']['code']}→{vuelo['destino']['code']}")
        
        return vuelo
    
    def enviar_mensaje(self, mensaje):
        """Envía mensaje al coordinador"""
        try:
            data = json.dumps(mensaje).encode('utf-8')
            self.socket.send(data + b'\n')
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            try:
                if self.running:
                    print("🔄 Reconectando al coordinador...")
                    if self.conectar():
                        data = json.dumps(mensaje).encode('utf-8')
                        self.socket.send(data + b'\n')
            except Exception as e2:
                print(f"❌ Error reintentando envío: {e2}")
    
    def loop_simulacion(self):
        """Loop principal de simulación"""
        print("🚀 Iniciando simulación de vuelos...")
        print(f"   Configuración: Máximo {self.max_vuelos} vuelos simultáneos")
        print(f"   Aeropuertos disponibles: {len(self.aeropuertos)} en todo el mundo")
        print(f"   Rango permitido: 50 - 50,000 vuelos")
        
        # Generar vuelos iniciales hasta llegar al mínimo de 50
        with self.lock:
            vuelos_iniciales = max(0, 50 - len(self.vuelos_activos))
            if vuelos_iniciales > 0:
                print(f"📦 Generando {vuelos_iniciales} vuelos iniciales para alcanzar el mínimo de 50...")
                for _ in range(vuelos_iniciales):
                    nuevo_vuelo = self.generar_vuelo()
                    self.vuelos_activos[nuevo_vuelo['id']] = nuevo_vuelo
                    
                    # Enviar vuelo nuevo al mapa
                    self.enviar_mensaje({
                        'tipo': 'vuelo_nuevo',
                        'vuelo': nuevo_vuelo
                    })
                    
                    # Guardar vuelo en base de datos cuando despega
                    pass
                
                print(f"✅ {len(self.vuelos_activos)} vuelos activos iniciales generados")
        
        while self.running:
            if self.pausado:
                time.sleep(1)
                continue
            
            self.actualizar_clima()
            
            with self.lock:
                if len(self.vuelos_activos) < self.max_vuelos:
                    vuelos_a_generar = min(10, self.max_vuelos - len(self.vuelos_activos))
                    
                    for _ in range(vuelos_a_generar):
                        nuevo_vuelo = self.generar_vuelo()
                        self.vuelos_activos[nuevo_vuelo['id']] = nuevo_vuelo
                        
                        if len(self.vuelos_activos) % 50 == 0 or len(self.vuelos_activos) <= 10:
                            print(f"✈️  Nuevo vuelo {nuevo_vuelo['id']}: "
                                  f"{nuevo_vuelo['origen']['code']} → {nuevo_vuelo['destino']['code']} "
                                  f"({nuevo_vuelo['distancia_total']:.0f} km) | Total activos: {len(self.vuelos_activos)}")
                        
                        # Enviar vuelo nuevo al mapa
                        self.enviar_mensaje({
                            'tipo': 'vuelo_nuevo',
                            'vuelo': nuevo_vuelo
                        })
                        
                        # Guardar vuelo en base de datos cuando despega
                        pass
                
                # Actualizar todos los vuelos activos
                vuelos_a_eliminar = []
                num_activos = len(self.vuelos_activos)
                
                for vuelo_id, vuelo in list(self.vuelos_activos.items()):
                    if vuelo['activo']:
                        vuelo = self.actualizar_vuelo(vuelo)
                        
                        # Enviar actualización con trayectoria completa
                        self.enviar_mensaje({
                            'tipo': 'vuelo_update',
                            'vuelo': vuelo,
                            'vuelos_activos': num_activos
                        })
                    else:
                        vuelos_a_eliminar.append(vuelo_id)
                        
                        self.enviar_mensaje({
                            'tipo': 'vuelo_completado',
                            'vuelo': vuelo
                        })
                
                # Eliminar vuelos completados
                for vuelo_id in vuelos_a_eliminar:
                    del self.vuelos_activos[vuelo_id]
            
            time.sleep(self.DT)
    
    def recibir_comandos(self):
        """Recibe comandos del coordinador"""
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    raise ConnectionError("Socket cerrado")
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    linea, buffer = buffer.split('\n', 1)
                    if not linea.strip():
                        continue
                    mensaje = json.loads(linea)
                    tipo = mensaje.get('tipo')
                    if tipo == 'comando':
                        accion = mensaje.get('accion')
                        if accion == 'pausar':
                            self.pausado = True
                            print("⏸️  Simulación PAUSADA")
                        elif accion == 'reanudar':
                            self.pausado = False
                            print("▶️  Simulación REANUDADA")
                        elif accion == 'resync':
                            with self.lock:
                                for v in list(self.vuelos_activos.values()):
                                    self.enviar_mensaje({'tipo': 'vuelo_nuevo', 'vuelo': v})
                    elif tipo == 'comando_atc':
                        vuelo_id = mensaje.get('vuelo_id')
                        accion = mensaje.get('accion')
                        valor = mensaje.get('valor')
                        with self.lock:
                            if vuelo_id in self.vuelos_activos:
                                vuelo = self.vuelos_activos[vuelo_id]
                                if accion == 'cambiar_altitud':
                                    vuelo['altitud'] = int(valor)
                                    print(f"👨‍✈️ ATC: Vuelo {vuelo_id} cambiando altitud a {valor} pies")
                                elif accion == 'cambiar_velocidad':
                                    vuelo['velocidad'] = int(valor)
                                    print(f"👨‍✈️ ATC: Vuelo {vuelo_id} cambiando velocidad a {valor} km/h")
                                elif accion == 'emergencia':
                                    vuelo['emergencia'] = True
                                    print(f"🚨 ATC: Vuelo {vuelo_id} declarado en EMERGENCIA")
                    elif tipo == 'configuracion':
                        if 'max_vuelos' in mensaje:
                            nuevo_max = mensaje['max_vuelos']
                            if 50 <= nuevo_max <= 50000:
                                self.max_vuelos = nuevo_max
                                print(f"⚙️  Máximo de vuelos actualizado: {self.max_vuelos}")
                                print(f"   Vuelos activos actualmente: {len(self.vuelos_activos)}")
                            else:
                                print(f"⚠️  El máximo debe estar entre 50 y 50,000 (recibido: {nuevo_max})")
                    elif tipo == 'reset_estado':
                        print("♻️  Reset de estado recibido: limpiando y generando vuelos aleatorios")
                        with self.lock:
                            self.vuelos_activos = {}
                            objetivo = max(50, min(self.max_vuelos, 50000))
                            vuelos_iniciales = random.randint(50, objetivo)
                            print(f"   Generando {vuelos_iniciales} vuelos iniciales (rango 50–{objetivo})")
                            for _ in range(vuelos_iniciales):
                                nuevo_vuelo = self.generar_vuelo()
                                self.vuelos_activos[nuevo_vuelo['id']] = nuevo_vuelo
                                self.enviar_mensaje({'tipo': 'vuelo_nuevo', 'vuelo': nuevo_vuelo})
                    elif tipo == 'crear_vuelo_manual':
                        vuelo_id = (mensaje.get('id') or f"FL{random.randint(1000,9999)}").upper()
                        origen_code = (mensaje.get('origen') or '').upper()
                        destino_code = (mensaje.get('destino') or '').upper()
                        velocidad = int(mensaje.get('velocidad') or random.randint(700, 900))
                        nuevo_vuelo = self.generar_vuelo_desde(vuelo_id, origen_code, destino_code, velocidad)
                        if nuevo_vuelo:
                            with self.lock:
                                self.vuelos_activos[nuevo_vuelo['id']] = nuevo_vuelo
                            self.enviar_mensaje({'tipo': 'vuelo_nuevo', 'vuelo': nuevo_vuelo})
                            print(f"✈️  Vuelo manual {nuevo_vuelo['id']} creado: {origen_code} → {destino_code}")
                        else:
                            print("⚠️  Códigos IATA inválidos para creación manual")
            except Exception as e:
                print(f"❌ Error recibiendo comandos: {e}")
                time.sleep(5)
                if self.running and self.conectar():
                    continue
    
    def iniciar(self):
        """Inicia el simulador"""
        if not self.conectar():
            return
        
        # Thread para recibir comandos
        threading.Thread(target=self.recibir_comandos, daemon=True).start()
        
        # Thread para simulación
        threading.Thread(target=self.loop_simulacion, daemon=True).start()
        
        # Mantener vivo
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Cerrando simulador...")
            self.running = False

    def actualizar_clima(self):
        """Simula cambios en el clima global"""
        if random.random() < 0.01:  # 1% probabilidad de cambio
            self.clima_global['viento_velocidad'] = random.randint(0, 100)
            self.clima_global['viento_direccion'] = random.randint(0, 360)
            self.clima_global['tormenta_activa'] = random.random() < 0.1  # 10% prob de tormenta
            
            print(f"🌤️  Cambio de clima: Viento {self.clima_global['viento_velocidad']} km/h, Tormenta: {self.clima_global['tormenta_activa']}")

if __name__ == "__main__":
    simulador = SimuladorVuelos()
    simulador.iniciar()

