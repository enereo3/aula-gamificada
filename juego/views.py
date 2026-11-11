import random
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from .models import (
    Personaje, Tarjeta, TarjetaAlumno, EventoAleatorio, EventoAlumno, 
    Transaccion, Clase, AVATAR_CHOICES, CONFIG_PRESUPUESTO, TASA_INTERES_FONDO, SituacionNarrativa, CartaTienda, CartaAlumno
)


# ==========================================
# 1. VISTAS DEL ALUMNO Y DASHBOARD
# ==========================================

@login_required
def dashboard(request):
    """Panel principal del alumno o previsualización demo para docentes."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    
    if es_profesor and request.GET.get('demo') != '1':
        return redirect('profesor_panel')

    narrativas_disponibles = list(SituacionNarrativa.objects.all())

    # --- MODO DEMOSTRACIÓN DOCENTE ---
    if es_profesor and request.GET.get('demo') == '1':
        personaje_demo = Personaje(
            usuario=request.user,
            avatar='bi-briefcase',
            salud=92,
            felicidad=88,
            dinero_disponible=Decimal('175.50'),
            fondo_emergencia=Decimal('50.00'),
            salario_semanal=Decimal('150.00'),
            nivel_comida='MEDIO',
            nivel_vivienda='ALTO',
            nivel_transporte='MEDIO',
            nivel_ocio='BAJO'
        )
        
        narrativa_demo = random.choice(narrativas_disponibles) if narrativas_disponibles else None
        eventos_demo = []
        if narrativa_demo:
            eventos_demo = [{
                'id': 0,
                'titulo_narrativo': narrativa_demo.titulo,
                'descripcion_narrativa': narrativa_demo.descripcion,
                'evento': {
                    'pregunta_matematica': '¿Cuál es el 15% de 200 €?',
                    'tipo_respuesta': 'NUMERICA',
                    'opciones_test': '',
                    'penalizacion_dinero': Decimal('30.00'),
                    'porcentaje_mitigacion': 50,
                }
            }]

        contexto = {
            'es_demo': True,
            'personaje': personaje_demo,
            'tarjetas_alumno': [],
            'eventos_pendientes': eventos_demo,
            'transacciones': [
                {'fecha': 'Hoy 10:30', 'concepto': 'Nómina Semanal', 'monto': Decimal('150.00'), 'explicacion_operacion': 'Ingreso base semanal'},
                {'fecha': 'Ayer 18:00', 'concepto': 'Cobro Gastos Fijos', 'monto': Decimal('-95.00'), 'explicacion_operacion': 'Presupuesto elegido'},
            ],
            'avatares': AVATAR_CHOICES,
            'config_presupuesto': CONFIG_PRESUPUESTO,
            'coste_actual': Decimal('95.00'),
            'impacto_salud': 4,
            'impacto_felicidad': -5,
            'tiene_seguro_disponible': False,
        }
        return render(request, 'juego/dashboard.html', contexto)

    # --- MODO ALUMNO REAL ---
    personaje, created = Personaje.objects.get_or_create(
        usuario=request.user,
        defaults={'salud': 100, 'felicidad': 100, 'dinero_disponible': Decimal('100.00')}
    )
    
    tarjetas_alumno = TarjetaAlumno.objects.filter(personaje=personaje, usada=False)
    eventos_pendientes = EventoAlumno.objects.filter(personaje=personaje, resuelto=False)
    transacciones = Transaccion.objects.filter(personaje=personaje).order_by('-fecha')[:10]
    tiene_seguro_disponible = tarjetas_alumno.filter(tarjeta__tipo='SEGURO').exists()
    retos_resueltos = EventoAlumno.objects.filter(personaje=personaje, resuelto=True).order_by('-fecha')

    # Asignar narrativa aleatoria temporal en caso de que el reto no la tuviera guardada
    for ep in eventos_pendientes:
        if not ep.titulo_narrativo:
            situacion = random.choice(narrativas_disponibles) if narrativas_disponibles else None
            if situacion:
                ep.titulo_narrativo = situacion.titulo
                ep.descripcion_narrativa = situacion.descripcion
            else:
                ep.titulo_narrativo = "Imprevisto Económico"
                ep.descripcion_narrativa = "Te ha surgido un gasto inesperado en tu día a día."

    contexto = {
        'es_demo': False,
        'personaje': personaje,
        'tarjetas_alumno': tarjetas_alumno,
        'eventos_pendientes': eventos_pendientes,
        'transacciones': transacciones,
        'avatares': AVATAR_CHOICES,
        'config_presupuesto': CONFIG_PRESUPUESTO,
        'coste_actual': personaje.obtener_coste_presupuesto(),
        'impacto_salud': personaje.obtener_impacto_salud(),
        'impacto_felicidad': personaje.obtener_impacto_felicidad(),
        'tiene_seguro_disponible': tiene_seguro_disponible,
        'retos_resueltos': retos_resueltos,
    }
    
    return render(request, 'juego/dashboard.html', contexto)


@login_required
def guardar_presupuesto(request):
    if request.method == 'POST':
        if request.user.is_staff or Clase.objects.filter(profesor=request.user).exists():
            messages.info(request, "Modo Demostración: Los cambios de presupuesto no se guardan en el perfil docente.")
            return redirect('/?demo=1')

        personaje = get_object_or_404(Personaje, usuario=request.user)
        personaje.nivel_comida = request.POST.get('comida', 'MEDIO')
        personaje.nivel_vivienda = request.POST.get('vivienda', 'MEDIO')
        personaje.nivel_transporte = request.POST.get('transporte', 'MEDIO')
        personaje.nivel_ocio = request.POST.get('ocio', 'MEDIO')
        personaje.save()
        
        messages.success(request, f"¡Presupuesto semanal actualizado! Coste estimado: {personaje.obtener_coste_presupuesto()}€")
    return redirect('dashboard')


@login_required
def cambiar_avatar(request):
    if request.method == 'POST' and hasattr(request.user, 'personaje'):
        nuevo_avatar = request.POST.get('avatar')
        personaje = request.user.personaje
        personaje.avatar = nuevo_avatar
        personaje.save()
        messages.success(request, "¡Avatar actualizado correctamente!")
    return redirect('dashboard')


@login_required
def usar_tarjeta(request, tarjeta_alumno_id):
    tarjeta_alumno = get_object_or_404(TarjetaAlumno, id=tarjeta_alumno_id, personaje__usuario=request.user)

    if tarjeta_alumno.usada:
        messages.error(request, "Esta tarjeta ya ha sido utilizada.")
        return redirect('dashboard')

    personaje = tarjeta_alumno.personaje
    tarjeta = tarjeta_alumno.tarjeta

    personaje.dinero_disponible += tarjeta.efecto_dinero
    personaje.salud = min(100, max(0, personaje.salud + tarjeta.efecto_salud))
    personaje.felicidad = min(100, max(0, personaje.felicidad + tarjeta.efecto_felicidad))
    personaje.save()

    tarjeta_alumno.usada = True
    tarjeta_alumno.save()

    explicacion = (
        f"Tarjeta activada: '{tarjeta.nombre}'. "
        f"Impacto: {tarjeta.efecto_dinero:+}€ | {tarjeta.efecto_salud:+} Salud | {tarjeta.efecto_felicidad:+} Felicidad."
    )
    Transaccion.objects.create(
        personaje=personaje,
        monto=tarjeta.efecto_dinero,
        concepto=f"Uso de Tarjeta: {tarjeta.nombre}",
        tipo='TARJETA',
        explicacion_operacion=explicacion
    )

    messages.success(request, f"¡Has activado la tarjeta '{tarjeta.nombre}' con éxito!")
    return redirect('dashboard')


@login_required
def responder_evento(request, evento_alumno_id):
    """Evalúa la respuesta del alumno, aplica mitigación si acierta o penalización completa si falla."""
    evento_alumno = get_object_or_404(EventoAlumno, id=evento_alumno_id, personaje__usuario=request.user)
    
    if request.method == 'POST':
        respuesta_usuario = request.POST.get('respuesta_alumno', '').strip()
        evento_alumno.respuesta_alumno = respuesta_usuario        
        reto = evento_alumno.evento
        tipo = reto.tipo_respuesta
        es_correcta = False

        if tipo == 'NUMERICA':
            try:
                val_usuario = float(respuesta_usuario.replace(',', '.'))
                val_correcto = float(reto.respuesta_correcta.replace(',', '.'))
                es_correcta = abs(val_usuario - val_correcto) < 0.01
            except (ValueError, AttributeError):
                es_correcta = False
            evento_alumno.resuelto = True
        elif tipo == 'TEST':
            if reto.respuesta_correcta:
                es_correcta = (respuesta_usuario.lower() == reto.respuesta_correcta.strip().lower())
            else:
                es_correcta = False
            evento_alumno.resuelto = True
        elif tipo == 'TEXTO':
            evento_alumno.pendiente_revision = True
            evento_alumno.save()
            messages.info(request, "Tu propuesta ha sido enviada. El profesor la revisará en breve.")
            return redirect('dashboard')

        evento_alumno.exito_reto = es_correcta

        # CALCULAR PENALIZACIÓN CON MITIGACIÓN
        factor_multa = Decimal('1.0')
        if es_correcta:
            mitigacion = Decimal(reto.porcentaje_mitigacion) / Decimal('100')
            factor_multa = Decimal('1.0') - mitigacion
            evento_alumno.mitigado = True
            messages.success(request, f"¡Respuesta correcta! Has mitigado el imprevisto en un {reto.porcentaje_mitigacion}%.")
        else:
            evento_alumno.mitigado = False
            messages.error(request, "Respuesta incorrecta. Se ha aplicado la penalización completa.")

        # APLICAR IMPACTO EN EL PERSONAJE
        pen_dinero = reto.penalizacion_dinero * factor_multa
        pen_salud = int(reto.penalizacion_salud * float(factor_multa))
        pen_felicidad = int(reto.penalizacion_felicidad * float(factor_multa))

        personaje = evento_alumno.personaje
        personaje.dinero_disponible -= pen_dinero
        personaje.salud = max(0, personaje.salud - pen_salud)
        personaje.felicidad = max(0, personaje.felicidad - pen_felicidad)
        personaje.save()

        # REGISTRAR TRANSACCIÓN
        Transaccion.objects.create(
            personaje=personaje,
            concepto=f"Imprevisto: {evento_alumno.titulo_narrativo or reto.temario}",
            monto=-pen_dinero,
            tipo='GASTO',
            explicacion_operacion=f"Penalización {'Mitigada' if es_correcta else 'Completa'}"
        )

        evento_alumno.save()

    return redirect('dashboard')



@login_required
def gestionar_fondo(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        try:
            monto = Decimal(request.POST.get('monto', '0')).quantize(Decimal('0.01'))
        except (ValueError, TypeError):
            messages.error(request, "Importe no válido.")
            return redirect('dashboard')

        if monto <= Decimal('0.00'):
            messages.error(request, "El importe debe ser mayor a 0,00 €.")
            return redirect('dashboard')

        personaje = get_object_or_404(Personaje, usuario=request.user)

        if accion == 'depositar':
            if personaje.dinero_disponible < monto:
                messages.error(request, "No tienes suficiente saldo disponible en tu Cuenta Corriente.")
            else:
                personaje.dinero_disponible -= monto
                personaje.fondo_emergencia += monto
                personaje.save()

                Transaccion.objects.create(
                    personaje=personaje,
                    monto=-monto,
                    concepto="Depósito en Fondo de Emergencia",
                    tipo='GASTO',
                    explicacion_operacion=f"Traspaso de {monto}€ al Fondo de Emergencia (+2% semanal)."
                )
                messages.success(request, f"¡Has ingresado {monto}€ en tu Fondo de Emergencia!")

        elif accion == 'retirar':
            if personaje.fondo_emergencia < monto:
                messages.error(request, "No dispones de tanto dinero en tu Fondo de Emergencia.")
            else:
                personaje.fondo_emergencia -= monto
                personaje.dinero_disponible += monto
                personaje.save()

                Transaccion.objects.create(
                    personaje=personaje,
                    monto=monto,
                    concepto="Retirada del Fondo de Emergencia",
                    tipo='INGRESO',
                    explicacion_operacion=f"Traspaso de {monto}€ a la Cuenta Corriente."
                )
                messages.success(request, f"Has retirado {monto}€ a tu Cuenta Corriente.")

    return redirect('dashboard')



@login_required
def solicitar_revision(request, evento_alumno_id):
    """El alumno solicita que el profesor revise su respuesta."""
    evento_alumno = get_object_or_404(EventoAlumno, id=evento_alumno_id, personaje__usuario=request.user)
    if request.method == 'POST' and not evento_alumno.exito_reto:
        evento_alumno.motivo_impugnacion = request.POST.get('motivo', 'El alumno considera válida su respuesta.')
        evento_alumno.estado_revision = 'PENDIENTE'
        evento_alumno.save()
        messages.info(request, "Solicitud de revisión enviada al profesor.")
    return redirect('dashboard')



def cerrar_sesion(request):
    logout(request)
    return redirect('login')


# ==========================================
# 2. PANEL Y FUNCIONES DEL DOCENTE
# ==========================================

@login_required
def profesor_panel(request):
    """Panel de gestión en el aula con filtrado estricto de materiales."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('dashboard')
    # 1. Obtener todas las clases del profesor
    clases = Clase.objects.filter(profesor=request.user).order_by('nombre')

    # 2. Determinar la clase activa (por URL o la primera de la lista)
    clase_id = request.GET.get('clase_id')
    clase_seleccionada = None
    if clase_id:
        clase_seleccionada = clases.filter(id=clase_id).first()
    
    if not clase_seleccionada and clases.exists():
        clase_seleccionada = clases.first()

    # 3. Filtrar los alumnos pertenecientes ÚNICAMENTE a la clase activa
    if clase_seleccionada:
        personajes = Personaje.objects.filter(clase=clase_seleccionada).select_related('usuario')
        revisiones_pendientes = EventoAlumno.objects.filter(
            estado_revision='PENDIENTE',
            personaje__clase=clase_seleccionada
        ).select_related('personaje__usuario', 'evento')
    else:
        personajes = Personaje.objects.none()
        revisiones_pendientes = EventoAlumno.objects.none()

    # 4. Alumnos registrados sin clase (para poder añadirlos a la clase activa)
    alumnos_disponibles = Personaje.objects.filter(clase__isnull=True).select_related('usuario')

    f_curso = request.GET.get('curso', '').strip()
    f_dificultad = request.GET.get('dificultad', '').strip()
    f_temario = request.GET.get('temario', '').strip()

    tarjetas = Tarjeta.objects.all()
    eventos = EventoAleatorio.objects.all()
    revisiones_pendientes = EventoAlumno.objects.filter(
        estado_revision='PENDIENTE',
        personaje__clase__profesor=request.user
    )

    if f_curso:
        tarjetas = tarjetas.filter(curso=f_curso)
        eventos = eventos.filter(curso=f_curso)

    if f_dificultad:
        tarjetas = tarjetas.filter(dificultad=f_dificultad)
        eventos = eventos.filter(dificultad=f_dificultad)

    if f_temario:
        tarjetas = tarjetas.filter(temario__icontains=f_temario)
        eventos = eventos.filter(temario__icontains=f_temario)



    context = {
        'personajes': personajes,
        'clases': clases,
        'clase_seleccionada': clase_seleccionada,
        'tarjetas': tarjetas,
        'alumnos_disponibles': alumnos_disponibles,
        'eventos': eventos,
        'revisiones_pendientes': revisiones_pendientes,
        'f_curso': f_curso,
        'f_dificultad': f_dificultad,
        'f_temario': f_temario,
    }
    return render(request, 'juego/profesor_panel.html', context)


