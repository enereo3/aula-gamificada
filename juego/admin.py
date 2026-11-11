from django.contrib import admin
from .models import (
    Personaje, 
    Tarjeta, 
    TarjetaAlumno, 
    EventoAleatorio, 
    Transaccion, 
    EventoAlumno, 
    SituacionNarrativa,
    Clase
)

@admin.register(Personaje)
class PersonajeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'dinero_disponible', 'salud', 'felicidad', 'salario_semanal')
    search_fields = ('usuario__username',)

@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'curso', 'dificultad', 'temario', 'efecto_dinero', 'efecto_salud', 'efecto_felicidad')
    list_filter = ('curso', 'dificultad')
    search_fields = ('nombre', 'temario')

@admin.register(TarjetaAlumno)
class TarjetaAlumnoAdmin(admin.ModelAdmin):
    list_display = ('personaje', 'tarjeta', 'usada', 'fecha_obtenida')
    list_filter = ('usada',)

@admin.register(EventoAleatorio)
class EventoAleatorioAdmin(admin.ModelAdmin):
    list_display = ('id', 'curso', 'dificultad', 'temario', 'tipo_respuesta', 'pregunta_matematica', 'penalizacion_dinero')
    list_filter = ('curso', 'dificultad', 'tipo_respuesta')
    search_fields = ('temario', 'pregunta_matematica')

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('personaje', 'monto', 'concepto', 'tipo', 'fecha')
    list_filter = ('tipo', 'fecha')

@admin.register(EventoAlumno)
class EventoAlumnoAdmin(admin.ModelAdmin):
    list_display = ('personaje', 'evento', 'resuelto', 'exito_reto', 'fecha')
    list_filter = ('resuelto', 'exito_reto', 'estado_revision')  # Añadimos estado_revision si quieres filtrar reclamos
    search_fields = ('personaje__usuario__username', 'evento__temario')

@admin.register(SituacionNarrativa)
class SituacionNarrativaAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'descripcion')
    search_fields = ('titulo', 'descripcion')

@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'profesor', 'fecha_creacion')
    search_fields = ('nombre', 'profesor__username')
