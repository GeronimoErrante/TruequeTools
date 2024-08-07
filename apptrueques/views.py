from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_406_NOT_ACCEPTABLE, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_409_CONFLICT,HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .serializers import *
from rest_framework.authtoken.models import Token
from .models import Usuario, Empleado
from django.contrib.auth import authenticate
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from .api import *
from .utils import *
from datetime import datetime, timedelta, time
from django.db import transaction
from django.db.models import Q

@permission_classes([AllowAny])
class RegisterView(APIView):
    def post(self, request):
        serializer = UsuarioSerializer(data=request.data)
        print(request.data)
        if len(request.data.get('password', '')) < 6:
            return Response({"error": "La contraseña debe tener al menos 6 caracteres"}, status=HTTP_400_BAD_REQUEST)
        if Usuario.objects.filter(email=request.data['email']).exists():
            return Response({"error": "El correo electrónico ya está en uso"}, status=HTTP_409_CONFLICT)
        if serializer.is_valid():
            try:
                
                sucursal = get_object_or_404(Sucursal, pk=request.data['sucursal_favorita'])
                fecha_nacimiento = datetime.strptime(request.data['fecha_de_nacimiento'], '%Y-%m-%d').date()
                fecha_actual = datetime.now().date()
                edad = fecha_actual.year - fecha_nacimiento.year - ((fecha_actual.month, fecha_actual.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                if (edad < 18):
                    return Response({"error": "Para registrarse en el sistema debe ser mayor de edad"}, status=HTTP_406_NOT_ACCEPTABLE)
                    
                usuario = Usuario.objects.create_user(
                    username=request.data['username'],
                    email=request.data['email'],
                    password=request.data['password'],
                    fecha_de_nacimiento=request.data['fecha_de_nacimiento'],  
                    sucursal_favorita=sucursal
                )
                token, created = Token.objects.get_or_create(user=usuario)
                print(serializer.validated_data)
                response_data = {
                    'token': token.key,
                    'user': serializer.data,
                    'sucursal favorita': sucursal.nombre
                }
                return Response(response_data, status=HTTP_201_CREATED)
            except ValidationError as e:
                return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


@permission_classes([AllowAny])
class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']
        user = authenticate(request, email=email, password=password)      
        user_instance = Usuario.objects.get(email=email)

        if user_instance.bloqueado:
            return Response({"error": "El usuario se encuentra bloqueado"}, status=HTTP_403_FORBIDDEN)
        
        if user is None:
            return Response({"error": "invalid credentials"}, status=HTTP_400_BAD_REQUEST)
        token, created = Token.objects.get_or_create(user=user)
        serializer = UsuarioSerializer(instance=user)
        return Response({'token': token.key, 'user': serializer.data}, status=HTTP_200_OK)


@permission_classes([AllowAny])
class LoginWorker(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"error": "invalid credentials"}, status=HTTP_400_BAD_REQUEST)
        serializer = EmpleadoSerializer(instance=user)
        return Response(serializer.data, status=HTTP_200_OK)



@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class ProfileView(APIView):
    def get(self, request):
        serializer = UsuarioSerializer(instance=request.user)
        return Response({"Usuario logueado": serializer.data}, status=HTTP_200_OK)

    def patch(self, request):
        user = request.user
        print(request.data)

        # Validar la longitud de la nueva contraseña si se proporciona
        new_password = request.data.get('new_password', None)
        confirm_password = request.data.get('confirm_password', None)

        if new_password is not None and new_password != '':
            if len(new_password) < 6:
                return Response({"error": "La nueva contraseña debe tener al menos 6 caracteres."}, status=HTTP_406_NOT_ACCEPTABLE)
        
            if new_password != confirm_password:
                return Response({"error": "Las contraseñas no coinciden."}, status=HTTP_409_CONFLICT)

        # Serializar y validar los datos
        serializer = UsuarioSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        

@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class CreatePostView(APIView):
    def post(self, request):
        serializer = PublicacionSerializer(data=request.data)
        print("DATA", request.data)
        if serializer.is_valid():
            suc_destino = Sucursal.objects.get(pk=request.data['sucursal_destino'])
            publicacion = serializer.save(usuario_propietario=request.user, sucursal_destino = suc_destino)  
            response_data = PublicacionSerializer(publicacion).data 
            print("RESPONSE", response_data) 
            return Response(response_data, status=HTTP_201_CREATED) 
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
class CreateSucursalView(APIView):
    def post(self, request):
        serializer = SucursalSerializer(data=request.data)
        if (serializer.is_valid()):
            sucursal = serializer.save()
            response_data = SucursalSerializer(sucursal).data
            return Response(response_data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def get(self, request):
        query = request.query_params.get('q', None)
        if query:
            sucursales = Sucursal.objects.filter(nombre__icontains=query, borrada=False)
        else:
            sucursales = Sucursal.objects.filter(borrada=False)
        serializer = SucursalSerializer(sucursales, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def patch(self, request, sucursal_id):
        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
        except Sucursal.DoesNotExist:
            return Response({'error': 'Sucursal not found.'}, status=HTTP_404_NOT_FOUND)
        
        total_sucursales = Sucursal.objects.filter(borrada=False).count()
   
        if total_sucursales <= 1:
            return Response({'error': 'Cannot delete the only remaining Sucursal.'}, status=HTTP_400_BAD_REQUEST)
        
        # Marcar la sucursal como borrada
        sucursal.borrada = True
        sucursal.save()

        # Reasignar empleados a otra sucursal
        empleados = Empleado.objects.filter(sucursal_de_trabajo=sucursal)
        otra_sucursal = Sucursal.objects.exclude(pk=sucursal_id).exclude(borrada=True).first()
        print(otra_sucursal)
        if otra_sucursal:
            for empleado in empleados:
                empleado.sucursal_de_trabajo = otra_sucursal
                empleado.save()
        
        users_sin_sucursal = Usuario.objects.filter(sucursal_favorita=sucursal)

        for user in users_sin_sucursal:
            user.sucursal_favorita = otra_sucursal
            contenido = f"Tu sucursal favorita ha cerrado, ahora es {otra_sucursal}, pero puedes elegir otra en tu perfil."
            notif = Notificacion.objects.create(contenido=contenido, usuario=user)
            user.save()
        return Response({'status': 'Sucursal marked as borrada and employees reassigned.'}, status=HTTP_200_OK)




class EmployeeView(APIView):
    def post(self, request):
        serializer = EmpleadoSerializer(data=request.data)
        if serializer.is_valid():
            empleado = serializer.save()
            response_data = EmpleadoSerializer(empleado).data
            return Response(response_data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
    def delete(self, request, employee_id):
        try:
            empleado = Empleado.objects.get(pk=employee_id)
            empleado.delete()
            return Response(status=HTTP_200_OK)
        except Empleado.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)





@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class CommentView(APIView):
    def post(self, request, publicacion_id):
        try:
            publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
        except Publicacion.DoesNotExist:
            return Response({"detail": "La publicación que deseas comentar ya no está disponible"}, status=HTTP_404_NOT_FOUND)
        serializer = ComentarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(publicacion=publicacion, usuario_propietario=request.user)  
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
    def delete(self, request, publicacion_id, comentario_id):
        try:
            publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
            comentario = get_object_or_404(Comentario, pk=comentario_id, publicacion=publicacion, usuario_propietario=request.user)
        except (Publicacion.DoesNotExist, Comentario.DoesNotExist):
            return Response({"detail": "El comentario o la publicación no está disponible"}, status=HTTP_404_NOT_FOUND)
        
        comentario.delete()
        return Response(status=HTTP_204_NO_CONTENT)
        
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class ReplyView(APIView):
    def post(self, request, publicacion_id, comentario_id):
        try:
            comentario_original = get_object_or_404(Comentario, pk=comentario_id)
        except Comentario.DoesNotExist:
            return Response({"detail": "el comentario que deseas responder ya no está disponible"}, status=HTTP_404_NOT_FOUND)
        try:
            publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
        except Publicacion.DoesNotExist:
            return Response({"detail": "la publicacion ya no está disponible"}, status=HTTP_404_NOT_FOUND)
        
        if publicacion.usuario_propietario.id != request.user.id:
            return Response({"detail": "Solo el propietario de la publicación puede responder a los comentarios"}, status=HTTP_403_FORBIDDEN)
        
        request.data['usuario_propietario'] = request.user.id
        
        serializer = ComentarioRespuestaSerializer(data=request.data)
        if serializer.is_valid():
            respuesta = serializer.save()
            comentario_original.respuesta = respuesta
            comentario_original.save()
            serializer.save()  
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class PostDetailView(APIView):
    def get(self, request, publicacion_id):
        try:
            publicacion = Publicacion.objects.get(pk=publicacion_id)
            serializer = PublicacionSerializer(publicacion)
            print(serializer.data)
            return Response(serializer.data, status=HTTP_200_OK)
        except Publicacion.DoesNotExist:
            return Response({"detail": "La publicación que deseas ver no está disponible"}, status=HTTP_404_NOT_FOUND)

    def delete(self, request, publicacion_id):
        try:
            publicacion = Publicacion.objects.get(pk=publicacion_id)
            for sol in publicacion.solicitudes_recibidas.all():
                usernotif = sol.publicacion_a_intercambiar.usuario_propietario
                contenido = f"El usuario {request.user} ha rechazado tu solicitud de intercambio"
                notif = Notificacion.objects.create(contenido=contenido, usuario=usernotif)
                sol.estado = 'RECHAZADA'
                sol.save()
            publicacion.delete()
            return Response(status=HTTP_200_OK)
        except Publicacion.DoesNotExist:
            return Response({"detail": "La publicación que deseas ver no está disponible"}, status=HTTP_404_NOT_FOUND)
       


class PostDetailAdminView(APIView):
    def get(self, request, publicacion_id):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)
        print(email)
        try:
            empleado = Empleado.objects.get(email=email)
        except Empleado.DoesNotExist:
            return Response({"error": "No se encontró un administrador asociado a este email."}, status=HTTP_404_NOT_FOUND)
        
        if email == 'admin@truequetools.com':
            try:
                publicacion = Publicacion.objects.get(pk=publicacion_id)
                serializer = PublicacionSerializer(publicacion)
                print(serializer.data)
                return Response(serializer.data, status=HTTP_200_OK)
            except Publicacion.DoesNotExist:
                return Response({"detail": "La publicación que deseas ver no está disponible"}, status=HTTP_404_NOT_FOUND)
        else:
            return Response({'detail:':'no tienes permisos para entrar al detalle.'})
        
    def delete(self, request, publicacion_id):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)
        print(email)
        try:
            empleado = Empleado.objects.get(email=email)
        except Empleado.DoesNotExist:
            return Response({"error": "No se encontró un administrador asociado a este email."}, status=HTTP_404_NOT_FOUND)
        
        if email == 'admin@truequetools.com':
            try:
                publicacion = Publicacion.objects.get(pk=publicacion_id)
                for sol in publicacion.solicitudes_recibidas.all():
                    usernotif = sol.publicacion_a_intercambiar.usuario_propietario
                    contenido = f"Se rechazó tu solicitud de intercambio para la publicacion '{sol.publicacion_deseada.titulo}' porque el propietario ha infringido las normas."
                    notif = Notificacion.objects.create(contenido=contenido, usuario=usernotif)
                    sol.estado='RECHAZADA'
                    sol.save()
                publicacion.delete()
                return Response(status=HTTP_200_OK)
            except Publicacion.DoesNotExist:
                return Response({"detail": "La publicación que deseas ver no está disponible"}, status=HTTP_404_NOT_FOUND)
        else:
            return Response({'detail:':'no tienes permisos para entrar al detalle.'})
        

@permission_classes([AllowAny])
class EmployeeDetailView(APIView):
    def get(self, request, employee_id):
        try:
            employee = Empleado.objects.get(pk=employee_id)
            serializer = EmpleadoSerializer(employee)
            return Response(serializer.data, status=HTTP_200_OK)
        except Empleado.DoesNotExist:
            return Response({"detail": "El empleado que deseas ver no está disponible"}, status=HTTP_404_NOT_FOUND)
    
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class UserInfoView(APIView):
     def get(self, request):
        user = request.user
        serializer = UsuarioSerializer(user)
        return Response(serializer.data)
     

class SucursalInfo(APIView):
    def get(self, request, sucursal_id):
        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
            serializer = SucursalSerializer(sucursal)
            return Response(serializer.data, status=HTTP_200_OK)
        except Sucursal.DoesNotExist:
            return Response({"detail": "No existe sucursal con ese id"}, status=HTTP_404_NOT_FOUND)
        
    def patch(self, request, sucursal_id):
        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
            serializer = SucursalSerializer(sucursal, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(status=HTTP_200_OK)
        except Sucursal.DoesNotExist:
            return Response({"detail": "No existe sucursal con ese id"}, status=HTTP_404_NOT_FOUND)



@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class PostComments(APIView):
    def get(self, request, publicacion_id):
        try:
            publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
        except Publicacion.DoesNotExist:
            return Response({"detail": "La publicación no está disponible"}, status=HTTP_404_NOT_FOUND)
        serializer = PublicacionSerializer(publicacion)
        comentarios = serializer.get_comentarios(publicacion)
        return Response(comentarios)
    
    
class EmployeesList(APIView):
    def get(self, request):
        query = request.query_params.get('q', None)
        if query:
            employees = Empleado.objects.filter(email__icontains=query).exclude(email="admin@truequetools.com")
            print(employees)
        else:
            employees = Empleado.objects.exclude(email="admin@truequetools.com")
        serializer = EmpleadoSerializer(employees, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    


@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class SearchPostsView(APIView):
    def get(self, request):
        # Obtén el queryset de PublicacionViewSet
        viewset = PublicacionViewSet()
        viewset.request = request  # Necesario si el método get_queryset depende del request
        queryset = viewset.get_queryset()
        
        # Filtra por título si hay un query param 'q'
        query = request.query_params.get('q', None)
        if query:
            queryset = queryset.filter(titulo__icontains=query)
            
        # Serializa y retorna la respuesta
        serializer = PublicacionSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    
class UserView(APIView):
    def get(self, request):
        # Obtén el queryset de UsuarioViewSet
        viewset = UsuarioViewSet()
        viewset.request = request  # Necesario si el método get_queryset depende del request
        queryset = viewset.get_queryset()
        
        # Filtra por nombre si hay un query param 'q'
        query = request.query_params.get('q', None)
        if query:
            queryset = queryset.filter(email__icontains=query)
        serializer = UsuarioSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def patch(self, request, usuario_id):
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)
        
        data = {'bloqueado': True}
        if usuario.bloqueado:
            data = {'bloqueado': False}
            
        serializer = UsuarioSerializer(usuario, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)    

    

@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class MisProductosView(APIView):
    def get(self, request):
        user = request.user
        try:
            # Obtener IDs de las publicaciones con al menos una solicitud en estado "PENDIENTE", "EXITOSA" o "FALLIDA"
            solicitudes_activas = SolicitudDeIntercambio.objects.filter(
                Q(estado='PENDIENTE') | Q(estado='EXITOSA') | Q(estado='FALLIDA')
            )

            # Obtener IDs únicas de publicaciones en solicitudes activas
            publicaciones_con_solicitudes_activas = set()
            for solicitud in solicitudes_activas:
                publicaciones_con_solicitudes_activas.add(solicitud.publicacion_deseada_id)
                publicaciones_con_solicitudes_activas.add(solicitud.publicacion_a_intercambiar_id)

            # Obtener todas las publicaciones del usuario actual que no están en la lista de IDs de publicaciones con solicitudes activas
            queryset = Publicacion.objects.filter(usuario_propietario=user).exclude(id__in=publicaciones_con_solicitudes_activas).order_by('-fecha')
            serializer = PublicacionSerializer(queryset, many=True)
            
            return Response(serializer.data, status=HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class SolicitudView(APIView):
    def post(self, request): ##este método se ejecuta cuando intercambia un prod
        publicacion_deseada_id = request.data.get('publicacion_deseada')
        publicacion_a_intercambiar_id = request.data.get('publicacion_a_intercambiar')
        try:
            publicacion_deseada = Publicacion.objects.get(id=publicacion_deseada_id)
            publicacion_a_intercambiar = Publicacion.objects.get(id=publicacion_a_intercambiar_id)
            print(publicacion_deseada.categoria, publicacion_a_intercambiar.categoria)
            if publicacion_deseada.categoria != publicacion_a_intercambiar.categoria:
                return Response({'error': 'Las publicaciones deben ser de la misma categoría.'}, status=HTTP_400_BAD_REQUEST)
            
            fecha = request.data.get('fecha_del_intercambio')
            print(fecha)
            if fecha:
                fecha = parse_datetime(fecha)
                print(fecha)
                if not fecha:
                    return Response({'error': 'Formato de fecha inválido.'}, status=HTTP_404_NOT_FOUND)
                if fecha < datetime.today():
                    return Response({'error': 'Formato de fecha inválido.'}, status=HTTP_404_NOT_FOUND)
                hora_inicio = time(8, 0)  # 8 AM
                hora_fin = time(20, 0)    # 8 PM
                if not (hora_inicio <= fecha.time() <= hora_fin):
                    return Response({'error': 'El servicio está cerrado en ese horario. El horario de atención es de 8:00 a 20:00.'}, status=HTTP_409_CONFLICT)
            else:
                return Response({'error': 'Formato de fecha inválido.'}, status=HTTP_404_NOT_FOUND)

            
            solicitud = SolicitudDeIntercambio.objects.create(
                publicacion_deseada=publicacion_deseada,
                publicacion_a_intercambiar=publicacion_a_intercambiar,
                estado='ESPERA',
                fecha_del_intercambio = fecha,
            )
            serializer = SolicitudDeIntercambioSerializer(solicitud)
            userNotif = solicitud.publicacion_deseada.usuario_propietario 
            contenido = f"El usuario {request.user.username} te ha ofrecido su {solicitud.publicacion_a_intercambiar.titulo} a cambio de tu {solicitud.publicacion_deseada.titulo}"
            notificacion = Notificacion.objects.create(contenido=contenido, usuario=userNotif)
            print(serializer.data)
            return Response(serializer.data, status=HTTP_201_CREATED)
    
        except Publicacion.DoesNotExist:
            return Response({'error': 'Publicación no encontrada.'}, status=HTTP_404_NOT_FOUND)
         
  

    def patch(self, request, solicitud_id):
        print("Entrando al método patch")

        try:
            solicitud = SolicitudDeIntercambio.objects.get(id=solicitud_id)
            print(f"Solicitud encontrada: {solicitud.id}")
        except SolicitudDeIntercambio.DoesNotExist:
            print("Solicitud no encontrada")
            return Response(status=HTTP_404_NOT_FOUND)

        accion = request.data.get('accion', '').lower()

        if accion == 'aceptar':
            estado_nuevo = 'PENDIENTE'
            contenido = f"El usuario {request.user.username} aceptó tu solicitud de intercambio! Puedes verla en tu historial"
            usernotif = solicitud.publicacion_a_intercambiar.usuario_propietario
            notif = Notificacion.objects.create(contenido=contenido, usuario=usernotif)
            print(notif)
        elif accion == 'rechazar':
            estado_nuevo = 'RECHAZADA'  
            contenido = f"El usuario {request.user.username} rechazó tu solicitud de intercambio."
            usernotif = solicitud.publicacion_a_intercambiar.usuario_propietario
            notif = Notificacion.objects.create(contenido=contenido, usuario=usernotif)


        data = {'estado': estado_nuevo}
        serializer = SolicitudDeIntercambioSerializer(solicitud, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            print(f"Estado actualizado a: {solicitud.estado}")

            if accion == 'aceptar':
                # Eliminar otras solicitudes para la misma publicación deseada
                otras_solicitudes = SolicitudDeIntercambio.objects.filter(
                    publicacion_deseada=solicitud.publicacion_deseada,
                    estado='ESPERA'
                ).exclude(id=solicitud_id)

                for otra_solicitud in otras_solicitudes:
                    otra_solicitud.estado = 'RECHAZADA'
                    otra_solicitud.save()
                    
                    # Crear notificación para cada solicitud rechazada
                    contenido_rechazo = f"El usuario {request.user.username} rechazó tu solicitud de intercambio."
                    usernotif_rechazo = otra_solicitud.publicacion_a_intercambiar.usuario_propietario
                    print(usernotif_rechazo)
                    notif_rechazo = Notificacion.objects.create(contenido=contenido_rechazo, usuario=usernotif_rechazo)
                    print(notif_rechazo)

            return Response(status=HTTP_204_NO_CONTENT)

        print(f"Errores del serializer: {serializer.errors}")
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        solicitudes = SolicitudDeIntercambio.objects.filter(
        Q(estado='ESPERA') | Q(estado='RECHAZADA'),
        publicacion_a_intercambiar__usuario_propietario=request.user,
        ).order_by('-fecha_del_intercambio')
        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
        

        

@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class MisSolicitudesView(APIView):
    def get(self, request, publicacion_id):
        print(request.data)
        print("ID:",publicacion_id)
        publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
        solicitudes = SolicitudDeIntercambio.objects.filter(
        estado='ESPERA',
        publicacion_deseada=publicacion,
        publicacion_a_intercambiar__usuario_propietario__bloqueado=False
        ).order_by('fecha_del_intercambio')
        
        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        return Response(serializer.data)
    
    
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class HistorialDeSolicitudesView(APIView):
    def get(self, request):
        user = request.user
        # Obtener las solicitudes basadas en las publicaciones del usuario
        solicitudes = get_solicitudes_no_espera(user).exclude(estado='RECHAZADA').order_by('-fecha')
        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        return Response(serializer.data)

@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
class CancelarSolicitudView(APIView):
    def patch(self, request, solicitud_id):
        try:
            solicitud = SolicitudDeIntercambio.objects.get(id=solicitud_id)
        except SolicitudDeIntercambio.DoesNotExist:
            print("Solicitud no encontrada")
            return Response(status=HTTP_404_NOT_FOUND)

        now_local = timezone.localtime(timezone.now())
        if solicitud.fecha_del_intercambio - now_local > timedelta(hours=24):
            solicitud.estado = 'RECHAZADA'
            solicitud.save()
            if request.user == solicitud.publicacion_a_intercambiar.usuario_propietario:
                usernotif = solicitud.publicacion_deseada.usuario_propietario
            else:
                usernotif = solicitud.publicacion_a_intercambiar.usuario_propietario
            fecha = solicitud.fecha_del_intercambio - timedelta(hours=3)

            fecha_formateada = fecha.strftime("%m/%d %H:%Mhs")

            contenido = f"El usuario {request.user} ha cancelado el intercambio del dia {fecha_formateada}."
            notif = Notificacion.objects.create(contenido=contenido, usuario=usernotif)
            return Response(status=HTTP_204_NO_CONTENT)
        else:
            return Response(status=HTTP_409_CONFLICT) 

@permission_classes([AllowAny])
class SolicitudesEmployeeView(APIView):
    def get(self, request, solicitud_id=None):
        if solicitud_id:
            return self.get_solicitud(request, solicitud_id)
        else:
            return self.get_solicitudes(request)

    def get_solicitudes(self, request):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)
        print(email)
        try:
            empleado = Empleado.objects.get(email=email)
        except Empleado.DoesNotExist:
            return Response({"error": "No se encontró un empleado asociado a este email."}, status=HTTP_404_NOT_FOUND)

        sucursal = empleado.sucursal_de_trabajo

        if not sucursal:
            if email == 'admin@truequetools.com':
                solicitudes = SolicitudDeIntercambio.objects.filter(
                estado='PENDIENTE',
        )
                serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
                return Response(serializer.data, status=HTTP_200_OK)
            return Response({"error": "El empleado no tiene una sucursal asignada."}, status=HTTP_400_BAD_REQUEST)
        else:
            solicitudes = SolicitudDeIntercambio.objects.filter(
                publicacion_deseada__sucursal_destino=sucursal,
                estado='PENDIENTE',
            )

        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def get_solicitud(self, request, solicitud_id):
        try:
            solicitud = SolicitudDeIntercambio.objects.get(pk=solicitud_id)
            serializer = SolicitudDeIntercambioSerializer(solicitud)
            return Response(serializer.data, status=HTTP_200_OK)
        except SolicitudDeIntercambio.DoesNotExist:
            return Response({"detail": "La solicitud que deseas ver no está disponible"}, status=HTTP_404_NOT_FOUND)
        
    def patch(self, request, solicitud_id):
        try:
            solicitud = SolicitudDeIntercambio.objects.get(pk=solicitud_id)
        except SolicitudDeIntercambio.DoesNotExist:
            return Response({"detail": "La solicitud que deseas ver no está disponible"}, status=HTTP_404_NOT_FOUND)
        
        action = request.data.get('action')
        if not action:
            return Response({"detail": "No se ha proporcionado ninguna acción"}, status=HTTP_400_BAD_REQUEST)

        if action == 'accept':
            data = {'estado': 'EXITOSA'}
        elif action == 'reject':
            data = {'estado': 'FALLIDA'}
        else:
            return Response({"detail": "Acción no válida"}, status=HTTP_400_BAD_REQUEST)
        
        serializer = SolicitudDeIntercambioSerializer(solicitud, data=data, partial=True)
        
        try:
            user1 = Usuario.objects.get(pk=solicitud.publicacion_a_intercambiar.usuario_propietario.id)
            user2 = Usuario.objects.get(pk=solicitud.publicacion_deseada.usuario_propietario.id)
        except Usuario.DoesNotExist:
            return Response({"detail": "Uno de los dos usuarios no existe."}, status=HTTP_404_NOT_FOUND)

        with transaction.atomic():
            if action == 'accept':
                user1.reputacion += 100
                user2.reputacion += 100

                user1.save()
                user2.save()

            if serializer.is_valid():
                serializer.save()
                print(f"Estado actualizado a: {solicitud.estado}")
            else:
                transaction.set_rollback(True)
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        return Response(status=HTTP_204_NO_CONTENT)

@permission_classes([AllowAny])
class SolicitudesHoyEmployeeView(APIView):
    def get(self, request):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)

        try:
            empleado = Empleado.objects.get(email=email)
        except Empleado.DoesNotExist:
            return Response({"error": "No se encontró un empleado asociado a este email."}, status=HTTP_404_NOT_FOUND)
        
        hoy = timezone.localtime(timezone.now()).date()
        sucursal = empleado.sucursal_de_trabajo

        if not sucursal:
            if email == 'admin@truequetools.com':
                solicitudes = SolicitudDeIntercambio.objects.filter(
                estado='PENDIENTE',
                fecha_del_intercambio__date=hoy
        )
                serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
                return Response(serializer.data, status=HTTP_200_OK)
            return Response({"error": "El empleado no tiene una sucursal asignada."}, status=HTTP_400_BAD_REQUEST)
        else:
            solicitudes = SolicitudDeIntercambio.objects.filter(
                publicacion_deseada__sucursal_destino=sucursal,
                estado='PENDIENTE',
                fecha_del_intercambio__date=hoy
            )
        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        print(serializer.data)
        return Response(serializer.data, status=HTTP_200_OK)

@permission_classes([AllowAny])
class TruequesExitososView(APIView):
    def get(self,request):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)
        try:
            empleado = Empleado.objects.get(email=email)
        except Empleado.DoesNotExist:
            return Response({"error": "No se encontró un empleado asociado a este email."}, status=HTTP_404_NOT_FOUND)
        
        solicitudes = SolicitudDeIntercambio.objects.filter(
            estado='EXITOSA',
        ).order_by('fecha_del_intercambio').distinct()
        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

@permission_classes([AllowAny])
class TruequesFallidosView(APIView):
    def get(self,request):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)
        try:
            empleado = Empleado.objects.get(email=email)
        except Empleado.DoesNotExist:
            return Response({"error": "No se encontró un empleado asociado a este email."}, status=HTTP_404_NOT_FOUND)
        
        solicitudes = SolicitudDeIntercambio.objects.filter(
            estado='FALLIDA',
        ).order_by('fecha_del_intercambio').distinct()
        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
        
        

