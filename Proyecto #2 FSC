#===========================================================================
# main.py - Raspberry Pi Pico W
# CElect - Máquina dispensadora
# CE-1104 Fundamentos en Sistemas Computacionales I Semestre 2026

# Mapa de pines:
#   GP26        → Potenciómetro (ADC0)
#   GP0 – GP6   → Segmentos a,b,c,d,e,f,g del display (cátodo común)
#   GP7         → Botón de compra (PULL_UP, activo en LOW)
#   GP8         → LED verde (hay stock)
#   GP9         → LED rojo  (sin stock)
#   GP10        → Señal PWM del servomotor
#===========================================================================
import machine     # GPIO, ADC, PWM - control de hardware de la Pico W
import utime       # Funciones de tiempo
import network     # Conexión WiFi de la Pico W
import usocket     # Comunicación TCP con la app en la PC
import ujson       # Serialización JSON ligera para MicroPython
#===========================================================================
# INVENTARIO INICIAL
inventario = [7, 3, 5] # máx 9
#===========================================================================
# POTENCIÓMETRO 
# selección de los productos
"""
from machine import Pin, ADC, PWM     #Importamos librerías   
import time                                

LED = PWM(Pin(15))     # Declaramos el pin 15 como PWM
LED.freq(1000)     # 1000Hz

POT = ADC(26)     #Declaramos la variable para la lectura analógica pin 26

while True: #Bucle infinito
    
  Valor = POT.read_u16()      # Almacenamos los valores leídos de nuestro potenciómetro en la variable "Valor"
                              #que serán de 0 a 65535
  
  porcentaje = round(Valor/65535*100) #Redondeamos los valores de 0 a 100
  
  print("Valor de 0 a 100:" ,porcentaje,"%") # Imprimimos los valores almacenados en la variable "porcentaje"
  
  
  LED.duty_u16(Valor)         # Establesemos el valor del ciclo de trabajo como el del valor del potenciómetro
  time.sleep(0.25)            # Le damos un diempo de 250msdef mover_servo(angulo):
  """

potenciometro = machine.ADC(26)
 
producto_actual = 0   # Último producto estable detectado (variable de estado)
 
def leer_producto():
    """
    Lee el potenciómetro y retorna el índice del producto seleccionado
    (0, 1 o 2). Usa histéresis para evitar cambios involuntarios en los
    bordes de cada franja.
    """
    global producto_actual
 
    valor = potenciometro.read_u16()   # Lectura ADC: 0 a 65535
 
    HISTERESIS = 400   # Margen de seguridad en cada borde (~0.6% del rango)
 
    # Bordes con histéresis aplicada
    #   Para SUBIR de franja (0→1, 1→2): el valor debe superar el borde + margen
    #   Para BAJAR de franja (1→0, 2→1): el valor debe caer por debajo del borde - margen
    BORDE_01 = 21845
    BORDE_12 = 43690
 
    if producto_actual == 0:
        if valor >= BORDE_01 + HISTERESIS:      # Supera 22245 → cambia a producto 1
            producto_actual = 1
 
    elif producto_actual == 1:
        if valor < BORDE_01 - HISTERESIS:       # Baja de 21445  → vuelve a producto 0
            producto_actual = 0
        elif valor >= BORDE_12 + HISTERESIS:    # Supera 44090  → cambia a producto 2
            producto_actual = 2
 
    else:   # producto_actual == 2
        if valor < BORDE_12 - HISTERESIS:       # Baja de 43290 → vuelve a producto 1
            producto_actual = 1
 
    return producto_actual
#=============================================================================
# 7 SEGMENTOS
# muestra las unidades disponibles de los productos

SEGMENTOS = [machine.Pin(i, machine.Pin.OUT) for i in range(7)]

DIGITOS = {
    0: [1,1,1,1,1,1,0],
    1: [0,1,1,0,0,0,0],
    2: [1,1,0,1,1,0,1],
    3: [1,1,1,1,0,0,1],
    4: [0,1,1,0,0,1,1],
    5: [1,0,1,1,0,1,1],
    6: [1,0,1,1,1,1,1],
    7: [1,1,1,0,0,0,0],
    8: [1,1,1,1,1,1,1],
    9: [1,1,1,1,0,1,1],
}

def mostrar_digito(n):
    patron = DIGITOS.get(n, [0,0,0,0,0,0,0])
    for i, seg in enumerate(SEGMENTOS):
        seg.value(patron[i])
#=============================================================================
# BOTÓN DE COMPRA
boton = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_UP)
#=============================================================================
# LEDs DE DISPONIBILIDAD
# Verde encendido = hay stock del producto seleccionado actualmente
# Rojo encendido  = sin stock, no se puede comprar

led_verde = machine.Pin(8, machine.Pin.OUT)
led_rojo  = machine.Pin(9, machine.Pin.OUT)
 
