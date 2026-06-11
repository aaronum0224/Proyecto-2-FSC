#===========================================================================
# CElect - Administrador de Máquina Dispensadora
# CE-1104 Fundamentos de Sistemas Computacionales I Semestre 2026
#===========================================================================

import tkinter as tk
from tkinter import messagebox
import socket
import json
import threading
import time
import urllib.request

# Configuración 
PICO_IP   = '192.168.1.100'  
PICO_PORT = 5000
PRECIO    = 250        # Colones por producto

# Estado global 
inventario      = [0, 0, 0]
ventas          = [0, 0, 0]
inventario_prev = None
mantenimiento   = False
tipo_cambio     = None


# ===========================================================================
# COMUNICACIÓN CON EL PICO W
# ===========================================================================
def enviar_comando(cmd_dict):
    """Envía un JSON al Pico y retorna la respuesta, o None si falla."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((PICO_IP, PICO_PORT))
            s.sendall(json.dumps(cmd_dict).encode())
            return json.loads(s.recv(1024).decode())
    except Exception:
        return None


# ===========================================================================
# API TIPO DE CAMBIO — Hacienda Costa Rica 
# ===========================================================================
def obtener_tipo_cambio():
    """Retorna el tipo de cambio venta USD/CRC desde Hacienda, o None."""
    try:
        url = "https://api.hacienda.go.cr/indicadores/tc/dolar"
        req = urllib.request.Request(url, headers={'User-Agent': 'CElect/1.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return float(json.loads(r.read().decode())['venta']['valor'])
    except Exception:
        return None


# ===========================================================================
# INTERFAZ
# ===========================================================================
def construir_ui(root):
    global lbl_estado, lbl_tc, btn_mant
    global lbl_stock, lbl_ventas, lbl_colones, lbl_dolares
    global lbl_total_ventas, lbl_total_colones, lbl_total_dolares

    root.title("CElect - Administrador")
    root.resizable(False, False)
    BG = '#f0f0f0'
    root.configure(bg=BG)

    fuente      = ('Arial', 10)
    fuente_bold = ('Arial', 10, 'bold')

    # Título 
    tk.Label(root, text="CElect — Administrador",
             font=('Arial', 13, 'bold'), bg=BG).pack(pady=(12, 2))

    lbl_estado = tk.Label(root, text="Conectando...", font=fuente, bg=BG, fg='gray')
    lbl_estado.pack()

    # Stock 
    frame_stock = tk.LabelFrame(root, text="Stock actual", font=fuente_bold,
                                 bg=BG, padx=10, pady=6)
    frame_stock.pack(padx=16, pady=(10, 4), fill='x')

    lbl_stock = []
    for i in range(3):
        fila = tk.Frame(frame_stock, bg=BG)
        fila.pack(fill='x', pady=2)
        tk.Label(fila, text=f"Producto {i+1}:", font=fuente,
                 bg=BG, width=12, anchor='w').pack(side='left')
        lbl = tk.Label(fila, text="0 uds", font=fuente_bold, bg=BG, fg='green')
        lbl.pack(side='left')
        lbl_stock.append(lbl)

    # Estadísticas 
    frame_stats = tk.LabelFrame(root, text="Estadísticas", font=fuente_bold,
                                 bg=BG, padx=10, pady=6)
    frame_stats.pack(padx=16, pady=4, fill='x')

    # Encabezado
    enc = tk.Frame(frame_stats, bg=BG)
    enc.pack(fill='x')
    for texto, ancho in [('', 10), ('Ventas', 8), ('Colones', 12), ('Dólares', 10)]:
        tk.Label(enc, text=texto, font=fuente_bold, bg=BG,
                 width=ancho, anchor='w').pack(side='left')

    lbl_ventas  = []
    lbl_colones = []
    lbl_dolares = []

    for i in range(3):
        fila = tk.Frame(frame_stats, bg=BG)
        fila.pack(fill='x', pady=1)

        tk.Label(fila, text=f"Producto {i+1}", font=fuente,
                 bg=BG, width=10, anchor='w').pack(side='left')

        lv = tk.Label(fila, text='0', font=fuente, bg=BG, width=8, anchor='w')
        lv.pack(side='left')
        lbl_ventas.append(lv)

        lc = tk.Label(fila, text='₡ 0', font=fuente, bg=BG, width=12, anchor='w')
        lc.pack(side='left')
        lbl_colones.append(lc)

        ld = tk.Label(fila, text='$ -', font=fuente, bg=BG, width=10, anchor='w')
        ld.pack(side='left')
        lbl_dolares.append(ld)

    # Separador + totales
    tk.Frame(frame_stats, bg='#cccccc', height=1).pack(fill='x', pady=4)

    fila_t = tk.Frame(frame_stats, bg=BG)
    fila_t.pack(fill='x')
    tk.Label(fila_t, text='TOTAL', font=fuente_bold, bg=BG,
             width=10, anchor='w').pack(side='left')

    lbl_total_ventas = tk.Label(fila_t, text='0', font=fuente_bold,
                                 bg=BG, width=8, anchor='w')
    lbl_total_ventas.pack(side='left')

    lbl_total_colones = tk.Label(fila_t, text='₡ 0', font=fuente_bold,
                                  bg=BG, width=12, anchor='w')
    lbl_total_colones.pack(side='left')

    lbl_total_dolares = tk.Label(fila_t, text='$ -', font=fuente_bold,
                                  bg=BG, width=10, anchor='w')
    lbl_total_dolares.pack(side='left')

    lbl_tc = tk.Label(frame_stats, text="Tipo de cambio: cargando...",
                       font=('Arial', 8), bg=BG, fg='gray')
    lbl_tc.pack(anchor='e', pady=(4, 0))

    # Mantenimiento 
    frame_mant = tk.Frame(root, bg=BG)
    frame_mant.pack(pady=(8, 14))

    btn_mant = tk.Button(frame_mant, text="Activar mantenimiento",
                          font=fuente_bold, bg='#e74c3c', fg='white',
                          relief='flat', padx=10, pady=5,
                          command=toggle_mantenimiento)
    btn_mant.pack()


# ===========================================================================
# LÓGICA DE ACTUALIZACIÓN
# ===========================================================================
def refrescar_ui(root):
    """Actualiza todos los labels con los datos más recientes."""
    global tipo_cambio

    # Estado de conexión y mantenimiento
    if mantenimiento:
        lbl_estado.config(text="⚠ MANTENIMIENTO", fg='orange')
        btn_mant.config(text="Desactivar mantenimiento", bg='#27ae60')
        root.configure(bg='#fff3cd')
    else:
        lbl_estado.config(
            text="● Conectado" if inventario != [0,0,0] else "● Sin conexión",
            fg='green' if inventario != [0,0,0] else 'red'
        )
        btn_mant.config(text="Activar mantenimiento", bg='#e74c3c')
        root.configure(bg='#f0f0f0')

    # Stock
    for i in range(3):
        u = inventario[i]
        lbl_stock[i].config(text=f"{u} uds", fg='green' if u > 0 else 'red')

    # Estadísticas
    total_v = sum(ventas)
    total_c = total_v * PRECIO

    for i in range(3):
        c = ventas[i] * PRECIO
        lbl_ventas[i].config(text=str(ventas[i]))
        lbl_colones[i].config(text=f'₡ {c:,}')
        if tipo_cambio:
            lbl_dolares[i].config(text=f'$ {c/tipo_cambio:,.2f}')
        else:
            lbl_dolares[i].config(text='$ N/D')

    lbl_total_ventas.config(text=str(total_v))
    lbl_total_colones.config(text=f'₡ {total_c:,}')
    if tipo_cambio:
        lbl_total_dolares.config(text=f'$ {total_c/tipo_cambio:,.2f}')
        lbl_tc.config(text=f"Tipo de cambio: ₡ {tipo_cambio:,.2f} / USD")
    else:
        lbl_total_dolares.config(text='$ N/D')
        lbl_tc.config(text="Tipo de cambio: no disponible")


def toggle_mantenimiento():
    """Activa o desactiva el modo mantenimiento enviando comando al Pico."""
    global mantenimiento
    nuevo = not mantenimiento
    resp = enviar_comando({'cmd': 'mantenimiento', 'v': nuevo})
    if resp and resp.get('ok'):
        mantenimiento = nuevo
    else:
        messagebox.showwarning("Sin conexión",
                               "No se pudo conectar al Pico W.\n"
                               "Verificá la IP y la red WiFi.")


def loop_actualizacion(root):
    """Hilo secundario: consulta el Pico cada 2 segundos y detecta ventas
    comparando el inventario anterior con el actual."""
    global inventario, inventario_prev, ventas, mantenimiento

    while True:
        datos = enviar_comando({'cmd': 'status'})

        if datos:
            nuevo_inv = datos.get('inventario', [0, 0, 0])
            mantenimiento = datos.get('mantenimiento', False)

            # Detectar ventas: stock bajó -> alguien compró
            if inventario_prev is not None:
                for i in range(3):
                    diff = inventario_prev[i] - nuevo_inv[i]
                    if diff > 0:
                        ventas[i] += diff

            inventario_prev = list(nuevo_inv)
            inventario = nuevo_inv

        # Actualizar UI en el hilo principal
        root.after(0, lambda: refrescar_ui(root))
        time.sleep(2)


# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == '__main__':
    root = tk.Tk()
    construir_ui(root)

    # Obtener tipo de cambio en hilo separado
    def fetch_tc():
        global tipo_cambio
        tipo_cambio = obtener_tipo_cambio()
    threading.Thread(target=fetch_tc, daemon=True).start()

    # Iniciar hilo de actualización
    threading.Thread(target=loop_actualizacion, args=(root,), daemon=True).start()

    root.mainloop()
