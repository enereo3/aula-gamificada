import os
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from PIL import Image


AVATAR_CHOICES = [
    ('bi-robot', '🤖 Robot'),
    ('bi-rocket-takeoff', '🚀 Cohete'),
    ('bi-controller', '🎮 Gamer'),
    ('bi-emoji-smile', '😊 Sonrisa'),
    ('bi-briefcase', '💼 Ejecutivo'),
    ('bi-cpu', '💻 Techie'),
    ('bi-trophy', '🏆 Campeón'),
    ('bi-palette', '🎨 Artista'),
    ('bi-piggy-bank', '🐷 Ahorrador'),
]

NIVELES_GASTO = [
    ('BAJO', 'Económico'),
    ('MEDIO', 'Estándar'),
    ('ALTO', 'Confort / Premium'),
]
# NIVELES DE SALARIO SEGÚN RENDIMIENTO / COMPORTAMIENTO
NIVELES_SALARIO = [
    ('75.00', 'Nivel 1: Penalización Alta (75 €/sem)'),
    ('125.00', 'Nivel 2: Penalización Leve (125 €/sem)'),
    ('150.00', 'Nivel 3: Sueldo Base Estándar (150 €/sem)'),
    ('175.00', 'Nivel 4: Ascenso 1 - Buen Trabajo (175 €/sem)'),
    ('300.00', 'Nivel 5: Ascenso 2 - Puesto de Excelencia (300 €/sem)'),
]
# CONFIGURACIÓN ACTUALIZADA CON TUS NUEVOS VALORES
CONFIG_PRESUPUESTO = {
    'comida': {
        'BAJO': {'coste': Decimal('25.00'), 'salud': -15, 'felicidad': -10, 'nombre': 'Comida ultra-procesada'},
        'MEDIO': {'coste': Decimal('50.00'), 'salud': 5, 'felicidad': 5, 'nombre': 'Dieta equilibrada básica'},
        'ALTO': {'coste': Decimal('80.00'), 'salud': 10, 'felicidad': 10, 'nombre': 'Comida de alta calidad u orgánica'},
    },
    'vivienda': {
        'BAJO': {'coste': Decimal('20.00'), 'salud': -20, 'felicidad': -30, 'nombre': 'Ahorro extremo en luz/calefacción'},
        'MEDIO': {'coste': Decimal('45.00'), 'salud': 0, 'felicidad': -5, 'nombre': 'Uso responsable de suministros'},
        'ALTO': {'coste': Decimal('85.00'), 'salud': 10, 'felicidad': 5, 'nombre': 'Climatización total y confort'},
    },
    'transporte': {
        'BAJO': {'coste': Decimal('5.00'), 'salud': 5, 'felicidad': -5, 'nombre': 'Caminando o bici'},
        'MEDIO': {'coste': Decimal('25.00'), 'salud': -10, 'felicidad': -5, 'nombre': 'Abono de transporte público'},
        'ALTO': {'coste': Decimal('55.00'), 'salud': -5, 'felicidad': 10, 'nombre': 'Vehículo propio / Taxi'},
    },
    'ocio': {
        'BAJO': {'coste': Decimal('0.00'), 'salud': -5, 'felicidad': -15, 'nombre': 'Sin salidas ni ocio'},
        'MEDIO': {'coste': Decimal('40.00'), 'salud': 5, 'felicidad': 10, 'nombre': 'Ocio equilibrado'},
        'ALTO': {'coste': Decimal('60.00'), 'salud': 5, 'felicidad': 15, 'nombre': 'Ocio VIP y eventos'},
    }
}

TASA_INTERES_FONDO = Decimal('0.02')  # 2% de rentabilidad semanal

# OPCIONES PARA CLASIFICACIÓN DE MATERIALES
CURSO_CHOICES = [
    ('1_ESO', '1º ESO'),
    ('2_ESO', '2º ESO'),
    ('3_ESO', '3º ESO'),
    ('4_ESO', '4º ESO'),
    ('BACH', 'Bachillerato'),
    ('GENERAL', 'General / Todos'),
]

DIFICULTAD_CHOICES = [
    ('FACIL', 'Fácil'),
    ('MEDIO', 'Medio'),
    ('DIFICIL', 'Difícil'),
]