@login_required
def profesor_detalle_alumno(request, personaje_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, clase__profesor=request.user)
    transacciones = Transaccion.objects.filter(personaje=personaje).order_by('-fecha')
    retos_enfrentados = EventoAlumno.objects.filter(personaje=personaje).order_by('-fecha')
    tarjetas_conseguidas = TarjetaAlumno.objects.filter(personaje=personaje).order_by('-fecha_obtenida')

    total_retos = retos_enfrentados.filter(resuelto=True).count()
    retos_exitosos = retos_enfrentados.filter(resuelto=True, exito_reto=True).count()
    porcentaje_acierto = int((retos_exitosos / total_retos) * 100) if total_retos > 0 else 0

    return render(request, 'juego/profesor_detalle_alumno.html', {
        'personaje': personaje,
        'transacciones': transacciones,
        'retos_enfrentados': retos_enfrentados,
        'tarjetas_conseguidas': tarjetas_conseguidas,
        'total_retos': total_retos,
        'retos_exitosos': retos_exitosos,
        'porcentaje_acierto': porcentaje_acierto,
        'config_presupuesto': CONFIG_PRESUPUESTO
    })


@login_required
def crear_clase(request):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        nombre_clase = request.POST.get('nombre_clase', '').strip()
        clase_id = request.POST.get('clase_id')
        
        if not nombre_clase:
            messages.error(request, "El nombre de la clase no puede estar vacío.")
            return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")

        # Comprobar si ya existe una clase con ese nombre para este profesor
        if Clase.objects.filter(nombre__iexact=nombre_clase, profesor=request.user).exists():
            messages.error(request, f"Ya tienes una clase registrada con el nombre '{nombre_clase}'.")
            return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")

        Clase.objects.create(nombre=nombre_clase, profesor=request.user)
        messages.success(request, f"Clase '{nombre_clase}' creada correctamente.")

    return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")



