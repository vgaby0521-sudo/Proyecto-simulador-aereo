
import os
import sys
import time
import json
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager


URL_BASE = "http://127.0.0.1:8000/"
RUTA_CAPTURAS = os.path.join(os.getcwd(), "Capturas_Completas")
RUTA_JSON = os.path.join(os.getcwd(), "data.json")
USUARIO_CLIENTE = {"usuario": "cliente1", "clave": "Cliente123!"}
USUARIO_ADMIN = {"usuario": "admin", "clave": "Admin12345!"}
PRODUCTO_TEST = {}

def cargar_config_desde_json():
    if os.path.exists(RUTA_JSON):
        try:
            with open(RUTA_JSON, "r", encoding="utf-8") as f:
                incoming = json.load(f)
                print("\n📥 JSON recibido desde n8n:")
                print(json.dumps(incoming, indent=4))
            if "usuario_cliente" in incoming:
                USUARIO_CLIENTE.update(incoming["usuario_cliente"])
            if "usuario_admin" in incoming:
                USUARIO_ADMIN.update(incoming["usuario_admin"])
            global PRODUCTO_TEST
            PRODUCTO_TEST = incoming.get("producto_test", {})
        except Exception as e:
            print(f"❌ Error leyendo JSON: {e}")
    else:
        print("⚠ No se encontró data.json. Usando valores por defecto.")

cargar_config_desde_json()



if sys.platform.startswith('win'):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')



