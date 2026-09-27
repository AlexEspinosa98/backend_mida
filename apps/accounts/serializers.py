from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import PerfilUsuario

Usuario = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """CRUD de usuarios, exclusivo de EsSuperadmin (ver UsuarioAdminViewSet). La contraseña solo
    se acepta al CREAR -- para cambiarla después de creado el usuario está el action aparte
    `cambiar-password` (ver CambiarPasswordSerializer), nunca este mismo serializer en un update,
    para no dejar la contraseña viajando por accidente en un PATCH normal de "editar mis datos"."""

    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    rol = serializers.ChoiceField(choices=PerfilUsuario.Rol.choices, source="perfil.rol")

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "email", "first_name", "last_name", "is_active", "rol", "password",
            "date_joined",
        ]
        read_only_fields = ["date_joined"]

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Obligatoria al crear un usuario."})
        return attrs

    def create(self, validated_data):
        perfil_data = validated_data.pop("perfil")
        password = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        PerfilUsuario.objects.create(user=usuario, rol=perfil_data["rol"])
        return usuario

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop("perfil", None)
        # password nunca llega en un update (ver validate/Meta: write_only + solo obligatoria al
        # crear) -- si alguien la manda igual acá, se ignora a propósito, no se aplica callado.
        validated_data.pop("password", None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.save()
        if perfil_data:
            PerfilUsuario.objects.update_or_create(
                user=instance, defaults={"rol": perfil_data["rol"]}
            )
        return instance


class CambiarPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, validators=[validate_password])