@login_required
def crear_alumno(request):
    if request.method == 'POST':
        nombre = request.POST.get('first_name', '').strip()
        apellidos = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        clase_id = request.POST.get('clase_id')
        
        clase = get_object_or_404(Clase, id=clase_id, profesor=request.user)

        if User.objects.filter(username=username).exists():
            messages.error(request, f"El usuario '{username}' ya existe.")
        else:
            nuevo_usuario = User.objects.create_user(
                username=username,
                password=password,
                first_name=nombre,
                last_name=apellidos,
                email=email
            )
            Personaje.objects.create(usuario=nuevo_usuario, clase=clase)
            messages.success(request, f"Alumno '{nombre} {apellidos}' inscrito.")

    return redirect('profesor_panel')


@login_required
def crear_alumnos_masivo(request):
    if request.method == 'POST':
        clase_id = request.POST.get('clase_id')
        clase = get_object_or_404(Clase, id=clase_id, profesor=request.user)
        
        datos_texto = request.POST.get('datos_masivos', '').strip()
        archivo_csv = request.FILES.get('archivo_csv')
        
        lineas = []
        if archivo_csv:
            contenido = archivo_csv.read().decode('utf-8')
            lineas = contenido.splitlines()
        elif datos_texto:
            lineas = datos_texto.splitlines()

        creados = 0
        errores = 0

        for linea in lineas:
            partes = [p.strip() for p in linea.split(';') if p.strip()]
            if len(partes) >= 5:
                nombre, apellidos, email, username, password = partes[:5]
                if not User.objects.filter(username=username).exists():
                    u = User.objects.create_user(
                        username=username, password=password,
                        first_name=nombre, last_name=apellidos, email=email
                    )
                    Personaje.objects.create(usuario=u, clase=clase)
                    creados += 1
                else:
                    errores += 1

        messages.success(request, f"Se crearon {creados} alumnos en {clase.nombre}.")

    return redirect('profesor_panel')


