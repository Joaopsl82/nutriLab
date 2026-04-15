from django.urls import path
from . import views

urlpatterns = [
    path('pacientes/', views.pacientes, name='pacientes'),
    path('pacientes/<int:id>/editar/', views.paciente_editar, name='paciente_editar'),
    path('pacientes/<int:id>/excluir/', views.paciente_excluir, name='paciente_excluir'),
    path('dados_paciente/', views.dados_paciente_listar, name="dados_paciente_listar"),
    path('dados_paciente/<str:id>/', views.dados_paciente, name="dados_paciente"),
    path(
        'dados_paciente/<str:id>/dado/<int:dado_id>/editar/',
        views.dado_clinico_editar,
        name='dado_clinico_editar',
    ),
    path(
        'dados_paciente/<str:id>/dado/<int:dado_id>/excluir/',
        views.dado_clinico_excluir,
        name='dado_clinico_excluir',
    ),
    path('dados_paciente/<str:id>/meta/', views.paciente_peso_meta, name="paciente_peso_meta"),
    path('dados_paciente/<str:id>/anamnese/', views.anamnese_adicionar, name='anamnese_adicionar'),
    path(
        'dados_paciente/<str:id>/anamnese/<int:ficha_id>/editar/',
        views.anamnese_editar,
        name='anamnese_editar',
    ),
    path(
        'dados_paciente/<str:id>/anamnese/<int:ficha_id>/excluir/',
        views.anamnese_excluir,
        name='anamnese_excluir',
    ),
    path(
        'dados_paciente/<str:id>/avaliacao/nova/',
        views.avaliacao_antropometrica_nova,
        name='avaliacao_antropometrica_nova',
    ),
    path(
        'dados_paciente/<str:id>/avaliacao/<int:av_id>/editar/',
        views.avaliacao_antropometrica_editar,
        name='avaliacao_antropometrica_editar',
    ),
    path(
        'dados_paciente/<str:id>/avaliacao/<int:av_id>/excluir/',
        views.avaliacao_antropometrica_excluir,
        name='avaliacao_antropometrica_excluir',
    ),
    path(
        'dados_paciente/<str:id>/gasto/nova/',
        views.gasto_energetico_nova,
        name='gasto_energetico_nova',
    ),
    path(
        'dados_paciente/<str:id>/gasto/<int:ge_id>/editar/',
        views.gasto_energetico_editar,
        name='gasto_energetico_editar',
    ),
    path(
        'dados_paciente/<str:id>/gasto/<int:ge_id>/excluir/',
        views.gasto_energetico_excluir,
        name='gasto_energetico_excluir',
    ),
    path('dados_paciente/<str:id>/anotacao/', views.anotacao_adicionar, name="anotacao_adicionar"),
    path(
        'dados_paciente/<str:id>/anotacao/<int:anotacao_id>/editar/',
        views.anotacao_editar,
        name='anotacao_editar',
    ),
    path(
        'dados_paciente/<str:id>/anotacao/<int:anotacao_id>/excluir/',
        views.anotacao_excluir,
        name='anotacao_excluir',
    ),
    path('dados_paciente/<str:id>/exportar.csv', views.dados_paciente_export_csv, name="dados_paciente_export_csv"),
    path('grafico_peso/<str:id>/', views.grafico_peso, name="grafico_peso"),
    path('plano_alimentar_listar/', views.plano_alimentar_listar, name="plano_alimentar_listar"),
    path('plano_alimentar/<str:id>/', views.plano_alimentar, name="plano_alimentar"),
    path(
        'plano_alimentar/<str:id_paciente>/item/adicionar/',
        views.item_refeicao_adicionar,
        name='item_refeicao_adicionar',
    ),
    path(
        'plano_alimentar/<str:id_paciente>/item/<int:item_id>/remover/',
        views.item_refeicao_remover,
        name='item_refeicao_remover',
    ),
    path(
        'plano_alimentar/<str:id_paciente>/alimento/custom/',
        views.alimento_custom_criar,
        name='alimento_custom_criar',
    ),
    path(
        'plano_alimentar/<str:id_paciente>/refeicao/<int:refeicao_id>/editar/',
        views.refeicao_editar,
        name='refeicao_editar',
    ),
    path(
        'plano_alimentar/<str:id_paciente>/refeicao/<int:refeicao_id>/excluir/',
        views.refeicao_excluir,
        name='refeicao_excluir',
    ),
    path('refeicao/<str:id_paciente>/', views.refeicao, name="refeicao"),
    path('opcao/<str:id_paciente>/', views.opcao, name="opcao"),
    path(
        'plano_alimentar/<str:id_paciente>/opcao/<int:opcao_id>/editar/',
        views.opcao_editar,
        name='opcao_editar',
    ),
    path(
        'plano_alimentar/<str:id_paciente>/opcao/<int:opcao_id>/excluir/',
        views.opcao_excluir,
        name='opcao_excluir',
    ),
]