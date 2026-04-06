from django.urls import path
from . import views

urlpatterns = [
    path('pacientes/', views.pacientes, name='pacientes'),
    path('pacientes/<int:id>/editar/', views.paciente_editar, name='paciente_editar'),
    path('pacientes/<int:id>/excluir/', views.paciente_excluir, name='paciente_excluir'),
    path('dados_paciente/', views.dados_paciente_listar, name="dados_paciente_listar"),
    path('dados_paciente/<str:id>/', views.dados_paciente, name="dados_paciente"),
    path('dados_paciente/<str:id>/meta/', views.paciente_peso_meta, name="paciente_peso_meta"),
    path('dados_paciente/<str:id>/anotacao/', views.anotacao_adicionar, name="anotacao_adicionar"),
    path('dados_paciente/<str:id>/exportar.csv', views.dados_paciente_export_csv, name="dados_paciente_export_csv"),
    path('grafico_peso/<str:id>/', views.grafico_peso, name="grafico_peso"),
    path('plano_alimentar_listar/', views.plano_alimentar_listar, name="plano_alimentar_listar"),
    path('plano_alimentar/<str:id>/', views.plano_alimentar, name="plano_alimentar"),
    path('refeicao/<str:id_paciente>/', views.refeicao, name="refeicao"),
    path('opcao/<str:id_paciente>/', views.opcao, name="opcao"),
]