@login_required
def agregar_alumno_a_clase(request):
    """Asigna un alumno ya existente a la clase seleccionada."""
    if request.method == 'POST':
        clase_id = request.POST.get('clase_id') 
        personaje_id = request.POST.get('personaje_id')

        clase = get_object_or_404(Clase, id=clase_id, profesor=request.user)
        personaje = get_object_or_404(Personaje, id=personaje_id)

        personaje.clase = clase
        personaje.save()

        messages.success(request, f"El alumno {personaje.usuario.get_full_name() or personaje.usuario.username} ha sido añadido a {clase.nombre}.")
    return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")


@login_required
def quitar_alumno_de_clase(request, personaje_id):
    """Desvincula a un alumno de su clase actual (deja la clase en None)."""
    personaje = get_object_or_404(Personaje, id=personaje_id, clase__profesor=request.user)
    clase_anterior_id = personaje.clase.id
    nombre_alumno = personaje.usuario.get_full_name() or personaje.usuario.username

    personaje.clase = None
    personaje.save()

    messages.info(request, f"Se ha retirado a {nombre_alumno} de la clase.")
    return redirect(f"{reverse('profesor_panel')}?clase_id={clase_anterior_id}")

@login_required
def lanzar_evento_clase(request):
    """Asigna un reto del banco a los alumnos fusionándolo con una situación narrativa aleatoria."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('profesor_panel')

    if request.method == 'POST':
        personaje_id = request.POST.get('personaje_id')
        evento_id = request.POST.get('evento_id')
        clase_id = request.POST.get('clase_id')

        # 1. Obtener el reto seleccionado desde la base de datos
        evento_base = get_object_or_404(EventoAleatorio, id=evento_id)

        # 2. Seleccionar una narrativa aleatoria del banco
        narrativas = list(SituacionNarrativa.objects.all())
        situacion = random.choice(narrativas) if narrativas else None

        titulo_envio = situacion.titulo if situacion else "Imprevisto Económico"
        descripcion_envio = situacion.descripcion if situacion else "Situación imprevista en tu día a día."

        # 3. Asignar el evento a los alumnos
        if personaje_id == 'TODOS':
            alumnos = Personaje.objects.filter(clase__profesor=request.user)
            for p in alumnos:
                EventoAlumno.objects.create(
                    personaje=p,
                    evento=evento_base,
                    titulo_narrativo=titulo_envio,
                    descripcion_narrativa=descripcion_envio
                )
            messages.success(request, f"¡Reto enviado a toda la clase ({alumnos.count()} alumnos) con la historia «{titulo_envio}»!")
        elif personaje_id:
            p = get_object_or_404(Personaje, id=personaje_id)
            EventoAlumno.objects.create(
                personaje=p,
                evento=evento_base,
                titulo_narrativo=titulo_envio,
                descripcion_narrativa=descripcion_envio
            )
            nombre = p.usuario.get_full_name() or p.usuario.username
            messages.success(request, f"¡Reto enviado a {nombre} con la historia «{titulo_envio}»!")

    return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")


@login_required
def entregar_tarjeta(request):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('dashboard')

    if request.method == 'POST':
        tarjeta_id = request.POST.get('tarjeta_id')
        personaje_id = request.POST.get('personaje_id')
        clase_id = request.POST.get('clase_id') 

        tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id)

        if personaje_id == 'TODOS':
            alumnos = Personaje.objects.filter(clase__profesor=request.user)
            for p in alumnos:
                TarjetaAlumno.objects.create(personaje=p, tarjeta=tarjeta)
            messages.success(request, f"¡Tarjeta '{tarjeta.nombre}' entregada a toda la clase!")
        elif personaje_id:
            p = get_object_or_404(Personaje, id=personaje_id)
            TarjetaAlumno.objects.create(personaje=p, tarjeta=tarjeta)
            nombre = p.usuario.get_full_name() or p.usuario.username
            messages.success(request, f"¡Tarjeta '{tarjeta.nombre}' entregada a {nombre}!")

    return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")


@login_required
def pagar_salarios(request):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')

    if request.method == 'POST':
        personajes = Personaje.objects.all()
        clase_id = request.POST.get('clase_id')

        for p in personajes:
            p.dinero_anterior = p.patrimonio_total
            p.salud_anterior = p.salud
            p.felicidad_anterior = p.felicidad

            p.dinero_disponible += p.salario_semanal
            Transaccion.objects.create(
                personaje=p,
                monto=p.salario_semanal,
                concepto="Nómina Semanal",
                tipo='INGRESO',
                explicacion_operacion=f"Ingreso del salario base semanal (+{p.salario_semanal}€)."
            )

            coste_total = p.obtener_coste_presupuesto()
            impacto_salud = p.obtener_impacto_salud()
            impacto_felicidad = p.obtener_impacto_felicidad()

            p.dinero_disponible -= coste_total
            p.salud = min(100, max(0, p.salud + impacto_salud))
            p.felicidad = min(100, max(0, p.felicidad + impacto_felicidad))

            Transaccion.objects.create(
                personaje=p,
                monto=-coste_total,
                concepto="Gastos de Presupuesto Semanal",
                tipo='GASTO',
                explicacion_operacion=f"Cobro de gastos semanales: Comida, Vivienda, Transporte y Ocio."
            )

            if p.fondo_emergencia > Decimal('0.00'):
                interes_generado = (p.fondo_emergencia * TASA_INTERES_FONDO).quantize(Decimal('0.01'))
                if interes_generado > Decimal('0.00'):
                    p.fondo_emergencia += interes_generado
                    Transaccion.objects.create(
                        personaje=p,
                        monto=interes_generado,
                        concepto="Intereses del Fondo de Emergencia (+2%)",
                        tipo='INGRESO',
                        explicacion_operacion=f"Rentabilidad del 2% semanal sobre el Fondo de Emergencia (+{interes_generado}€)."
                    )

            p.save()

        messages.success(request, f"¡Ciclo semanal ejecutado correctamente para {personajes.count()} alumnos!")

    return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")


@login_required
def cambiar_salario_alumno(request, personaje_id):
    """Permite al docente ascender o bajar el salario semanal a un alumno."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('dashboard')

    if request.method == 'POST':
        personaje = get_object_or_404(Personaje, id=personaje_id)
        nuevo_salario_str = request.POST.get('nuevo_salario')
        clase_id = request.POST.get('clase_id') 

        try:
            nuevo_salario = Decimal(nuevo_salario_str)
            salario_anterior = personaje.salario_semanal
            personaje.salario_semanal = nuevo_salario
            personaje.save()

            nombre_alumno = personaje.usuario.get_full_name() or personaje.usuario.username
            
            if nuevo_salario > salario_anterior:
                messages.success(request, f"¡Has ASCENDIDO a {nombre_alumno}! Su nuevo sueldo es de {nuevo_salario}€/semana.")
            elif nuevo_salario < salario_anterior:
                messages.warning(request, f"Has reducido el sueldo de {nombre_alumno} a {nuevo_salario}€/semana.")
            else:
                messages.info(request, f"El sueldo de {nombre_alumno} se mantiene en {nuevo_salario}€/semana.")

        except (ValueError, TypeError):
            messages.error(request, "Importe de salario no válido.")

    return redirect(f"{reverse('profesor_panel')}?clase_id={clase_id}")