class VentasView(APIView):
    def post(self, request, solicitud_id):
        try:
            solicitud = SolicitudDeIntercambio.objects.get(id=solicitud_id)
        except SolicitudDeIntercambio.DoesNotExist:
            return Response({"error": "La solicitud de intercambio no existe"}, status=HTTP_404_NOT_FOUND)
        print(request.data)
        productos_data = request.data.get('productos', [])
        productos_validados = []

        print(productos_data)
        # Validar los datos recibidos
        for producto_data in productos_data:
            producto_id = producto_data.get('id')
            cantidad_vendida = producto_data.get('cantidad_vendida')
            print(producto_id)
            print(cantidad_vendida)
            # Verificar que se proporcionen tanto el ID del producto como la cantidad vendida
            if not (producto_id and cantidad_vendida):
                return Response({"error": "Se requiere tanto el ID del producto como la cantidad vendida"}, status=HTTP_400_BAD_REQUEST)
            
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                return Response({"error": f"El producto con ID {producto_id} no existe"}, status=HTTP_404_NOT_FOUND)
            
            # Validar que la cantidad vendida sea un entero positivo
            try:
                cantidad_vendida = int(cantidad_vendida)
                if cantidad_vendida <= 0:
                    raise ValueError()
            except ValueError:
                return Response({"error": "La cantidad vendida debe ser un entero positivo"}, status=HTTP_400_BAD_REQUEST)
            
            productos_validados.append({"producto": producto, "cantidad_vendida": cantidad_vendida})

        try:
            # Crear una nueva instancia de Venta
            venta = Venta.objects.create(intercambio=solicitud)
            
            # Agregar los productos a la venta con las cantidades proporcionadas
            for producto_data in productos_validados:
                producto = producto_data["producto"]
                cantidad_vendida = producto_data["cantidad_vendida"]
                venta_producto = VentaProducto.objects.create(producto=producto, cantidad=cantidad_vendida)
                venta.productos_vendidos.add(venta_producto)
            
            # Guardar la venta en la base de datos
            venta.save()
            
            return Response({"message": "Venta creada exitosamente"}, status=HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"error": "Error al procesar la venta"}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request, solicitud_id):
        try:
            solicitud = get_object_or_404(SolicitudDeIntercambio, pk=solicitud_id)
    
            ventas = Venta.objects.filter(intercambio=solicitud) 
            print(ventas)   
            serializer = VentaSerializer(ventas, many=True)
            print(serializer.data)
            print(ventas)
            return Response(serializer.data, status=HTTP_200_OK)
        except SolicitudDeIntercambio.DoesNotExist:
            return Response({"error": "La solicitud de intercambio no existe"}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Error al obtener las ventas"}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class PostListAdmin(APIView):
    def get(self, request):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)
        print(email)
        try:
            empleado = Empleado.objects.get(email=email)
        except Empleado.DoesNotExist:
            return Response({"error": "No se encontró un empleado asociado a este email."}, status=HTTP_404_NOT_FOUND)
        
        solicitudes_activas = SolicitudDeIntercambio.objects.filter(
            Q(estado='PENDIENTE') | Q(estado='EXITOSA') | Q(estado='FALLIDA')
        )

        # Obtener IDs únicas de publicaciones en solicitudes activas
        publicaciones_con_solicitudes_activas = set()
        for solicitud in solicitudes_activas:
            publicaciones_con_solicitudes_activas.add(solicitud.publicacion_deseada_id)
            publicaciones_con_solicitudes_activas.add(solicitud.publicacion_a_intercambiar_id)

        # Obtener todas las publicaciones que no están en la lista de IDs de publicaciones con solicitudes activas
        queryset = Publicacion.objects.exclude(id__in=publicaciones_con_solicitudes_activas)

        serializer = PublicacionSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
        