TIPO_RESPUESTA_CHOICES = [
    ('NUMERICA', 'Numérica (Autocorregible)'),
    ('TEXTO', 'Texto / Respuesta Abierta (Requiere revisión)'),
    ('TEST', 'Opción Múltiple / Test (Autocorregible)'),
]


class Clase(models.Model):
    nombre = models.CharField(max_length=100)
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clases_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    class Meta:
        # Un profesor no puede repetir el nombre de una clase
        unique_together = ('nombre', 'profesor')
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'

    def __str__(self):
        return f"{self.nombre} ({self.profesor.username})"


class Personaje(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personaje')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='alumnos', null=True, blank=True)
    
    avatar = models.CharField(max_length=50, choices=AVATAR_CHOICES, default='bi-robot')
    salud = models.IntegerField(default=100)
    felicidad = models.IntegerField(default=100)
    dinero_disponible = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    fondo_emergencia = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    salario_semanal = models.DecimalField(max_digits=10, decimal_places=2, default=150.00)

    dinero_anterior = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    salud_anterior = models.IntegerField(default=100)
    felicidad_anterior = models.IntegerField(default=100)

    nivel_comida = models.CharField(max_length=10, choices=NIVELES_GASTO, default='MEDIO')
    nivel_vivienda = models.CharField(max_length=10, choices=NIVELES_GASTO, default='MEDIO')
    nivel_transporte = models.CharField(max_length=10, choices=NIVELES_GASTO, default='MEDIO')
    nivel_ocio = models.CharField(max_length=10, choices=NIVELES_GASTO, default='MEDIO')

    def __str__(self):
        nombre_completo = self.usuario.get_full_name() or self.usuario.username
        return f"{nombre_completo} | Saldo: {self.dinero_disponible}€ | Fondo: {self.fondo_emergencia}€"

    @property
    def patrimonio_total(self):
        return self.dinero_disponible + self.fondo_emergencia

    @property
    def var_dinero(self):
        return self.patrimonio_total - self.dinero_anterior

    @property
    def var_salud(self):
        return self.salud - self.salud_anterior

    @property
    def var_felicidad(self):
        return self.felicidad - self.felicidad_anterior

    def calcular_interes_estimado(self):
        """Calcula el rendimiento estimado del 2% semanal sobre el Fondo de Emergencia"""
        return (self.fondo_emergencia * TASA_INTERES_FONDO).quantize(Decimal('0.01'))

    def obtener_coste_presupuesto(self):
        return (CONFIG_PRESUPUESTO['comida'][self.nivel_comida]['coste'] +
                CONFIG_PRESUPUESTO['vivienda'][self.nivel_vivienda]['coste'] +
                CONFIG_PRESUPUESTO['transporte'][self.nivel_transporte]['coste'] +
                CONFIG_PRESUPUESTO['ocio'][self.nivel_ocio]['coste'])

    def obtener_impacto_salud(self):
        return (CONFIG_PRESUPUESTO['comida'][self.nivel_comida]['salud'] +
                CONFIG_PRESUPUESTO['vivienda'][self.nivel_vivienda]['salud'] +
                CONFIG_PRESUPUESTO['transporte'][self.nivel_transporte]['salud'] +
                CONFIG_PRESUPUESTO['ocio'][self.nivel_ocio]['salud'])

    def obtener_impacto_felicidad(self):
        return (CONFIG_PRESUPUESTO['comida'][self.nivel_comida]['felicidad'] +
                CONFIG_PRESUPUESTO['vivienda'][self.nivel_vivienda]['felicidad'] +
                CONFIG_PRESUPUESTO['transporte'][self.nivel_transporte]['felicidad'] +
                CONFIG_PRESUPUESTO['ocio'][self.nivel_ocio]['felicidad'])


class Tarjeta(models.Model):
    TIPO_CHOICES = [
        ('TRABAJO', '💼 Trabajo Extra / Esfuerzo'),
        ('EXCELENCIA', '🌟 Premio a la Excelencia Académica'),
        ('PARTICIPACION', '🙋‍♂️ Participación Activa en Clase'),
        ('AHORRO', '🐖 Incentivo de Ahorro'),
        ('SEGURO', '🛡️ Seguro / Mitigador de Imprevistos'),
        ('BONO', '📈 Bono Financiero / Inversión'),
        ('BECA', '🎓 Beca o Ayuda Escolar'),
        ('COMODIN', '🃏 Comodín / Especial'),
    ]
    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tarjetas_creadas')
    es_publica = models.BooleanField(default=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='TRABAJO')
    
    efecto_dinero = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    efecto_salud = models.IntegerField(default=0)
    efecto_felicidad = models.IntegerField(default=0)

    curso = models.CharField(max_length=20, choices=CURSO_CHOICES, default='1_ESO')
    dificultad = models.CharField(max_length=20, choices=DIFICULTAD_CHOICES, default='MEDIO')
    temario = models.CharField(max_length=100, default='General', help_text="Ej: Porcentajes, Ahorro, Presupuesto")

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class TarjetaAlumno(models.Model):
    personaje = models.ForeignKey(Personaje, on_delete=models.CASCADE, related_name='tarjetas')
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.CASCADE)
    usada = models.BooleanField(default=False)
    fecha_obtenida = models.DateTimeField(auto_now_add=True)