@login_required
def resolver_impugnacion(request, evento_alumno_id):
    """El docente aprueba o rechaza la impugnación."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso no autorizado.")
        return redirect('profesor_panel')

    evento_alumno = get_object_or_404(EventoAlumno, id=evento_alumno_id)
    accion = request.POST.get('accion') # 'APROBAR' o 'RECHAZAR'

    if accion == 'APROBAR' and evento_alumno.estado_revision == 'PENDIENTE':
        evento_alumno.exito_reto = True
        evento_alumno.estado_revision = 'APROBADO'
        evento_alumno.save()

        # Reembolso de la penalización y ajuste de estadísticas
        personaje = evento_alumno.personaje
        monto_reembolso = evento_alumno.evento.penalizacion_dinero
        personaje.dinero_disponible += monto_reembolso
        personaje.salud = min(100, personaje.salud + evento_alumno.evento.penalizacion_salud)
        personaje.felicidad = min(100, personaje.felicidad + evento_alumno.evento.penalizacion_felicidad)
        personaje.save()

        # Registro contable
        Transaccion.objects.create(
            personaje=personaje,
            tipo='INGRESO',
            concepto=f"Ajuste Docente: Reto Aprobado ({evento_alumno.evento.temario})",
            monto=monto_reembolso,
            explicacion_operacion="Corrección tras revisión de respuesta impugnada."
        )
        messages.success(request, f"Impugnación aprobada. Se le han devuelto {monto_reembolso}€ al alumno.")

    elif accion == 'RECHAZAR':
        evento_alumno.estado_revision = 'RECHAZADO'
        evento_alumno.save()
        messages.warning(request, "Impugnación desestimada.")

    return redirect('profesor_panel')



# ==========================================
# 3. REPOSITORIO Y BANCO DE RECURSOS
# ==========================================

@login_required
def banco_recursos(request):
    """Página dedicada a buscar, filtrar, crear y editar recursos."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        return redirect('dashboard')

    f_curso = request.GET.get('curso', '')
    f_dificultad = request.GET.get('dificultad', '')
    f_temario = request.GET.get('temario', '')

    tarjetas = Tarjeta.objects.all()
    eventos_list = EventoAleatorio.objects.all()
    
    if f_curso:
        tarjetas = tarjetas.filter(curso=f_curso)
        eventos_list = eventos_list.filter(curso=f_curso)
    if f_dificultad:
        tarjetas = tarjetas.filter(dificultad=f_dificultad)
        eventos_list = eventos_list.filter(dificultad=f_dificultad)
    if f_temario:
        tarjetas = tarjetas.filter(Q(nombre__icontains=f_temario) | Q(temario__icontains=f_temario))
        eventos_list = eventos_list.filter(Q(pregunta_matematica__icontains=f_temario) | Q(temario__icontains=f_temario))

    paginator = Paginator(eventos_list, 9)
    page_number = request.GET.get('page')
    eventos_paginados = paginator.get_page(page_number)

    context = {
        'tarjetas': tarjetas,
        'eventos': eventos_paginados,
        'eventos_list': eventos_list,
                        
    }
    return render(request, 'juego/repositorio.html', context)