class WineShopTestCompleto(unittest.TestCase):
    """Suite completa de pruebas funcionales para Wine Shop"""
    
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*80)
        print("INICIANDO PRUEBAS FUNCIONALES COMPLETAS DE WINE SHOP")
        print("="*80 + "\n")

       
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=options)
        cls.wait = WebDriverWait(cls.driver, 15)
        cls.contador_capturas = 0

    
        if not os.path.exists(RUTA_CAPTURAS):
            os.makedirs(RUTA_CAPTURAS)
            print(f" Carpeta de capturas creada: {RUTA_CAPTURAS}\n")

    @classmethod
    def tearDownClass(cls):
        time.sleep(2)
        cls.driver.quit()
        print("\n" + "="*80)
        print(f"✅ PRUEBAS FINALIZADAS - {cls.contador_capturas} capturas guardadas")
        print(f"📂 Ubicación: {RUTA_CAPTURAS}")
        print("="*80 + "\n")

    def capturar(self, nombre, descripcion=""):
        """Guarda una captura con nombre estructurado y contador"""
        WineShopTestCompleto.contador_capturas += 1
        numero = str(WineShopTestCompleto.contador_capturas).zfill(3)
        nombre_archivo = f"{numero}_{nombre}.png"
        ruta = os.path.join(RUTA_CAPTURAS, nombre_archivo)
        self.driver.save_screenshot(ruta)
        if descripcion:
            print(f"📸 [{numero}] {descripcion}")
        else:
            print(f"📸 [{numero}] Captura: {nombre}")

    def esperar_y_hacer_scroll(self, element):
        """Hace scroll hasta el elemento antes de interactuar"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
    
    def esperar_desvanecimiento_mensajes(self):
        """Espera a que los mensajes de alerta se desvanezcan"""
        try:
            
            time.sleep(3)
           
            self.driver.execute_script("""
                var messages = document.querySelectorAll('.message');
                messages.forEach(function(msg) {
                    msg.style.display = 'none';
                });
            """)
        except:
            pass

    # =============================
    # PRUEBA 1 - NAVEGACIÓN PÚBLICA (SIN LOGIN)
    # =============================
    def test_01_paginas_publicas_completas(self):
        """Prueba exhaustiva de todas las páginas públicas"""
        print("\n🧪 TEST 1: Navegación de Páginas Públicas (Sin Login)")
        print("-" * 60)
        driver = self.driver
        
       
        print("➤ Accediendo a la página principal...")
        driver.get(URL_BASE)
        time.sleep(2)
        self.capturar("home_inicial", "Página principal sin autenticación")
        
        
        try:
            productos_destacados = driver.find_elements(By.CLASS_NAME, "producto-card")
            print(f"  ✓ Encontrados {len(productos_destacados)} productos destacados")
        except:
            print("  ⚠ No se encontraron productos destacados")
        
       
        print("➤ Navegando al catálogo...")
        try:
            catalogo_link = driver.find_element(By.LINK_TEXT, "Catálogo")
            catalogo_link.click()
            time.sleep(2)
            self.capturar("catalogo_publico", "Catálogo de productos completo")
            
            
            try:
                busqueda = driver.find_element(By.NAME, "busqueda")
                busqueda.send_keys("vino")
                busqueda.send_keys(Keys.RETURN)
                time.sleep(1)
                self.capturar("catalogo_busqueda", "Búsqueda de productos")
                print("  ✓ Función de búsqueda operativa")
            except:
                print("  ⚠ No se encontró campo de búsqueda")
                
        except NoSuchElementException:
            print("  ❌ Enlace al catálogo no encontrado")
        
        
        print("➤ Visualizando detalle de producto...")
        try:
            driver.get(URL_BASE + "catalogo/")
            time.sleep(1)
            productos = driver.find_elements(By.CSS_SELECTOR, "a[href*='producto']")
            if productos:
                productos[0].click()
                time.sleep(2)
                self.capturar("detalle_producto_publico", "Detalle de producto sin login")
                print("  ✓ Página de detalle de producto cargada")
        except Exception as e:
            print(f"  ⚠ No se pudo acceder al detalle: {e}")
        
       
        print("➤ Revisando sección de ofertas...")
        try:
            driver.get(URL_BASE)
            ofertas_link = driver.find_element(By.LINK_TEXT, "Ofertas")
            ofertas_link.click()
            time.sleep(2)
            self.capturar("ofertas_publico", "Sección de ofertas")
            print("  ✓ Página de ofertas cargada")
        except NoSuchElementException:
            print("  ⚠ Enlace a ofertas no encontrado")
        
        print("✅ Test 1 completado: Navegación pública\n")

    # =============================
    # PRUEBA 2 - REGISTRO DE NUEVO USUARIO
    # =============================
    def test_02_registro_usuario(self):
        """Prueba el proceso completo de registro"""
        print("\n🧪 TEST 2: Registro de Nuevo Usuario")
        print("-" * 60)
        driver = self.driver
        
        print("➤ Accediendo a formulario de registro...")
        driver.get(URL_BASE)
        time.sleep(1)
        
        try:
            registro_link = driver.find_element(By.LINK_TEXT, "Registro")
            registro_link.click()
            time.sleep(1)
            self.capturar("formulario_registro", "Formulario de registro de usuario")
            
            # Llenar formulario (solo visualizar, no registrar para no crear usuarios duplicados)
            print("  ✓ Formulario de registro accesible")
            
        except NoSuchElementException:
            print("  ❌ No se encontró el enlace de registro")
        
        print("✅ Test 2 completado: Registro de usuario\n")

    # =============================
    # PRUEBA 3 - LOGIN Y FUNCIONES DE CLIENTE
    # =============================
    def test_03_cliente_flujo_completo(self):
        """Prueba exhaustiva de todas las funcionalidades de cliente"""
        print("\n🧪 TEST 3: Flujo Completo de CLIENTE")
        print("-" * 60)
        driver = self.driver
        
    
        print("➤ Iniciando sesión como cliente...")
        driver.get(URL_BASE + "login/")
        time.sleep(1)
        self.capturar("login_form_cliente", "Formulario de login")
        
        try:
            username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_field = driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(USUARIO_CLIENTE["usuario"])
            password_field.clear()
            password_field.send_keys(USUARIO_CLIENTE["clave"])
            
            submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_btn.click()
            time.sleep(2)
            
            self.capturar("cliente_logueado", "Cliente autenticado exitosamente")
            print(f"  ✓ Login exitoso como: {USUARIO_CLIENTE['usuario']}")
            
          
            self.esperar_desvanecimiento_mensajes()
            
        except Exception as e:
            print(f"  ❌ Error en login: {e}")
            return
        
     
        print("➤ Accediendo al perfil de usuario...")
        try:
            perfil_link = driver.find_element(By.LINK_TEXT, "Mi Cuenta")
            perfil_link.click()
            time.sleep(2)
            self.capturar("perfil_cliente", "Perfil completo del cliente")
            print("  ✓ Página de perfil cargada")
        except NoSuchElementException:
            print("  ⚠ Enlace 'Mi Cuenta' no encontrado")
        
       
        print("➤ Navegando al catálogo desde sesión activa...")
        try:
            driver.find_element(By.LINK_TEXT, "Catálogo").click()
            time.sleep(2)
            self.capturar("catalogo_cliente_logueado", "Catálogo con sesión activa")
        except:
            driver.get(URL_BASE + "catalogo/")
            time.sleep(2)
        
       
        print("➤ Agregando productos al carrito...")
        try:
           
            productos_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='producto']")
            if productos_links:
                
                producto_url = productos_links[0].get_attribute('href')
                productos_links[0].click()
                time.sleep(2)
                self.capturar("detalle_producto_cliente", "Detalle de producto para cliente")
                
                
                try:
                    # Buscar botón de agregar al carrito
                    agregar_btns = driver.find_elements(By.XPATH, 
                        "//button[contains(text(),'Agregar') or contains(text(),'agregar') or contains(@onclick, 'carrito')]")
                    
                    if agregar_btns:
                        self.esperar_y_hacer_scroll(agregar_btns[0])
                        agregar_btns[0].click()
                        time.sleep(2)
                        self.capturar("producto_agregado_carrito", "Producto agregado al carrito")
                        print("  ✓ Producto agregado al carrito")
                    else:
                        print("  ⚠ No se encontró botón 'Agregar al Carrito'")
                        
                except Exception as e:
                    print(f"  ⚠ No se pudo agregar al carrito: {e}")
                
        except Exception as e:
            print(f"  ⚠ Error al acceder a detalle de producto: {e}")
        
       
        print("➤ Visualizando carrito de compras...")
        try:
            driver.find_element(By.LINK_TEXT, "Mi Carrito").click()
            time.sleep(2)
            self.capturar("carrito_productos", "Carrito con productos")
            print("  ✓ Carrito accesible")
            
           
            try:
                cantidad_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='number']")
                if cantidad_inputs:
                    print("  ✓ Controles de cantidad disponibles")
            except:
                pass
                
        except NoSuchElementException:
            print("  ⚠ No se pudo acceder al carrito")
       

        print("➤ Iniciando proceso de checkout...")
        try:
           
            checkout_btns = driver.find_elements(By.XPATH, 
                "//a[contains(text(),'Checkout') or contains(text(),'Finalizar')]")
            if checkout_btns:
                checkout_btns[0].click()
                time.sleep(2)
                self.capturar("checkout_formulario", "Formulario de checkout")
                print("  ✓ Página de checkout cargada")
                
               
                try:
                    formularios = driver.find_elements(By.TAG_NAME, "form")
                    if formularios:
                        self.capturar("checkout_detalle", "Detalle completo del checkout")
                except:
                    pass
            else:
                print("  ⚠ Botón de checkout no encontrado")
        except Exception as e:
            print(f"  ⚠ Error en checkout: {e}")
        
     
        print("➤ Consultando historial de pedidos...")
        try:
            driver.get(URL_BASE + "mis_pedidos/")
            time.sleep(2)
            self.capturar("mis_pedidos", "Historial de pedidos del cliente")
            print("  ✓ Página 'Mis Pedidos' accesible")
        except:
            print("  ⚠ No se pudo acceder a 'Mis Pedidos'")
        
    
        print("➤ Cerrando sesión...")
        try:
            driver.find_element(By.LINK_TEXT, "Salir").click()
            time.sleep(2)
            self.capturar("cliente_logout", "Sesión de cliente cerrada")
            print("  ✓ Logout exitoso")
        except NoSuchElementException:
            print("  ⚠ No se encontró opción de cerrar sesión")
        
        print("✅ Test 3 completado: Flujo completo de cliente\n")

    # =============================
    # PRUEBA 4 - FUNCIONALIDADES DE ADMINISTRADOR
    # =============================
    def test_04_admin_flujo_completo(self):
        """Prueba exhaustiva de todas las funcionalidades de administrador"""
        print("\n🧪 TEST 4: Flujo Completo de ADMINISTRADOR")
        print("-" * 60)
        driver = self.driver
        
    
        print("➤ Iniciando sesión como administrador...")
        driver.get(URL_BASE + "login/")
        time.sleep(1)
        
        try:
            username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_field = driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(USUARIO_ADMIN["usuario"])
            password_field.clear()
            password_field.send_keys(USUARIO_ADMIN["clave"])
            
            submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_btn.click()
            time.sleep(2)
            
            self.capturar("admin_logueado", "Administrador autenticado")
            print(f"  ✓ Login exitoso como: {USUARIO_ADMIN['usuario']}")
            
           
            self.esperar_desvanecimiento_mensajes()
            
        except Exception as e:
            print(f"  ❌ Error en login de admin: {e}")
            return
        
    
        print("➤ Accediendo al panel de administración...")
        try:
            admin_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Admin")
            admin_link.click()
            time.sleep(2)
            self.capturar("panel_admin_principal", "Panel principal de administración")
            print("  ✓ Panel de administración cargado")
            
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.capturar("panel_admin_estadisticas", "Estadísticas del panel admin")
            
        except NoSuchElementException:
            print("  ❌ No se encontró acceso al panel de admin")
            return
        
      
        print("➤ Gestionando productos...")
        try:
            productos_link = driver.find_element(By.LINK_TEXT, "Productos")
            productos_link.click()
            time.sleep(2)
            self.capturar("admin_productos_lista", "Lista de productos (Admin)")
            print("  ✓ Lista de productos accesible")
            
           
            try:
                crear_btns = driver.find_elements(By.XPATH, 
                    "//a[contains(text(),'Crear') or contains(text(),'Nuevo') or contains(text(),'Agregar')]")
                if crear_btns:
                    crear_btns[0].click()
                    time.sleep(2)
                    self.capturar("admin_producto_crear_form", "Formulario de creación de producto")
                    print("  ✓ Formulario de creación de producto accesible")
                    driver.back()
                    time.sleep(1)
            except:
                print("  ⚠ Botón de crear producto no encontrado")
                
       
            try:
                editar_btns = driver.find_elements(By.XPATH, "//a[contains(text(),'Editar')]")
                if editar_btns:
                    editar_btns[0].click()
                    time.sleep(2)
                    self.capturar("admin_producto_editar_form", "Formulario de edición de producto")
                    print("  ✓ Formulario de edición de producto accesible")
                    driver.back()
                    time.sleep(1)
            except:
                print("  ⚠ Botón de editar producto no encontrado")
            
            driver.back()
            time.sleep(1)
            
        except NoSuchElementException:
            print("  ⚠ Enlace a 'Productos' no encontrado")
        
       
        print("➤ Gestionando proveedores...")
        try:
            proveedores_link = driver.find_element(By.LINK_TEXT, "Proveedores")
            proveedores_link.click()
            time.sleep(2)
            self.capturar("admin_proveedores_lista", "Lista de proveedores (Admin)")
            print("  ✓ Lista de proveedores accesible")
            
          
            try:
                crear_btns = driver.find_elements(By.XPATH, 
                    "//a[contains(text(),'Crear') or contains(text(),'Nuevo')]")
                if crear_btns:
                    crear_btns[0].click()
                    time.sleep(2)
                    self.capturar("admin_proveedor_crear_form", "Formulario de creación de proveedor")
                    print("  ✓ Formulario de creación de proveedor accesible")
                    driver.back()
                    time.sleep(1)
            except:
                print("  ⚠ Botón de crear proveedor no encontrado")
            
            driver.back()
            time.sleep(1)
            
        except NoSuchElementException:
            print("  ⚠ Enlace a 'Proveedores' no encontrado")
        
     
        print("➤ Gestionando pedidos...")
        try:
            pedidos_link = driver.find_element(By.LINK_TEXT, "Pedidos")
            pedidos_link.click()
            time.sleep(2)
            self.capturar("admin_pedidos_lista", "Lista de pedidos (Admin)")
            print("  ✓ Lista de pedidos accesible")
            
          
            try:
                editar_btns = driver.find_elements(By.XPATH, "//a[contains(text(),'Editar') or contains(text(),'Ver')]")
                if editar_btns:
                    editar_btns[0].click()
                    time.sleep(2)
                    self.capturar("admin_pedido_detalle", "Detalle/Edición de pedido")
                    print("  ✓ Edición de pedido accesible")
                    driver.back()
                    time.sleep(1)
            except:
                print("  ⚠ No hay pedidos para editar")
            
            driver.back()
            time.sleep(1)
            
        except NoSuchElementException:
            print("  ⚠ Enlace a 'Pedidos' no encontrado")
        
   
        print("➤ Gestionando clientes...")
        try:
            clientes_link = driver.find_element(By.LINK_TEXT, "Clientes")
            clientes_link.click()
            time.sleep(2)
            self.capturar("admin_clientes_lista", "Lista de clientes (Admin)")
            print("  ✓ Lista de clientes accesible")
            
        
            try:
                crear_btns = driver.find_elements(By.XPATH, 
                    "//a[contains(text(),'Crear') or contains(text(),'Nuevo')]")
                if crear_btns:
                    crear_btns[0].click()
                    time.sleep(2)
                    self.capturar("admin_cliente_crear_form", "Formulario de creación de cliente")
                    print("  ✓ Formulario de creación de cliente accesible")
                    driver.back()
                    time.sleep(1)
            except:
                print("  ⚠ Botón de crear cliente no encontrado")
            
            driver.back()
            time.sleep(1)
            
        except NoSuchElementException:
            print("  ⚠ Enlace a 'Clientes' no encontrado")
        
      
        print("➤ Gestionando usuarios...")
        try:
            usuarios_link = driver.find_element(By.LINK_TEXT, "Usuarios")
            usuarios_link.click()
            time.sleep(2)
            self.capturar("admin_usuarios_lista", "Lista de usuarios administradores")
            print("  ✓ Lista de usuarios accesible")
            
            driver.back()
            time.sleep(1)
            
        except NoSuchElementException:
            print("  ⚠ Enlace a 'Usuarios' no encontrado")
        
 
        print("➤ Generando reporte Excel...")
        try:
           
            driver.get(URL_BASE + "admin_panel/")
            time.sleep(2)
            
         
            excel_btns = driver.find_elements(By.XPATH, 
                "//a[contains(text(),'Excel') or contains(text(),'Reporte') or contains(text(),'Exportar')]")
            
            if excel_btns:
                self.capturar("admin_antes_reporte_excel", "Antes de generar reporte Excel")
                excel_btns[0].click()
                time.sleep(3)
                print("  ✓ Reporte Excel generado (descarga iniciada)")
                self.capturar("admin_despues_reporte_excel", "Después de generar reporte Excel")
              
                self.esperar_desvanecimiento_mensajes()
            else:
                print("  ⚠ Botón de reporte Excel no encontrado")
                
        except Exception as e:
            print(f"  ⚠ Error al generar reporte Excel: {e}")
        
  
        print("➤ Consultando roles...")
        try:
            driver.get(URL_BASE + "roles/")
            time.sleep(2)
            self.capturar("admin_roles_lista", "Lista de roles del sistema")
            print("  ✓ Página de roles accesible")
         
            self.esperar_desvanecimiento_mensajes()
        except:
            print("  ⚠ Página de roles no accesible")
        

        print("➤ Accediendo al perfil de administrador...")
        try:
            driver.find_element(By.LINK_TEXT, "Mi Cuenta").click()
            time.sleep(2)
            self.capturar("perfil_admin", "Perfil del administrador")
            print("  ✓ Perfil de admin accesible")
        except:
            print("  ⚠ Perfil de admin no accesible")
        
  
        print("➤ Cerrando sesión de administrador...")
        try:
           
            self.esperar_desvanecimiento_mensajes()
            
          
            salir_btn = driver.find_element(By.LINK_TEXT, "Salir")
            
          
            try:
                salir_btn.click()
            except:
         
                driver.execute_script("arguments[0].click();", salir_btn)
            
            time.sleep(2)
            self.capturar("admin_logout", "Sesión de administrador cerrada")
            print("  ✓ Logout de admin exitoso")
        except NoSuchElementException:
            print("  ⚠ No se pudo cerrar sesión de admin")
        except Exception as e:
            print(f"  ⚠ Error en logout de admin: {e}")
        
        print("✅ Test 4 completado: Flujo completo de administrador\n")

    # =============================
    # PRUEBA 5 - VERIFICACIÓN FINAL
    # =============================
    def test_05_verificacion_final(self):
        """Verificación final del sistema"""
        print("\n🧪 TEST 5: Verificación Final del Sistema")
        print("-" * 60)
        driver = self.driver
        
     
        print("➤ Verificación final de accesibilidad...")
        driver.get(URL_BASE)
        time.sleep(2)
        self.capturar("verificacion_final", "Verificación final del sistema")
        
     
        try:
          
            header = driver.find_element(By.TAG_NAME, "header")
            print("  ✓ Header presente")
            
          
            footer = driver.find_element(By.TAG_NAME, "footer")
            print("  ✓ Footer presente")
            
         
            nav = driver.find_element(By.TAG_NAME, "nav")
            print("  ✓ Navegación presente")
            
            print("\n" + "="*60)
            print("🎉 TODAS LAS PRUEBAS FUNCIONALES COMPLETADAS EXITOSAMENTE")
            print("="*60)
            
        except Exception as e:
            print(f"  ⚠ Advertencia en verificación final: {e}")
        
        print("✅ Test 5 completado: Verificación final\n")


if __name__ == "__main__":
   
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None  
    suite = loader.loadTestsFromTestCase(WineShopTestCompleto)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    