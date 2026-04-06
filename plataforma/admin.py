from django.contrib import admin
from django.db.models import Q

from .models import (
    AlimentoNutricional,
    DadosPaciente,
    ItemRefeicaoAlimento,
    Opcao,
    Pacientes,
    Refeicao,
)


@admin.register(Pacientes)
class PacientesAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'nutri', 'situacao')
    list_filter = ('situacao',)
    search_fields = ('nome', 'email', 'telefone')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(nutri=request.user)

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if not request.user.is_superuser:
            return [f for f in fields if f != 'nutri']
        return fields

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not change:
            obj.nutri = request.user
        super().save_model(request, obj, form, change)


class _PacienteDoNutriAdminMixin:
    """Restringe listagens e FKs ao nutricionista autenticado (exceto superuser)."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(paciente__nutri=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'paciente' and not request.user.is_superuser:
            kwargs['queryset'] = Pacientes.objects.filter(nutri=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DadosPaciente)
class DadosPacienteAdmin(_PacienteDoNutriAdminMixin, admin.ModelAdmin):
    list_display = ('paciente', 'data', 'peso')
    list_filter = ('data',)
    search_fields = ('paciente__nome', 'paciente__email')


class ItemRefeicaoAlimentoInline(admin.TabularInline):
    model = ItemRefeicaoAlimento
    extra = 0
    raw_id_fields = ('alimento',)


@admin.register(Refeicao)
class RefeicaoAdmin(_PacienteDoNutriAdminMixin, admin.ModelAdmin):
    list_display = ('titulo', 'paciente', 'horario')
    search_fields = ('titulo', 'paciente__nome')
    inlines = [ItemRefeicaoAlimentoInline]


@admin.register(Opcao)
class OpcaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'descricao', 'refeicao')
    search_fields = ('titulo', 'descricao', 'refeicao__titulo')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(refeicao__paciente__nutri=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'refeicao' and not request.user.is_superuser:
            kwargs['queryset'] = Refeicao.objects.filter(paciente__nutri=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AlimentoNutricional)
class AlimentoNutricionalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'nutri', 'eh_prato', 'kcal_100g')
    list_filter = ('eh_prato',)
    search_fields = ('nome',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(nutri__isnull=True) | Q(nutri=request.user))