@login_required
def crear_tarjeta_personalizada(request):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('profesor_panel')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        tipo = request.POST.get('tipo', 'TRABAJO')
        efecto_dinero = Decimal(request.POST.get('efecto_dinero') or '0.00')
        efecto_salud = int(request.POST.get('efecto_salud') or 0)
        efecto_felicidad = int(request.POST.get('efecto_felicidad') or 0)
        es_publica = request.POST.get('es_publica') == 'on'
        
        curso = request.POST.get('curso', '1_ESO')
        dificultad = request.POST.get('dificultad', 'MEDIO')
        temario = request.POST.get('temario', 'General')

        Tarjeta.objects.create(
            creador=request.user,
            nombre=nombre,
            descripcion=descripcion,
            tipo=tipo,
            efecto_dinero=efecto_dinero,
            efecto_salud=efecto_salud,
            efecto_felicidad=efecto_felicidad,
            es_publica=es_publica,
            curso=curso,
            dificultad=dificultad,
            temario=temario,
        )
        messages.success(request, f"Tarjeta '{nombre}' guardada en el catálogo.")

    return redirect(request.META.get('HTTP_REFERER', 'banco_recursos'))


@login_required
def crear_evento_personalizado(request):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('profesor_panel')

    if request.method == 'POST':
        curso = request.POST.get('curso', '1_ESO')
        dificultad = request.POST.get('dificultad', 'MEDIO')
        temario = request.POST.get('temario', 'General')
        tipo_respuesta = request.POST.get('tipo_respuesta', 'NUMERICA')
        pregunta_matematica = request.POST.get('pregunta_matematica', '')
        opciones_test = request.POST.get('opciones_test', '')
        respuesta_correcta = request.POST.get('respuesta_correcta', '')
        penalizacion_dinero = Decimal(request.POST.get('penalizacion_dinero') or '0.00')
        penalizacion_salud = int(request.POST.get('penalizacion_salud') or 0)
        penalizacion_felicidad = int(request.POST.get('penalizacion_felicidad') or 0)
        porcentaje_mitigacion = int(request.POST.get('porcentaje_mitigacion') or 50)
        imagen_adjunta = request.FILES.get('imagen')
        if imagen_adjunta and imagen_adjunta.size > 5 * 1024 * 1024:
            messages.error(request, "La imagen es demasiado pesada. El tamaño máximo permitido es 5 MB.")
            return redirect(request.META.get('HTTP_REFERER') or 'banco_recursos')

        
        EventoAleatorio.objects.create(
            creador=request.user,
            curso=curso,
            dificultad=dificultad,
            temario=temario,
            tipo_respuesta=tipo_respuesta,
            pregunta_matematica=pregunta_matematica,
            opciones_test=opciones_test,
            respuesta_correcta=respuesta_correcta,
            penalizacion_dinero=penalizacion_dinero,
            penalizacion_salud=penalizacion_salud,
            penalizacion_felicidad=penalizacion_felicidad,
            porcentaje_mitigacion=porcentaje_mitigacion,
            imagen=imagen_adjunta # <-- Guardar imagen
        )
        
        messages.success(request, f"Reto del tema '{temario}' guardado correctamente.")

    return redirect(request.META.get('HTTP_REFERER', 'banco_recursos'))


@login_required
def editar_tarjeta(request, tarjeta_id):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('banco_recursos')

    tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id)

    if request.method == 'POST':
        tarjeta.nombre = request.POST.get('nombre')
        tarjeta.descripcion = request.POST.get('descripcion')
        tarjeta.curso = request.POST.get('curso', '1_ESO')
        tarjeta.dificultad = request.POST.get('dificultad', 'MEDIO')
        tarjeta.temario = request.POST.get('temario', 'General')
        tarjeta.efecto_dinero = Decimal(request.POST.get('efecto_dinero') or '0.00')
        tarjeta.efecto_salud = int(request.POST.get('efecto_salud') or 0)
        tarjeta.efecto_felicidad = int(request.POST.get('efecto_felicidad') or 0)
        tarjeta.save()

        messages.success(request, f"Tarjeta '{tarjeta.nombre}' actualizada correctamente.")

    return redirect('banco_recursos')


