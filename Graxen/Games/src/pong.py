"""
=====================================================================
 PONG NEON — Edición Synthwave
=====================================================================
Un Pong moderno y pulido hecho con la librería `arcade`.

Características:
    - Menú principal con título animado y selección de modo de juego.
    - Estados: Menú, Jugando, Pausa y Game Over.
    - Modo IA (sigue la pelota) o modo 2 Jugadores (mismo teclado).
    - Física de rebote con ángulo dinámico y aumento de velocidad.
    - Estética Synthwave / Neon Retro con partículas y destellos.

Controles:
    Jugador 1 (Izquierda): W (arriba) / S (abajo)
    Jugador 2 (Derecha, si hay 2 jugadores): Flecha Arriba / Flecha Abajo
    Menú: [I] Modo IA   [D] Modo Dos Jugadores   ESPACIO/ENTER: iniciar
    En partida: P = Pausar / Reanudar

Requisitos: únicamente la librería `arcade` y la librería estándar
(`math`, `random`). Un solo archivo, orientado a objetos.
=====================================================================
"""

import arcade
import math
import random


# =====================================================================
# CONFIGURACIÓN GENERAL Y CONSTANTES
# =====================================================================

ANCHO_PANTALLA = 900
ALTO_PANTALLA = 600
TITULO_PANTALLA = "PONG NEON // Synthwave Edition"

# --- Paleta de colores estilo Synthwave / Neon Retro ---
COLOR_FONDO = (10, 8, 28)             # Azul noche casi negro
COLOR_CYAN = (0, 255, 240)            # Neón cyan -> Jugador 1 (izquierda)
COLOR_MAGENTA = (255, 0, 200)         # Neón magenta -> Jugador 2 / IA (derecha)
COLOR_VERDE_NEON = (57, 255, 140)     # Verde neón -> Pelota
COLOR_BLANCO = (235, 235, 250)
COLOR_GRIS_NEON = (170, 160, 210)
COLOR_FLASH = (255, 255, 140)         # Color del destello al chocar
COLOR_RED_CENTRAL = (110, 80, 170)    # Color de la red punteada
COLOR_LINEA_FONDO = (70, 45, 110, 70)  # Líneas decorativas de fondo (con alpha)

# --- Estados posibles del juego ---
ESTADO_MENU = "menu"
ESTADO_JUGANDO = "jugando"
ESTADO_PAUSA = "pausa"
ESTADO_GAME_OVER = "game_over"

# --- Modos de juego disponibles ---
MODO_IA = "ia"
MODO_DOS_JUGADORES = "dos_jugadores"

# --- Configuración de las paletas ---
PALETA_ANCHO = 16
PALETA_ALTO = 100
PALETA_VELOCIDAD = 420       # píxeles por segundo
PALETA_MARGEN = 40           # distancia desde el borde de la pantalla

# --- Configuración de la pelota ---
PELOTA_RADIO = 10
PELOTA_VELOCIDAD_INICIAL = 320
PELOTA_INCREMENTO_VELOCIDAD = 1.05   # +5% de velocidad en cada choque con paleta
PELOTA_VELOCIDAD_MAXIMA = 950
ANGULO_MAXIMO_REBOTE = 55            # grados; ángulo al golpear el borde de la paleta
TIEMPO_ESPERA_SAQUE = 0.8            # segundos de pausa antes de lanzar la pelota

# --- Reglas de la partida ---
PUNTOS_PARA_GANAR = 5


# =====================================================================
# CLASE: Partícula (efecto visual de choque)
# =====================================================================
class Particula:
    """Pequeña partícula que se dispersa al chocar la pelota contra algo."""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

        angulo = random.uniform(0, math.pi * 2)
        velocidad = random.uniform(70, 240)
        self.vx = math.cos(angulo) * velocidad
        self.vy = math.sin(angulo) * velocidad

        self.vida_maxima = random.uniform(0.25, 0.5)
        self.vida = self.vida_maxima
        self.radio = random.uniform(2, 4)

    def actualizar(self, delta_time):
        """Mueve la partícula y reduce su tiempo de vida."""
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.vx *= 0.90  # fricción para que la partícula frene poco a poco
        self.vy *= 0.90
        self.vida -= delta_time

    def esta_viva(self):
        return self.vida > 0

    def dibujar(self):
        """Dibuja la partícula con transparencia proporcional a su vida restante."""
        alpha = max(0, min(255, int(255 * (self.vida / self.vida_maxima))))
        color_con_alpha = (self.color[0], self.color[1], self.color[2], alpha)
        arcade.draw_circle_filled(self.x, self.y, self.radio, color_con_alpha)


