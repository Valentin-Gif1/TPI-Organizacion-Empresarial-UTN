"""
=============================================================
TechSoluciones S.A. - Chatbot de Soporte Tecnico Nivel 1
=============================================================
Materia: Organizacion Empresarial - TUPaD UTN
Alumno: Valentin Carbone
=============================================================
"""

import csv
import os
import re
from datetime import datetime

# ---------------------------------------------------------
#  CONFIGURACION
# ---------------------------------------------------------
ARCHIVO_BD = "base_datos.csv"
ARCHIVO_TICKETS = "tickets.csv"

# ---------------------------------------------------------
#  MAQUINA DE ESTADOS
# ---------------------------------------------------------
ESTADOS = {
    "INICIO":                "Saludo y solicitud de datos",
    "MENU_CATEGORIA":        "Seleccion de categoria de problema",
    "VALIDAR_CATEGORIA":     "Validacion de opcion ingresada",
    "BUSCAR_SOLUCION":       "Consulta en base de datos",
    "ENTREGAR_SOLUCION":     "Entrega de solucion al usuario",
    "CONFIRMAR_RESOLUCION":  "Confirmacion de si se resolvio",
    "GENERAR_TICKET":        "Generacion de ticket para tecnico senior",
    "CERRADO_OK":            "Caso cerrado correctamente",
    "CERRADO_ESCALADO":      "Caso escalado a tecnico senior",
}

# ---------------------------------------------------------
#  UTILIDADES
# ---------------------------------------------------------
def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")

def separador():
    print("-" * 55)

def encabezado():
    separador()
    print("  TECHSOLUCIONES S.A. - SOPORTE TECNICO NIVEL 1")
    print("  Bot de Atencion Automatizada")
    separador()

