from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- DASHBOARD ALUMNO Y AUTENTICACIÓN ---
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='juego/login.html'), name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('cambiar-avatar/', views.cambiar_avatar, name='cambiar_avatar'),
    path('guardar-presupuesto/', views.guardar_presupuesto, name='guardar_presupuesto'),
    path('usar-tarjeta/<int:tarjeta_alumno_id>/', views.usar_tarjeta, name='usar_tarjeta'),
    path('responder-evento/<int:evento_alumno_id>/', views.responder_evento, name='responder_evento'),
    path('fondo/gestionar/', views.gestionar_fondo, name='gestionar_fondo'),
    path('solicitar-revision/<int:evento_alumno_id>/', views.solicitar_revision, name='solicitar_revision'),

    # --- PANEL DOCENTE Y GESTIÓN DE AULA ---
    path('profesor/', views.profesor_panel, name='profesor_panel'),
    path('profesor/alumno/<int:personaje_id>/', views.profesor_detalle_alumno, name='profesor_detalle_alumno'),
    path('profesor/alumno/<int:personaje_id>/cambiar-salario/', views.cambiar_salario_alumno, name='cambiar_salario_alumno'),
    path('profesor/crear-clase/', views.crear_clase, name='crear_clase'),
    path('profesor/crear-alumno/', views.crear_alumno, name='crear_alumno'),
    path('profesor/crear-alumnos-masivo/', views.crear_alumnos_masivo, name='crear_alumnos_masivo'),
    path('profesor/entregar-tarjeta/', views.entregar_tarjeta, name='entregar_tarjeta'),
    path('profesor/lanzar-evento/', views.lanzar_evento_clase, name='lanzar_evento_clase'),
    path('profesor/pagar-salarios/', views.pagar_salarios, name='pagar_salarios'),
    path('resolver-impugnacion/<int:evento_alumno_id>/', views.resolver_impugnacion, name='resolver_impugnacion'),
    path('clase/agregar-alumno/', views.agregar_alumno_a_clase, name='agregar_alumno_a_clase'),
    path('clase/quitar-alumno/<int:personaje_id>/', views.quitar_alumno_de_clase, name='quitar_alumno_de_clase'),

    # --- BANCO DE RECURSOS Y CREACIÓN DE MATERIALES ---
    path('profesor/repositorio/', views.banco_recursos, name='banco_recursos'),
    path('profesor/crear-tarjeta/', views.crear_tarjeta_personalizada, name='crear_tarjeta_personalizada'),
    path('profesor/crear-evento/', views.crear_evento_personalizado, name='crear_evento_personalizado'),
    path('profesor/tarjeta/<int:tarjeta_id>/editar/', views.editar_tarjeta, name='editar_tarjeta'),
    path('profesor/evento/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('profesor/tarjeta/<int:tarjeta_id>/eliminar/', views.eliminar_tarjeta, name='eliminar_tarjeta'),
    path('profesor/evento/<int:evento_id>/eliminar/', views.eliminar_evento, name='eliminar_evento'),

 # --- CARTAS Y TIENDA  ---
    path('tienda/', views.tienda_cartas, name='tienda_cartas'),
    path('tienda/comprar/<int:carta_id>/', views.comprar_carta, name='comprar_carta'),
    path('profesor/usar-carta/<int:carta_alumno_id>/', views.usar_carta_profesor, name='usar_carta_profesor'),
    path('tienda/cargar-defecto/<int:clase_id>/', views.cargar_cartas_defecto, name='cargar_cartas_defecto'),
    path('tienda/crear/', views.crear_carta, name='crear_carta'),
    path('tienda/editar/<int:carta_id>/', views.editar_carta, name='editar_carta'),
    path('tienda/eliminar/<int:carta_id>/', views.eliminar_carta, name='eliminar_carta'),

]