# =====================================================================
# CLASE: Paleta (raqueta de cada jugador)
# =====================================================================
class Paleta:
    """Representa la paleta/raqueta que controla un jugador o la IA."""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.ancho = PALETA_ANCHO
        self.alto = PALETA_ALTO
        self.color_base = color
        self.color_actual = color
        self.vy = 0.0
        self.tiempo_flash = 0.0

    def mover(self, delta_time):
        """Actualiza la posición vertical respetando los límites de la pantalla."""
        self.y += self.vy * delta_time

        limite_inferior = self.alto / 2
        limite_superior = ALTO_PANTALLA - self.alto / 2
        self.y = max(limite_inferior, min(self.y, limite_superior))

        # Apagar el destello de color con el paso del tiempo
        if self.tiempo_flash > 0:
            self.tiempo_flash -= delta_time
            if self.tiempo_flash <= 0:
                self.color_actual = self.color_base

    def activar_flash(self):
        """Cambia momentáneamente el color de la paleta al recibir un impacto."""
        self.color_actual = COLOR_FLASH
        self.tiempo_flash = 0.12

    def dibujar(self):
        izquierda = self.x - self.ancho / 2
        abajo = self.y - self.alto / 2

        # Halo/resplandor neón: una versión más grande y translúcida detrás
        color_glow = (self.color_base[0], self.color_base[1], self.color_base[2], 60)
        arcade.draw_lbwh_rectangle_filled(
            izquierda - 4, abajo - 4, self.ancho + 8, self.alto + 8, color_glow
        )
        # Cuerpo sólido de la paleta
        arcade.draw_lbwh_rectangle_filled(izquierda, abajo, self.ancho, self.alto, self.color_actual)


# =====================================================================
# CLASE: Pelota
# =====================================================================
class Pelota:
    """Representa la pelota y toda su física de movimiento y rebote."""

    def __init__(self):
        self.x = ANCHO_PANTALLA / 2
        self.y = ALTO_PANTALLA / 2
        self.radio = PELOTA_RADIO
        self.vx = 0.0
        self.vy = 0.0
        self.color_base = COLOR_VERDE_NEON
        self.color_actual = COLOR_VERDE_NEON
        self.tiempo_flash = 0.0

    def lanzar(self, hacia_derecha):
        """Lanza la pelota desde el centro en una dirección aleatoria."""
        self.x = ANCHO_PANTALLA / 2
        self.y = ALTO_PANTALLA / 2

        # Ángulo aleatorio de salida entre -30° y 30° respecto a la horizontal
        angulo = random.uniform(-math.pi / 6, math.pi / 6)
        direccion_x = 1 if hacia_derecha else -1

        self.vx = math.cos(angulo) * PELOTA_VELOCIDAD_INICIAL * direccion_x
        self.vy = math.sin(angulo) * PELOTA_VELOCIDAD_INICIAL

    def actualizar(self, delta_time):
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

        if self.tiempo_flash > 0:
            self.tiempo_flash -= delta_time
            if self.tiempo_flash <= 0:
                self.color_actual = self.color_base

    def activar_flash(self):
        self.color_actual = COLOR_FLASH
        self.tiempo_flash = 0.1

    def rebotar_pared(self):
        """Invierte la velocidad vertical al chocar con el techo o el piso."""
        self.vy *= -1
        self.activar_flash()

    def rebotar_paleta(self, paleta, es_paleta_izquierda):
        """
        Calcula el nuevo vector de velocidad tras chocar con una paleta.
        El ángulo de salida depende de en qué parte de la paleta impactó
        y la velocidad aumenta un 5% en cada choque.
        """
        velocidad_actual = math.hypot(self.vx, self.vy)
        nueva_velocidad = min(velocidad_actual * PELOTA_INCREMENTO_VELOCIDAD, PELOTA_VELOCIDAD_MAXIMA)

        # Desplazamiento relativo del punto de impacto: -1 (borde inferior) a 1 (borde superior)
        desplazamiento = (self.y - paleta.y) / (paleta.alto / 2)
        desplazamiento = max(-1.0, min(1.0, desplazamiento))
        angulo = math.radians(desplazamiento * ANGULO_MAXIMO_REBOTE)

        direccion_x = 1 if es_paleta_izquierda else -1
        self.vx = math.cos(angulo) * nueva_velocidad * direccion_x
        self.vy = math.sin(angulo) * nueva_velocidad

        self.activar_flash()
        paleta.activar_flash()

    def dibujar(self):
        # Resplandor neón detrás de la pelota (dos capas translúcidas)
        c = self.color_actual
        arcade.draw_circle_filled(self.x, self.y, self.radio + 8, (c[0], c[1], c[2], 40))
        arcade.draw_circle_filled(self.x, self.y, self.radio + 4, (c[0], c[1], c[2], 90))
        arcade.draw_circle_filled(self.x, self.y, self.radio, self.color_actual)