def cargar_base_datos():
    """Carga el CSV de problemas y soluciones en una lista de dicts."""
    problemas = []
    try:
        with open(ARCHIVO_BD, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for fila in reader:
                problemas.append(fila)
    except FileNotFoundError:
        print("[ERROR] No se encontro el archivo '" + ARCHIVO_BD + "'.")
        print("Asegurese de que base_datos.csv este en la misma carpeta.")
        input("Presione Enter para salir...")
        exit()
    return problemas

def obtener_categorias(problemas):
    """Extrae las categorias unicas de la base de datos."""
    categorias = []
    for p in problemas:
        if p["categoria"] not in categorias:
            categorias.append(p["categoria"])
    return categorias

def buscar_soluciones(problemas, categoria):
    """Devuelve todos los problemas de una categoria."""
    return [p for p in problemas if p["categoria"] == categoria]

def registrar_ticket(nombre, sector, categoria, descripcion, estado):
    """Registra el resultado en el archivo tickets.csv."""
    existe = os.path.exists(ARCHIVO_TICKETS)
    with open(ARCHIVO_TICKETS, "a", newline="", encoding="utf-8") as f:
        campos = ["id_ticket", "fecha_hora", "nombre", "sector",
                  "categoria", "descripcion", "estado"]
        writer = csv.DictWriter(f, fieldnames=campos)
        if not existe:
            writer.writeheader()
        id_ticket = "TKT-" + datetime.now().strftime("%Y%m%d%H%M%S")
        writer.writerow({
            "id_ticket":   id_ticket,
            "fecha_hora":  datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "nombre":      nombre,
            "sector":      sector,
            "categoria":   categoria,
            "descripcion": descripcion,
            "estado":      estado,
        })
    return id_ticket

def validar_opcion_numerica(texto, minimo, maximo):
    """
    Valida que la entrada sea un numero dentro del rango valido.
    Retorna (True, numero) o (False, mensaje_error).
    """
    texto = texto.strip()
    if not texto.isdigit():
        return False, "ERROR: '" + texto + "' no es un numero. Ingrese entre " + str(minimo) + " y " + str(maximo) + "."
    numero = int(texto)
    if numero < minimo or numero > maximo:
        return False, "ERROR: Opcion fuera de rango. Ingrese entre " + str(minimo) + " y " + str(maximo) + "."
    return True, numero

def validar_texto_no_vacio(texto, nombre_campo):
    """
    Valida que el texto no este vacio.
    Retorna (True, texto) o (False, mensaje_error).
    """
    texto = texto.strip()
    if not texto:
        return False, "ERROR: El campo '" + nombre_campo + "' no puede estar vacio."
    if len(texto) < 2:
        return False, "ERROR: El campo '" + nombre_campo + "' es demasiado corto. Minimo 2 caracteres."
    return True, texto

def validar_si_no(entrada):
    """
    Valida respuesta si/no.
    Retorna (True, bool) o (False, mensaje_error).
    """
    entrada = entrada.strip().lower()
    if entrada in ["s", "si", "1", "yes", "y"]:
        return True, True
    elif entrada in ["n", "no", "2"]:
        return True, False
    else:
        return False, "ERROR: Respuesta no reconocida. Ingrese 's' para SI o 'n' para NO."

# ---------------------------------------------------------
#  ESTADOS DEL BOT
# ---------------------------------------------------------

def estado_inicio():
    """
    ESTADO: INICIO
    Saluda y solicita nombre y sector.
    Permite hasta 3 intentos por campo.
    """
    print("\nBienvenido al sistema de soporte tecnico de TechSoluciones S.A.")
    print("Soy el asistente virtual de IT. Voy a ayudarte a resolver")
    print("tu problema tecnico de forma rapida y eficiente.\n")
    separador()

    intentos = 0
    nombre = ""
    while True:
        nombre_raw = input("Cual es tu nombre? ").strip()
        valido, resultado = validar_texto_no_vacio(nombre_raw, "nombre")
        if valido:
            nombre = resultado
            break
        else:
            intentos += 1
            print(resultado)
            if intentos >= 3:
                print("AVISO: Demasiados intentos fallidos. Reiniciando...")
                return None, None

    intentos = 0
    sector = ""
    while True:
        sector_raw = input("De que sector sos? (ej: Administracion, Ventas, IT) ").strip()
        valido, resultado = validar_texto_no_vacio(sector_raw, "sector")
        if valido:
            sector = resultado
            break
        else:
            intentos += 1
            print(resultado)
            if intentos >= 3:
                print("AVISO: Demasiados intentos fallidos. Reiniciando...")
                return None, None

    print("\nHola, " + nombre + " de " + sector + ". En que puedo ayudarte hoy?")
    return nombre, sector


def estado_menu_categoria(categorias):
    """
    ESTADO: MENU_CATEGORIA
    Muestra las categorias y retorna la elegida.
    Si falla 3 veces, retorna 'ESCALAR_DIRECTO'.
    """
    separador()
    print("\nCATEGORIAS DE PROBLEMAS DISPONIBLES:\n")
    for i, cat in enumerate(categorias, 1):
        print("  " + str(i) + ". " + cat)
    print("  " + str(len(categorias) + 1) + ". Mi problema no esta en la lista")
    separador()

    intentos = 0
    while True:
        entrada = input("\nIngresa el numero de tu problema (1-" + str(len(categorias)+1) + "): ")
        valido, resultado = validar_opcion_numerica(entrada, 1, len(categorias) + 1)
        if valido:
            if resultado == len(categorias) + 1:
                return None
            return categorias[resultado - 1]
        else:
            intentos += 1
            print(resultado)
            if intentos >= 3:
                print("AVISO: Demasiados intentos. Derivando con un tecnico humano...")
                return "ESCALAR_DIRECTO"


def estado_menu_subcategoria(problemas_categoria):
    """
    ESTADO: BUSCAR_SOLUCION
    Muestra los problemas especificos de la categoria elegida.
    """
    separador()
    print("\nPROBLEMAS ENCONTRADOS EN ESTA CATEGORIA:\n")
    for i, p in enumerate(problemas_categoria, 1):
        print("  " + str(i) + ". " + p["descripcion"])
    print("  " + str(len(problemas_categoria) + 1) + ". Mi problema es diferente")
    separador()

    intentos = 0
    while True:
        entrada = input("\nSelecciona tu problema (1-" + str(len(problemas_categoria)+1) + "): ")
        valido, resultado = validar_opcion_numerica(entrada, 1, len(problemas_categoria) + 1)
        if valido:
            if resultado == len(problemas_categoria) + 1:
                return None
            return problemas_categoria[resultado - 1]
        else:
            intentos += 1
            print(resultado)
            if intentos >= 3:
                print("AVISO: Demasiados intentos. Derivando con un tecnico humano...")
                return "ESCALAR_DIRECTO"


def estado_entregar_solucion(problema):
    """
    ESTADO: ENTREGAR_SOLUCION
    Muestra la solucion paso a paso.
    Retorna True si es automatica, False si requiere escalado.
    """
    separador()
    print("\nPROBLEMA IDENTIFICADO: " + problema["descripcion"] + "\n")

    if problema["requiere_escalado"] == "Si":
        print("AVISO: Este problema requiere tecnico especializado.")
        print("Te compartimos los pasos iniciales que podes intentar:\n")

    pasos = re.split(r'(?=\d+\.)', problema["solucion"])
    for paso in pasos:
        paso = paso.strip()
        if paso:
            print("  >> " + paso)
    print()
    return problema["requiere_escalado"] != "Si"


def estado_confirmar_resolucion():
    """
    ESTADO: CONFIRMAR_RESOLUCION
    Pregunta si el problema se resolvio.
    Retorna True (resuelto) o False (no resuelto).
    """
    separador()
    intentos = 0
    while True:
        entrada = input("Los pasos anteriores resolvieron tu problema? (s/n): ")
        valido, resultado = validar_si_no(entrada)
        if valido:
            return resultado
        else:
            intentos += 1
            print(resultado)
            if intentos >= 3:
                print("AVISO: No se pudo interpretar la respuesta. Se genera ticket preventivo.")
                return False


def estado_generar_ticket(nombre, sector, categoria, descripcion):
    """
    ESTADO: GENERAR_TICKET
    Genera y registra un ticket de escalado.
    """
    separador()
    print("\nGenerando ticket de escalado...\n")
    id_ticket = registrar_ticket(nombre, sector, categoria, descripcion, "ESCALADO")
    print("  Ticket generado: " + id_ticket)
    print("  Un tecnico senior se pondra en contacto con vos en el sector " + sector + ".")
    return id_ticket


def estado_cierre_ok(nombre, sector, categoria, descripcion):
    """ESTADO: CERRADO_OK - Registra caso resuelto."""
    separador()
    registrar_ticket(nombre, sector, categoria, descripcion, "RESUELTO")
    print("\nEl problema quedo registrado como RESUELTO.")
    print("Gracias, " + nombre + ". Que tengas un buen dia!")
    separador()


def estado_cierre_escalado(nombre):
    """ESTADO: CERRADO_ESCALADO - Mensaje de cierre para casos escalados."""
    separador()
    print("\nEl caso fue escalado correctamente, " + nombre + ".")
    print("Recibiras atencion personalizada a la brevedad.")
    print("Gracias por usar el sistema de soporte de TechSoluciones S.A.")
    separador()

# ---------------------------------------------------------
#  FLUJO PRINCIPAL
# ---------------------------------------------------------

def ejecutar_bot():
    """
    Funcion principal que controla el flujo completo del bot
    siguiendo la maquina de estados definida en el BPMN.
    """
    limpiar_pantalla()
    encabezado()

    problemas = cargar_base_datos()
    categorias = obtener_categorias(problemas)

    estado_actual = "INICIO"
    nombre, sector = estado_inicio()
    if nombre is None:
        print("Sesion terminada por inactividad.")
        return

    estado_actual = "MENU_CATEGORIA"
    categoria_elegida = estado_menu_categoria(categorias)

    if categoria_elegida == "ESCALAR_DIRECTO" or categoria_elegida is None:
        estado_actual = "GENERAR_TICKET"
        estado_generar_ticket(nombre, sector, "Sin categoria", "Problema no identificado")
        estado_cierre_escalado(nombre)
        return

    estado_actual = "BUSCAR_SOLUCION"
    problemas_cat = buscar_soluciones(problemas, categoria_elegida)
    problema_elegido = estado_menu_subcategoria(problemas_cat)

    if problema_elegido == "ESCALAR_DIRECTO" or problema_elegido is None:
        estado_actual = "GENERAR_TICKET"
        estado_generar_ticket(nombre, sector, categoria_elegida, "Problema especifico no registrado")
        estado_cierre_escalado(nombre)
        return

    estado_actual = "ENTREGAR_SOLUCION"
    tiene_solucion_auto = estado_entregar_solucion(problema_elegido)

    if not tiene_solucion_auto:
        estado_actual = "GENERAR_TICKET"
        estado_generar_ticket(nombre, sector, categoria_elegida, problema_elegido["descripcion"])
        estado_cierre_escalado(nombre)
        return

    estado_actual = "CONFIRMAR_RESOLUCION"
    se_resolvio = estado_confirmar_resolucion()

    if se_resolvio:
        estado_actual = "CERRADO_OK"
        estado_cierre_ok(nombre, sector, categoria_elegida, problema_elegido["descripcion"])
    else:
        estado_actual = "GENERAR_TICKET"
        estado_generar_ticket(nombre, sector, categoria_elegida, problema_elegido["descripcion"])
        estado_cierre_escalado(nombre)

    print("\n[Sistema] Estado final: " + estado_actual)
    print("[Sistema] Registro guardado en: " + ARCHIVO_TICKETS)
    separador()


# ---------------------------------------------------------
#  PUNTO DE ENTRADA
# ---------------------------------------------------------
if __name__ == "__main__":
    continuar = True
    while continuar:
        ejecutar_bot()
        separador()
        respuesta = input("\nDeseas iniciar una nueva consulta? (s/n): ").strip().lower()
        if respuesta not in ["s", "si"]:
            print("\nGracias por usar TechSoluciones S.A. Hasta pronto!")
            continuar = False