class CommentAdminView(APIView):
    def get(self, request, publicacion_id):
        try:
            publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
        except Publicacion.DoesNotExist:
            return Response({"detail": "La publicación que deseas comentar ya no está disponible"}, status=HTTP_404_NOT_FOUND)
        try:
            publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
        except Publicacion.DoesNotExist:
            return Response({"detail": "La publicación no está disponible"}, status=HTTP_404_NOT_FOUND)
        serializer = PublicacionSerializer(publicacion)
        comentarios = serializer.get_comentarios(publicacion)
        return Response(comentarios)
        
    def delete(self, request, publicacion_id, comentario_id):
        email = request.headers.get('X-User-Email')
        if not email:
            return Response({"error": "No se proporcionó el email del usuario."}, status=HTTP_400_BAD_REQUEST)
        
        if email == 'admin@truequetools.com':
            try:
                publicacion = get_object_or_404(Publicacion, pk=publicacion_id)
                comentario = get_object_or_404(Comentario, pk=comentario_id, publicacion=publicacion)
            except (Publicacion.DoesNotExist, Comentario.DoesNotExist):
                return Response({"detail": "El comentario o la publicación no está disponible"}, status=HTTP_404_NOT_FOUND)

            comentario.delete()
            return Response(status=HTTP_204_NO_CONTENT)
        else:
            # Si el usuario no es administrador, devolver un error de autorización
            return Response({"error": "No tienes permiso para eliminar este comentario."}, status=HTTP_403_FORBIDDEN)