# =====================================================================
# CLASE PRINCIPAL: JuegoPong (ventana de arcade)
# =====================================================================
class JuegoPong(arcade.Window):
    """Clase principal que administra la ventana, los estados y la lógica del juego."""

    def __init__(self):
        super().__init__(ANCHO_PANTALLA, ALTO_PANTALLA, TITULO_PANTALLA)
        self.background_color = COLOR_FONDO

        # --- Estado general ---
        self.estado = ESTADO_MENU
        self.modo_juego = MODO_IA

        # --- Objetos del juego ---
        self.paleta_izquierda = None
        self.paleta_derecha = None
        self.pelota = None
        self.particulas = []

        # --- Marcador ---
        self.puntos_izquierda = 0
        self.puntos_derecha = 0
        self.ganador = ""

        # --- Teclas presionadas actualmente ---
        self.tecla_w = False
        self.tecla_s = False
        self.tecla_arriba = False
        self.tecla_abajo = False

        # --- Control del saque (pequeña espera antes de lanzar la pelota) ---
        self.esperando_saque = False
        self.tiempo_saque = 0.0
        self.hacia_donde_sacar = True

        # --- Animación del título del menú ---
        self.tiempo_titulo = 0.0

        # Preparamos objetos iniciales para evitar referencias nulas
        self.iniciar_nueva_partida()

    # -----------------------------------------------------------------
    # PREPARACIÓN DE PARTIDAS Y SAQUES
    # -----------------------------------------------------------------
    def iniciar_nueva_partida(self):
        """Crea las paletas y la pelota, y reinicia el marcador a cero."""
        self.paleta_izquierda = Paleta(
            PALETA_MARGEN + PALETA_ANCHO / 2, ALTO_PANTALLA / 2, COLOR_CYAN
        )
        self.paleta_derecha = Paleta(
            ANCHO_PANTALLA - PALETA_MARGEN - PALETA_ANCHO / 2, ALTO_PANTALLA / 2, COLOR_MAGENTA
        )
        self.pelota = Pelota()
        self.particulas = []
        self.puntos_izquierda = 0
        self.puntos_derecha = 0
        self.ganador = ""
        self.iniciar_saque(hacia_derecha=random.choice([True, False]))

    def iniciar_saque(self, hacia_derecha):
        """Ubica la pelota en el centro y programa un breve retraso antes de lanzarla."""
        self.pelota.x = ANCHO_PANTALLA / 2
        self.pelota.y = ALTO_PANTALLA / 2
        self.pelota.vx = 0.0
        self.pelota.vy = 0.0
        self.hacia_donde_sacar = hacia_derecha
        self.esperando_saque = True
        self.tiempo_saque = TIEMPO_ESPERA_SAQUE

    # -----------------------------------------------------------------
    # ACTUALIZACIÓN (LÓGICA DEL JUEGO)
    # -----------------------------------------------------------------
    def on_update(self, delta_time):
        self.tiempo_titulo += delta_time

        if self.estado == ESTADO_JUGANDO:
            self._actualizar_jugando(delta_time)

        # Las partículas se actualizan en cualquier estado en que existan
        for particula in self.particulas:
            particula.actualizar(delta_time)
        self.particulas = [p for p in self.particulas if p.esta_viva()]

    def _actualizar_jugando(self, delta_time):
        # --- Movimiento de la paleta izquierda: Jugador 1 (W / S) ---
        self.paleta_izquierda.vy = 0
        if self.tecla_w:
            self.paleta_izquierda.vy = PALETA_VELOCIDAD
        elif self.tecla_s:
            self.paleta_izquierda.vy = -PALETA_VELOCIDAD
        self.paleta_izquierda.mover(delta_time)

        # --- Movimiento de la paleta derecha: Jugador 2 o IA ---
        if self.modo_juego == MODO_DOS_JUGADORES:
            self.paleta_derecha.vy = 0
            if self.tecla_arriba:
                self.paleta_derecha.vy = PALETA_VELOCIDAD
            elif self.tecla_abajo:
                self.paleta_derecha.vy = -PALETA_VELOCIDAD
        else:
            self._mover_ia()
        self.paleta_derecha.mover(delta_time)

        # --- Espera antes del saque: la pelota no se mueve todavía ---
        if self.esperando_saque:
            self.tiempo_saque -= delta_time
            if self.tiempo_saque <= 0:
                self.esperando_saque = False
                self.pelota.lanzar(self.hacia_donde_sacar)
            return

        # --- Física y colisiones de la pelota ---
        self.pelota.actualizar(delta_time)
        self._comprobar_colisiones()
        self._comprobar_puntos()

    def _mover_ia(self):
        """
        IA simple pero fluida: sigue la posición Y de la pelota.
        Usa una pequeña zona muerta y una velocidad proporcional a la
        distancia para que el movimiento se vea suave y no "perfecto".
        """
        diferencia = self.pelota.y - self.paleta_derecha.y
        zona_muerta = 10

        if abs(diferencia) < zona_muerta:
            self.paleta_derecha.vy = 0
        else:
            direccion = 1 if diferencia > 0 else -1
            velocidad_deseada = min(abs(diferencia) * 4, PALETA_VELOCIDAD) * 0.9
            self.paleta_derecha.vy = direccion * velocidad_deseada

    def _comprobar_colisiones(self):
        """Revisa y resuelve los choques de la pelota con paredes y paletas."""
        pelota = self.pelota

        # Rebote contra el borde superior
        if pelota.y + pelota.radio >= ALTO_PANTALLA:
            pelota.y = ALTO_PANTALLA - pelota.radio
            pelota.rebotar_pared()
            self._crear_particulas(pelota.x, pelota.y, pelota.color_base)

        # Rebote contra el borde inferior
        elif pelota.y - pelota.radio <= 0:
            pelota.y = pelota.radio
            pelota.rebotar_pared()
            self._crear_particulas(pelota.x, pelota.y, pelota.color_base)

        # Choque con la paleta izquierda (solo si la pelota va hacia la izquierda)
        if pelota.vx < 0 and self._colisiona_con_paleta(pelota, self.paleta_izquierda):
            pelota.x = self.paleta_izquierda.x + self.paleta_izquierda.ancho / 2 + pelota.radio
            pelota.rebotar_paleta(self.paleta_izquierda, es_paleta_izquierda=True)
            self._crear_particulas(pelota.x, pelota.y, COLOR_CYAN)

        # Choque con la paleta derecha (solo si la pelota va hacia la derecha)
        elif pelota.vx > 0 and self._colisiona_con_paleta(pelota, self.paleta_derecha):
            pelota.x = self.paleta_derecha.x - self.paleta_derecha.ancho / 2 - pelota.radio
            pelota.rebotar_paleta(self.paleta_derecha, es_paleta_izquierda=False)
            self._crear_particulas(pelota.x, pelota.y, COLOR_MAGENTA)

    @staticmethod
    def _colisiona_con_paleta(pelota, paleta):
        dentro_x = abs(pelota.x - paleta.x) <= (paleta.ancho / 2 + pelota.radio)
        dentro_y = abs(pelota.y - paleta.y) <= (paleta.alto / 2 + pelota.radio)
        return dentro_x and dentro_y

    def _crear_particulas(self, x, y, color, cantidad=12):
        for _ in range(cantidad):
            self.particulas.append(Particula(x, y, color))

    def _comprobar_puntos(self):
        """Detecta si la pelota salió de la pantalla y otorga el punto correspondiente."""
        pelota = self.pelota

        if pelota.x + pelota.radio < 0:
            # La pelota cruzó el borde izquierdo -> punto para el jugador derecho
            self.puntos_derecha += 1
            self._crear_particulas(0, pelota.y, COLOR_MAGENTA, 20)
            self._despues_de_punto(hacia_derecha=False)

        elif pelota.x - pelota.radio > ANCHO_PANTALLA:
            # La pelota cruzó el borde derecho -> punto para el jugador izquierdo
            self.puntos_izquierda += 1
            self._crear_particulas(ANCHO_PANTALLA, pelota.y, COLOR_CYAN, 20)
            self._despues_de_punto(hacia_derecha=True)

    def _despues_de_punto(self, hacia_derecha):
        """Comprueba si hay un ganador; si no, prepara el siguiente saque."""
        if self.puntos_izquierda >= PUNTOS_PARA_GANAR:
            self.ganador = "JUGADOR 1"
            self.estado = ESTADO_GAME_OVER
        elif self.puntos_derecha >= PUNTOS_PARA_GANAR:
            self.ganador = "JUGADOR 2" if self.modo_juego == MODO_DOS_JUGADORES else "LA IA"
            self.estado = ESTADO_GAME_OVER
        else:
            # El saque va hacia el jugador que NO anotó el punto
            self.iniciar_saque(hacia_derecha)

    # -----------------------------------------------------------------
    # ENTRADA DE TECLADO
    # -----------------------------------------------------------------
    def on_key_press(self, key, modifiers):
        # Estado de las teclas de movimiento (se usa en cualquier estado)
        if key == arcade.key.W:
            self.tecla_w = True
        elif key == arcade.key.S:
            self.tecla_s = True
        elif key == arcade.key.UP:
            self.tecla_arriba = True
        elif key == arcade.key.DOWN:
            self.tecla_abajo = True

        if self.estado == ESTADO_MENU:
            if key in (arcade.key.SPACE, arcade.key.ENTER, arcade.key.RETURN):
                self.iniciar_nueva_partida()
                self.estado = ESTADO_JUGANDO
            elif key == arcade.key.I:
                self.modo_juego = MODO_IA
            elif key == arcade.key.D:
                self.modo_juego = MODO_DOS_JUGADORES

        elif self.estado == ESTADO_JUGANDO:
            if key == arcade.key.P:
                self.estado = ESTADO_PAUSA

        elif self.estado == ESTADO_PAUSA:
            if key == arcade.key.P:
                self.estado = ESTADO_JUGANDO

        elif self.estado == ESTADO_GAME_OVER:
            if key in (arcade.key.SPACE, arcade.key.ENTER, arcade.key.RETURN):
                self.estado = ESTADO_MENU

        if key == arcade.key.ESCAPE:
            self.close()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.tecla_w = False
        elif key == arcade.key.S:
            self.tecla_s = False
        elif key == arcade.key.UP:
            self.tecla_arriba = False
        elif key == arcade.key.DOWN:
            self.tecla_abajo = False

    # -----------------------------------------------------------------
    # DIBUJADO
    # -----------------------------------------------------------------
    def on_draw(self):
        self.clear()

        if self.estado == ESTADO_MENU:
            self._dibujar_fondo()
            self._dibujar_red_central()
            self._dibujar_menu()

        elif self.estado == ESTADO_JUGANDO:
            self._dibujar_fondo()
            self._dibujar_juego()

        elif self.estado == ESTADO_PAUSA:
            self._dibujar_fondo()
            self._dibujar_juego()
            self._dibujar_pausa()

        elif self.estado == ESTADO_GAME_OVER:
            self._dibujar_fondo()
            self._dibujar_juego()
            self._dibujar_game_over()

    def _dibujar_fondo(self):
        """Líneas horizontales sutiles y bordes neón para reforzar la estética synthwave."""
        for i in range(6):
            y = 30 + i * 32
            arcade.draw_lbwh_rectangle_filled(0, y, ANCHO_PANTALLA, 1, COLOR_LINEA_FONDO)

        arcade.draw_lbwh_rectangle_filled(0, ALTO_PANTALLA - 3, ANCHO_PANTALLA, 3, COLOR_CYAN)
        arcade.draw_lbwh_rectangle_filled(0, 0, ANCHO_PANTALLA, 3, COLOR_MAGENTA)

    def _dibujar_red_central(self):
        """Dibuja la red divisoria como una línea punteada vertical."""
        alto_segmento = 18
        espacio = 12
        y = espacio
        while y < ALTO_PANTALLA:
            arcade.draw_lbwh_rectangle_filled(
                ANCHO_PANTALLA / 2 - 2, y, 4, alto_segmento, COLOR_RED_CENTRAL
            )
            y += alto_segmento + espacio

    def _dibujar_menu(self):
        # --- Título animado: pulso de tamaño y cambio de color ---
        onda = math.sin(self.tiempo_titulo * 3)
        tamano_titulo = int(60 + 6 * onda)
        color_titulo = COLOR_CYAN if onda > 0 else COLOR_MAGENTA

        arcade.draw_text(
            "PONG NEON", 0, ALTO_PANTALLA * 0.68, color_titulo, tamano_titulo,
            width=ANCHO_PANTALLA, align="center", bold=True
        )
        arcade.draw_text(
            "S Y N T H W A V E   E D I T I O N", 0, ALTO_PANTALLA * 0.68 - 46,
            COLOR_BLANCO, 16, width=ANCHO_PANTALLA, align="center"
        )

        arcade.draw_text(
            "Presiona ESPACIO o ENTER para iniciar",
            0, ALTO_PANTALLA * 0.44, COLOR_BLANCO, 22,
            width=ANCHO_PANTALLA, align="center", bold=True
        )

        texto_ia = "> [I] IA (Computadora) <" if self.modo_juego == MODO_IA else "[I] IA (Computadora)"
        texto_2j = "> [D] Dos Jugadores <" if self.modo_juego == MODO_DOS_JUGADORES else "[D] Dos Jugadores"
        arcade.draw_text(
            f"{texto_ia}      {texto_2j}",
            0, ALTO_PANTALLA * 0.33, COLOR_VERDE_NEON, 17,
            width=ANCHO_PANTALLA, align="center"
        )

        arcade.draw_text(
            "Jugador 1: W / S      Jugador 2: Flecha Arriba / Flecha Abajo",
            0, ALTO_PANTALLA * 0.20, COLOR_GRIS_NEON, 14,
            width=ANCHO_PANTALLA, align="center"
        )
        arcade.draw_text(
            f"Pausa: P      Primero en llegar a {PUNTOS_PARA_GANAR} puntos gana      Salir: ESC",
            0, ALTO_PANTALLA * 0.14, COLOR_GRIS_NEON, 14,
            width=ANCHO_PANTALLA, align="center"
        )

    def _dibujar_juego(self):
        self._dibujar_red_central()

        self.paleta_izquierda.dibujar()
        self.paleta_derecha.dibujar()

        for particula in self.particulas:
            particula.dibujar()

        self.pelota.dibujar()

        self._dibujar_marcador()

        if self.esperando_saque and self.estado == ESTADO_JUGANDO:
            arcade.draw_text(
                "Preparando saque...", 0, ALTO_PANTALLA / 2 + 46, COLOR_BLANCO, 16,
                width=ANCHO_PANTALLA, align="center"
            )

    def _dibujar_marcador(self):
        arcade.draw_text(
            str(self.puntos_izquierda), ANCHO_PANTALLA / 2 - 90, ALTO_PANTALLA - 78,
            COLOR_CYAN, 50, anchor_x="center", bold=True
        )
        arcade.draw_text(
            str(self.puntos_derecha), ANCHO_PANTALLA / 2 + 90, ALTO_PANTALLA - 78,
            COLOR_MAGENTA, 50, anchor_x="center", bold=True
        )

    def _dibujar_pausa(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, ANCHO_PANTALLA, ALTO_PANTALLA, (0, 0, 0, 165))
        arcade.draw_text(
            "PAUSA", 0, ALTO_PANTALLA / 2 + 15, COLOR_BLANCO, 46,
            width=ANCHO_PANTALLA, align="center", bold=True
        )
        arcade.draw_text(
            "Presiona P para continuar", 0, ALTO_PANTALLA / 2 - 30, COLOR_VERDE_NEON, 18,
            width=ANCHO_PANTALLA, align="center"
        )

    def _dibujar_game_over(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, ANCHO_PANTALLA, ALTO_PANTALLA, (0, 0, 0, 195))
        arcade.draw_text(
            "¡FIN DEL JUEGO!", 0, ALTO_PANTALLA / 2 + 75, COLOR_MAGENTA, 42,
            width=ANCHO_PANTALLA, align="center", bold=True
        )
        arcade.draw_text(
            f"GANADOR: {self.ganador}", 0, ALTO_PANTALLA / 2 + 18, COLOR_VERDE_NEON, 28,
            width=ANCHO_PANTALLA, align="center", bold=True
        )
        arcade.draw_text(
            f"{self.puntos_izquierda}  -  {self.puntos_derecha}", 0, ALTO_PANTALLA / 2 - 30,
            COLOR_BLANCO, 24, width=ANCHO_PANTALLA, align="center"
        )
        arcade.draw_text(
            "Presiona ESPACIO o ENTER para volver al menú",
            0, ALTO_PANTALLA / 2 - 85, COLOR_BLANCO, 16, width=ANCHO_PANTALLA, align="center"
        )


# =====================================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# =====================================================================
def main():
    """Crea la ventana del juego e inicia el bucle principal de arcade."""
    JuegoPong()
    arcade.run()


if __name__ == "__main__":
    main()