class EventoAleatorio(models.Model):
    TIPO_RETO_CHOICES = [
        ('IMPREVISTO', '⚡ Imprevisto Financiero (Penalización mitigable)'),
        ('ACTIVIDAD', '📚 Actividad / Tarea de Clase (Recompensa al acertar)'),
        ('OPERACIONES', '🔢 Operaciones Combinadas / Problema Matemático'),
        ('FINANZAS', '💡 Caso Práctico de Economía y Finanzas'),
    ]

    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_creados')
    es_publico = models.BooleanField(default=True)
    tipo_reto = models.CharField(max_length=20, choices=TIPO_RETO_CHOICES, default='IMPREVISTO')
    titulo = models.CharField(max_length=150, blank=True, default="")
    descripcion = models.TextField(blank=True, default="")
    imagen = models.ImageField(upload_to='retos/', null=True, blank=True)
    def save(self, *args, **kwargs):
            # 1. Guardar la imagen original primero
            super().save(*args, **kwargs)
            # 2. Si hay imagen, redimensionarla y optimizarla
            if self.imagen and os.path.exists(self.imagen.path):
                try:
                    img = Image.open(self.imagen.path)

                    # Convertir transparencias PNG a RGB para guardar en JPG/PNG optimizado
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Redimensionar solo si supera los 1000px de ancho o alto
                    max_size = (1000, 1000)
                    if img.height > max_size[1] or img.width > max_size[0]:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        img.save(self.imagen.path, quality=80, optimize=True)

                except Exception as e:
                    # Si el archivo subido está dañado o falla Pillow, la aplicación
                    # no se rompe y el reto se guarda sin problemas.
                    print(f"Aviso: No se pudo optimizar la imagen del reto: {e}")

    curso = models.CharField(max_length=20, choices=CURSO_CHOICES, default='1_ESO')
    dificultad = models.CharField(max_length=20, choices=DIFICULTAD_CHOICES, default='MEDIO')
    temario = models.CharField(max_length=100, default='General', help_text="Ej: Ecuaciones, Regla de 3, Consumo Responsable")
    tipo_respuesta = models.CharField(max_length=20, choices=TIPO_RESPUESTA_CHOICES, default='NUMERICA')
    opciones_test = models.TextField(blank=True, null=True, help_text="Opciones separadas por coma si es tipo TEST. Ej: 10, 20, 30")
    pregunta_matematica = models.CharField(max_length=255, blank=True, default="")
    respuesta_correcta = models.CharField(max_length=100, blank=True, null=True)    

    
    penalizacion_dinero = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    penalizacion_salud = models.IntegerField(default=0)
    penalizacion_felicidad = models.IntegerField(default=0)
    porcentaje_mitigacion = models.IntegerField(default=50)

    recompensa_dinero = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    recompensa_salud = models.IntegerField(default=0)
    recompensa_felicidad = models.IntegerField(default=0)

    
    def __str__(self):
        return f"[{self.get_curso_display()} - {self.temario}] {self.pregunta_matematica}"