@login_required
def editar_evento(request, evento_id):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('banco_recursos')

    evento = get_object_or_404(EventoAleatorio, id=evento_id)

    if request.method == 'POST':
        evento.curso = request.POST.get('curso', '1_ESO')
        evento.dificultad = request.POST.get('dificultad', 'MEDIO')
        evento.temario = request.POST.get('temario', 'General')
        evento.tipo_respuesta = request.POST.get('tipo_respuesta', 'NUMERICA')
        evento.pregunta_matematica = request.POST.get('pregunta_matematica', '')
        evento.opciones_test = request.POST.get('opciones_test', '')
        evento.respuesta_correcta = request.POST.get('respuesta_correcta', '')
        evento.penalizacion_dinero = Decimal(request.POST.get('penalizacion_dinero') or '0.00')
        evento.penalizacion_salud = int(request.POST.get('penalizacion_salud') or 0)
        evento.penalizacion_felicidad = int(request.POST.get('penalizacion_felicidad') or 0)
        evento.porcentaje_mitigacion = int(request.POST.get('porcentaje_mitigacion') or 50)
        evento.imagen = request.FILES.get('imagen')
        if evento.imagen and evento.imagen.size > 5 * 1024 * 1024:
            messages.error(request, "La imagen es demasiado pesada. El tamaño máximo permitido es 5 MB.")
            return redirect(request.META.get('HTTP_REFERER') or 'banco_recursos')
        evento.save()
            
        messages.success(request, f"Reto del tema '{evento.temario}' actualizado correctamente.")

    return redirect('banco_recursos')


@login_required
def eliminar_tarjeta(request, tarjeta_id):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('profesor_panel')

    if request.method == 'POST':
        tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id)
        nombre_tarjeta = tarjeta.nombre
        tarjeta.delete()
        messages.success(request, f"Tarjeta '{nombre_tarjeta}' eliminada correctamente.")

    return redirect(request.META.get('HTTP_REFERER', 'profesor_panel'))


@login_required
def eliminar_evento(request, evento_id):
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso restringido al docente.")
        return redirect('profesor_panel')

    if request.method == 'POST':
        evento = get_object_or_404(EventoAleatorio, id=evento_id)
        temario_evento = evento.temario
        evento.delete()
        messages.success(request, f"Reto del tema '{temario_evento}' eliminado correctamente.")

    return redirect(request.META.get('HTTP_REFERER', 'profesor_panel'))



# ==========================================
# 4. CARTAS DE RECOMPENSAS
# ==========================================

# LISTADO DE CARTAS BÁSICAS POR DEFECTO
CARTAS_DEFECTO_PREDEFINIDAS = [
    {
        "titulo": "Día sin deberes",
        "descripcion": "Exención de entregar las tareas individuales de un día determinado.",
        "precio_base": Decimal('15.00'),
        "stock_total": 3,
        "incremento_por_uso": Decimal('5.00')
    },
    {
        "titulo": "Elegir sitio por un día",
        "descripcion": "Puedes cambiarte al sitio que desees en el aula durante una jornada completa.",
        "precio_base": Decimal('10.00'),
        "stock_total": 5,
        "incremento_por_uso": Decimal('3.00')
    },
    {
        "titulo": "Elegir música en clase",
        "descripcion": "Elige la lista de reproducción durante el tiempo de trabajo individual.",
        "precio_base": Decimal('8.00'),
        "stock_total": 4,
        "incremento_por_uso": Decimal('2.00')
    },
    {
        "titulo": "Pista en un reto",
        "descripcion": "El profesor te dará una pista directa durante la resolución de un problema.",
        "precio_base": Decimal('12.00'),
        "stock_total": 5,
        "incremento_por_uso": Decimal('4.00')
    },
    {
        "titulo": "Entrega tardía (+24h)",
        "descripcion": "Permite entregar un trabajo hasta 24 horas después del plazo fijado sin penalización.",
        "precio_base": Decimal('20.00'),
        "stock_total": 2,
        "incremento_por_uso": Decimal('8.00')
    },
]