def actualizar_leds(producto):
    """
    Enciende el LED verde si hay stock, rojo si no hay.
    Solo uno puede estar encendido a la vez.
    """
    if inventario[producto] > 0:
        led_verde.value(1)
        led_rojo.value(0)
    else:
        led_verde.value(0)
        led_rojo.value(1)
#=============================================================================
# SERVO

servo_pwm = machine.PWM(machine.Pin(10))
servo_pwm.freq(50)

def mover_servo(angulo):
    # pulso entre 1ms (1_000_000 ns) y 2ms (2_000_000 ns)
    pulso_ns = int(1_000_000 + (angulo / 180) * 1_000_000)
    servo_pwm.duty_ns(pulso_ns)

def abrir_compuerta():
  mover_servo(90)         # Abrir
  utime.sleep(2)          # Esperar 2 segundos
  mover_servo(0)          # Cerrar
#=============================================================================
# LÓGICA DE COMPRA
def comprar_producto(producto):
    if inventario[producto] > 0:
        inventario[producto] -= 1   # Descontar una unidad
        abrir_compuerta()           # Entregar el producto físicamente
        return True
 
    # Sin stock: no hacer nada, retornar False
    return False
#=============================================================================
# CONEXIÓN WiFi
ssid = ""
password = ""
port = ""

def conectar_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
 
    for intento in range(10):
        if wlan.isconnected():
            print("WiFi conectado. IP del Pico W:", wlan.ifconfig()[0])
            return True
        print("Conectando WiFi... intento", intento + 1, "de 10")
        utime.sleep(1)
 
    print("Error: no se pudo conectar al WiFi.")
    return False
#=============================================================================
# SERVIDOR TCP
mantenimiento = False 
def crear_servidor(puerto=5000):
    srv = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    srv.bind(('', puerto))
    srv.listen(1)          # Cola máxima de 1 conexión pendiente
    srv.setblocking(False)
    print("Servidor TCP escuchando en puerto", puerto)
    return srv

def manejar_cliente(servidor):
    global mantenimiento
    try:
        conn, addr = servidor.accept()
        datos = ujson.loads(conn.recv(256).decode())
 
        if datos.get('cmd') == 'status':
            respuesta = ujson.dumps({
                'inventario': inventario,
                'mantenimiento': mantenimiento
            })
            conn.send(respuesta.encode())
 
        elif datos.get('cmd') == 'mantenimiento':
            mantenimiento = datos.get('v', False)
            conn.send(ujson.dumps({'ok': True}).encode())
 
        conn.close()
 
    except OSError:
        pass
#=============================================================================
# PROGRAMA PRINCIPAL
def main():
    # Posición inicial: compuerta cerrada
    mover_servo(0)
 
    # Apagar ambos LEDs al inicio
    led_verde.value(0)
    led_rojo.value(0)
 
    # Conectar al WiFi (cambiá estos datos por los de tu red)
    conectar_wifi('TU_SSID', 'TU_PASSWORD')
 
    # Crear servidor TCP para recibir comandos de la app de administración
    servidor = crear_servidor(puerto=5000)
 
    ultimo_estado_boton = 1   # 1 = no presionado (PULL_UP activo en reposo)
 #=============================================================================
 # LOOP PRINCIPAL
 while True:
 
        # --- 1. Leer producto seleccionado con el potenciómetro ---
        producto = leer_producto()
 
        # --- 2. Mostrar stock del producto en el display ---
        mostrar_digito(inventario[producto])
 
        # --- 3. Actualizar LEDs ---
        actualizar_leds(producto)
 
        # --- 4. Leer estado del botón y detectar flanco bajante (1 → 0) ---
        estado_actual = boton.value()
 
        if estado_actual == 0 and ultimo_estado_boton == 1:
            # Posible pulsación detectada → aplicar anti-rebote
            utime.sleep_ms(50)
 
            if boton.value() == 0:   # Confirmar que sigue presionado
 
                if mantenimiento:
                    # Máquina en mantenimiento: bloquear todas las compras
                    print("Máquina en mantenimiento. Compra bloqueada.")
 
                else:
                    # --- 5. Intentar compra ---
                    exito = comprar_producto(producto)
 
                    if exito:
                        print("Compra exitosa. Producto", producto + 1,
                              "| Stock restante:", inventario[producto])
                    else:
                        print("Sin stock para producto", producto + 1,
                              "| Compra rechazada.")
 
        ultimo_estado_boton = estado_actual   # Actualizar estado previo
 
        # --- 6. Atender comandos de la app PC (no bloquea) ---
        manejar_cliente(servidor)
 
        # --- Pausa del ciclo: 100 ms (~10 lecturas/segundo) ---
        utime.sleep_ms(100)
 
 
# Punto de entrada — main.py se ejecuta automáticamente al encender el Pico
main()