class EventoAlumno(models.Model):
    personaje = models.ForeignKey(Personaje, on_delete=models.CASCADE, related_name='eventos_pendientes')
    evento = models.ForeignKey(EventoAleatorio, on_delete=models.CASCADE)
    resuelto = models.BooleanField(default=False)
    exito_reto = models.BooleanField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    titulo_narrativo = models.CharField(max_length=150, blank=True, default="")
    descripcion_narrativa = models.TextField(blank=True, default="")
    respuesta_alumno = models.CharField(max_length=255, blank=True, default="")
    pendiente_revision = models.BooleanField(default=False)
    mitigado = models.BooleanField(default=False)
    respuesta_enviada = models.CharField(max_length=255, blank=True, null=True)
    estado_revision = models.CharField(
        max_length=20,
        choices=[
            ('NONE', 'Sin Solicitud'),
            ('PENDIENTE', 'Pendiente de Revisión'),
            ('APROBADO', 'Aceptado por Profesor'),
            ('RECHAZADO', 'Rechazado'),
        ],
        default='NONE'
    )
    motivo_impugnacion = models.TextField(blank=True, null=True)

    @property
    def lista_opciones(self):
        """Devuelve las opciones del test como una lista limpia sin espacios extras."""
        if self.opciones_test:
            return [opc.strip() for opc in self.opciones_test.split(',') if opc.strip()]
        return []

    def __str__(self):
        return f"[{self.get_curso_display()} - {self.temario}] {self.pregunta_matematica}"


class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso / Salario / Rentabilidad'),
        ('GASTO', 'Gasto / Penalización / Traspaso'),
        ('TARJETA', 'Uso de Tarjeta'),
        ('RETO', 'Recompensa por Reto / Actividad'),
    ]
    personaje = models.ForeignKey(Personaje, on_delete=models.CASCADE, related_name='transacciones')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    concepto = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    explicacion_operacion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)


class SituacionNarrativa(models.Model):
    """Banco de contexto cotidiano e imprevistos para envolver los retos."""
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(help_text="Texto narrativo sin incluir el problema matemático.")

    def __str__(self):
        return self.titulo

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import math

class CartaTienda(models.Model):
    clase = models.ForeignKey('Clase', on_delete=models.CASCADE, related_name='cartas_tienda')
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(help_text="Beneficio de la carta en el aula")
    precio_base = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('10.00'))
    
    # Control de Stock
    stock_total = models.PositiveIntegerField(default=3, help_text="Número máximo de cartas en circulación")
    stock_disponible = models.PositiveIntegerField(default=3, help_text="Stock actual en tienda")
    
    # Factor de incremento de precio por uso (ej: 5.00€ extra de base al ser devuelta)
    incremento_por_uso = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5.00'))

    def __str__(self):
        return f"{self.titulo} - {self.clase.nombre}"

    @property
    def precio_actual(self):
        """
        Calcula el precio dinámico según la escasez:
        Si queda poco stock, el precio se multiplica exponencialmente.
        Ejemplo: 3 de stock => Precio base | 2 de stock => Base x 2 | 1 de stock => Base x 6
        """
        if self.stock_disponible == 0:
            return self.precio_base * Decimal('10.00')

        compradas = self.stock_total - self.stock_disponible
        if compradas <= 0:
            return self.precio_base
        
        # Factor multiplicador exponencial según unidades compradas
        multiplicador = Decimal(math.factorial(compradas + 1))
        return (self.precio_base * multiplicador).quantize(Decimal('0.01'))


class CartaAlumno(models.Model):
    ESTADOS = [
        ('ACTIVA', 'En inventario'),
        ('USADA', 'Usada y devuelta a tienda'),
    ]

    personaje = models.ForeignKey('Personaje', on_delete=models.CASCADE, related_name='cartas_compradas')
    carta = models.ForeignKey(CartaTienda, on_delete=models.CASCADE, related_name='historial_compras')
    precio_pagado = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVA')
    fecha_compra = models.DateTimeField(auto_now_add=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.carta.titulo} - {self.personaje.usuario.username} ({self.estado})"