@login_required
def tienda_cartas(request):
    """Vista diferenciada según rol: Alumno (compras) vs Profesor (administración)."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()

    if es_profesor:
        # VISTA DOCENTE: Selección de clase y gestión del catálogo
        clases = Clase.objects.filter(profesor=request.user).order_by('nombre')
        clase_id = request.GET.get('clase_id')
        
        clase_seleccionada = None
        if clase_id:
            clase_seleccionada = clases.filter(id=clase_id).first()
        if not clase_seleccionada and clases.exists():
            clase_seleccionada = clases.first()

        cartas = CartaTienda.objects.filter(clase=clase_seleccionada) if clase_seleccionada else CartaTienda.objects.none()
        
        # Historial de cartas en posesión de alumnos de esta clase
        cartas_alumnos = CartaAlumno.objects.filter(
            carta__clase=clase_seleccionada, 
            estado='ACTIVA'
        ).select_related('personaje__usuario', 'carta') if clase_seleccionada else CartaAlumno.objects.none()

        context = {
            'es_profesor': True,
            'clases': clases,
            'clase_seleccionada': clase_seleccionada,
            'cartas': cartas,
            'cartas_alumnos': cartas_alumnos,
        }
    else:
        # VISTA ALUMNO: Compra e inventario personal
        personaje = get_object_or_404(Personaje, usuario=request.user)
        if not personaje.clase:
            messages.warning(request, "Aún no estás asignado a ninguna clase.")
            return redirect('dashboard')

        cartas = CartaTienda.objects.filter(clase=personaje.clase)
        mis_cartas = CartaAlumno.objects.filter(personaje=personaje, estado='ACTIVA')

        context = {
            'es_profesor': False,
            'personaje': personaje,
            'cartas': cartas,
            'mis_cartas': mis_cartas,
        }

    return render(request, 'juego/tienda.html', context)

@login_required
def comprar_carta(request, carta_id):
    """Procesa la compra de una carta por parte del alumno."""
    if request.method == 'POST':
        personaje = get_object_or_404(Personaje, usuario=request.user)
        carta = get_object_or_404(CartaTienda, id=carta_id, clase=personaje.clase)

        if carta.stock_disponible <= 0:
            messages.error(request, "¡Esta carta se ha agotado en la tienda!")
            return redirect('tienda_cartas')

        precio_final = carta.precio_actual

        if personaje.dinero_disponible < precio_final:
            messages.error(request, f"No tienes suficiente dinero. La carta cuesta {precio_final}€.")
            return redirect('tienda_cartas')

        # 1. Descontar dinero y reducir stock
        personaje.dinero_disponible -= precio_final
        personaje.save()

        carta.stock_disponible -= 1
        carta.save()

        # 2. Registrar carta al alumno
        CartaAlumno.objects.create(
            personaje=personaje,
            carta=carta,
            precio_pagado=precio_final
        )

        # 3. Registrar transacción contable
        Transaccion.objects.create(
            personaje=personaje,
            tipo='GASTO',
            concepto=f"Compra de Carta: {carta.titulo}",
            monto=precio_final,
            explicacion_operacion="Adquisición de carta de recompensa en la tienda."
        )

        messages.success(request, f"¡Felicidades! Has comprado '{carta.titulo}' por {precio_final}€.")

    return redirect('tienda_cartas')


@login_required
def usar_carta_profesor(request, carta_alumno_id):
    """El profesor valida y consumirá la carta del alumno en clase."""
    es_profesor = request.user.is_staff or Clase.objects.filter(profesor=request.user).exists()
    if not es_profesor:
        messages.error(request, "Acceso no autorizado.")
        return redirect('profesor_panel')

    carta_alumno = get_object_or_404(CartaAlumno, id=carta_alumno_id, estado='ACTIVA')
    carta_tienda = carta_alumno.carta

    if request.method == 'POST':
        # 1. Marcar carta del alumno como USADA
        carta_alumno.estado = 'USADA'
        carta_alumno.fecha_uso = timezone.now()
        carta_alumno.save()

        # 2. Reincorporar a la tienda + incrementar el precio base
        carta_tienda.stock_disponible += 1
        carta_tienda.precio_base += carta_tienda.incremento_por_uso
        carta_tienda.save()

        messages.success(request, f"Carta '{carta_tienda.titulo}' canjeada. Vuelve a la tienda por un precio base superior (+{carta_tienda.incremento_por_uso}€).")

    return redirect(f"{reverse('profesor_panel')}?clase_id={carta_tienda.clase.id}")


@login_required
def cargar_cartas_defecto(request, clase_id):
    """Carga el paquete inicial de cartas predefinidas a una clase."""
    clase = get_object_or_404(Clase, id=clase_id, profesor=request.user)
    
    creadas = 0
    for c in CARTAS_DEFECTO_PREDEFINIDAS:
        _, created = CartaTienda.objects.get_or_create(
            clase=clase,
            titulo=c['titulo'],
            defaults={
                'descripcion': c['descripcion'],
                'precio_base': c['precio_base'],
                'stock_total': c['stock_total'],
                'stock_disponible': c['stock_total'],
                'incremento_por_uso': c['incremento_por_uso']
            }
        )
        if created:
            creadas += 1

    messages.success(request, f"Se han cargado {creadas} cartas básicas en {clase.nombre}.")
    return redirect(f"{reverse('tienda_cartas')}?clase_id={clase.id}")


@login_required
def crear_carta(request):
    """El profesor crea una nueva carta personalizada para su clase."""
    if request.method == 'POST':
        clase_id = request.POST.get('clase_id')
        clase = get_object_or_404(Clase, id=clase_id, profesor=request.user)

        stock = int(request.POST.get('stock_total', 3))
        CartaTienda.objects.create(
            clase=clase,
            titulo=request.POST.get('titulo').strip(),
            descripcion=request.POST.get('descripcion').strip(),
            precio_base=Decimal(request.POST.get('precio_base', '10.00')),
            stock_total=stock,
            stock_disponible=stock,
            incremento_por_uso=Decimal(request.POST.get('incremento_por_uso', '5.00'))
        )
        messages.success(request, "Carta añadida correctamente al catálogo.")
        return redirect(f"{reverse('tienda_cartas')}?clase_id={clase.id}")
    return redirect('tienda_cartas')


@login_required
def editar_carta(request, carta_id):
    """El profesor modifica precio base, stock o características de una carta."""
    carta = get_object_or_404(CartaTienda, id=carta_id, clase__profesor=request.user)
    
    if request.method == 'POST':
        carta.titulo = request.POST.get('titulo').strip()
        carta.descripcion = request.POST.get('descripcion').strip()
        carta.precio_base = Decimal(request.POST.get('precio_base'))
        carta.incremento_por_uso = Decimal(request.POST.get('incremento_por_uso'))
        
        nuevo_stock_total = int(request.POST.get('stock_total'))
        diferencia_stock = nuevo_stock_total - carta.stock_total
        carta.stock_total = nuevo_stock_total
        
        # Ajustar el stock disponible proporcionalmente
        carta.stock_disponible = max(0, carta.stock_disponible + diferencia_stock)
        carta.save()

        messages.success(request, f"Carta '{carta.titulo}' actualizada correctamente.")
        return redirect(f"{reverse('tienda_cartas')}?clase_id={carta.clase.id}")
    return redirect('tienda_cartas')


@login_required
def eliminar_carta(request, carta_id):
    """El profesor retira una carta del catálogo."""
    carta = get_object_or_404(CartaTienda, id=carta_id, clase__profesor=request.user)
    clase_id = carta.clase.id
    carta.delete()
    messages.warning(request, "Carta eliminada del catálogo.")
    return redirect(f"{reverse('tienda_cartas')}?clase_id={clase_id}")