@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
class NotificacionView(APIView):
    def get(self, request):
        try:    
            notificaciones = Notificacion.objects.filter(
                usuario=request.user,
            ).order_by('-fecha')
            serializer = NotificacionSerializer(notificaciones, many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        except (Notificacion.DoesNotExist):
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request, notificacion_id=None):
        try:
            if notificacion_id is None:
                # Marcar todas las notificaciones como leídas
                Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
                return Response(status=HTTP_200_OK)
            else:
                notif = get_object_or_404(Notificacion, pk=notificacion_id)
                data = {'leida': not notif.leida}
                serializer = NotificacionSerializer(notif, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(status=HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        except Notificacion.DoesNotExist:
            return Response(status=HTTP_400_BAD_REQUEST)


class EstadisticasView(APIView):
    def get(self, request):
        fecha_ini = request.query_params.get('fecha1')
        fecha_fin = request.query_params.get('fecha2')
        suc = request.query_params.get('sucursal')
        
        filters = {'estado': 'EXITOSA'}
        
        if fecha_ini and fecha_fin:
            try:
                fecha_ini = parse_datetime(fecha_ini)
                fecha_fin = parse_datetime(fecha_fin)
            except ValueError:
                return Response(
                    {"error": "Formato de fecha no válido"},
                    status=HTTP_400_BAD_REQUEST
                )

            if fecha_ini > fecha_fin:
                return Response(
                    {"error": "La fecha inicial no puede ser mayor que la fecha final"},
                    status=HTTP_400_BAD_REQUEST
                )

            filters['fecha_del_intercambio__range'] = (fecha_ini, fecha_fin)
        
        if suc:
            filters['publicacion_deseada__sucursal_destino_id'] = suc
        
        solicitudes = SolicitudDeIntercambio.objects.filter(**filters).order_by('publicacion_deseada__sucursal_destino', 'fecha_del_intercambio')
        
        serializer = SolicitudDeIntercambioSerializer(solicitudes, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
class DestacarProductoView(APIView):
    def patch(self, request, publicacion_id):
        publicacion = get_object_or_404(Publicacion, pk=publicacion_id)

        if publicacion.titulo == 'ultima demo':
            today = datetime.today()
            future_date = today + timedelta(seconds=20)
        else:
            today = datetime.today()
            future_date = today + timedelta(days=7)
        
        publicacion.fecha_fin_promocion = future_date
        publicacion.save()
        
        serializer = PublicacionSerializer(publicacion)
        return Response(serializer.data)


@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
class  ChequearPromosView(APIView):
    def patch(self, request):
        publicaciones = Publicacion.objects.filter(fecha_fin_promocion__isnull=False)
        today = timezone.now()
        for publicacion in publicaciones:
            if publicacion.fecha_fin_promocion < today:
                publicacion.fecha_fin_promocion = None
                user = publicacion.usuario_propietario
                contenido = f"La promoción de tu publicación {publicacion.titulo} se ha vencido!"
                Notificacion.objects.create(usuario=user, contenido=contenido)
                publicacion.save()
        return Response({"message": "Publicaciones actualizadas correctamente"})