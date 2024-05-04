from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    def __str__(self):
        return self.nombre

class Usuario(AbstractUser):
    reputacion = models.IntegerField(null=True, default=0)
    fecha_de_nacimiento = models.DateField(auto_now_add=True)
    sucursal_favorita = models.ForeignKey(Sucursal, related_name="usuarios", null=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150, unique=False)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'fecha_de_nacimiento', 'sucursal_favorita']
    def __str__(self):
        return self.username
    

class Publicacion(models.Model):
    usuario_propietario = models.ForeignKey(Usuario, related_name="publicaciones", on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.TextField()
    imagen = models.ImageField(null=True, blank=True)
    def __str__(self):
        return self.titulo
    # sucursal destino?

class Comentario(models.Model):
    contenido = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    publicacion = models.ForeignKey(Publicacion, related_name="comentarios", on_delete=models.CASCADE)
    usuario_propietario = models.ForeignKey(Usuario, related_name="comentarios", on_delete=models.CASCADE)
    respuesta = models.ForeignKey('self', related_name='respuestas', on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.usuario_propietario.username

class Solicitud(models.Model):
    publicacion_deseada = models.ForeignKey(Publicacion, related_name='solicitudes_recibidas', on_delete=models.CASCADE)
    publicacion_a_intercambiar = models.ForeignKey(Publicacion, related_name='solicitudes_enviadas', on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.publicacion_a_intercambiar.usuario_propietario

    
