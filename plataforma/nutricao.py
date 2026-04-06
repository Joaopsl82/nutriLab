"""Cálculos nutricionais a partir de quantidades (g) e valores por 100 g."""

from decimal import Decimal

TOTAIS_ZERADOS = {
    'kcal': Decimal('0'),
    'carboidratos_g': Decimal('0'),
    'proteinas_g': Decimal('0'),
    'gorduras_g': Decimal('0'),
    'fibra_g': Decimal('0'),
    'sodio_mg': Decimal('0'),
    'calcio_mg': Decimal('0'),
    'ferro_mg': Decimal('0'),
}


def _f(x):
    if x is None:
        return 0.0
    return float(x)


def totais_por_itens(itens_qs):
    """
    itens_qs: queryset de ItemRefeicaoAlimento com select_related('alimento').
    Retorna totais ingeridos (não por 100g).
    """
    t = {
        'kcal': Decimal('0'),
        'carboidratos_g': Decimal('0'),
        'proteinas_g': Decimal('0'),
        'gorduras_g': Decimal('0'),
        'fibra_g': Decimal('0'),
        'sodio_mg': Decimal('0'),
        'calcio_mg': Decimal('0'),
        'ferro_mg': Decimal('0'),
    }
    for it in itens_qs:
        a = it.alimento
        fator = Decimal(it.quantidade_gramas) / Decimal('100')
        t['kcal'] += a.kcal_100g * fator
        t['carboidratos_g'] += a.carboidratos_g_100g * fator
        t['proteinas_g'] += a.proteinas_g_100g * fator
        t['gorduras_g'] += a.gorduras_g_100g * fator
        t['fibra_g'] += a.fibra_g_100g * fator
        t['sodio_mg'] += a.sodio_mg_100g * fator
        t['calcio_mg'] += a.calcio_mg_100g * fator
        t['ferro_mg'] += a.ferro_mg_100g * fator
    return t


def somar_totais(a, b):
    out = {}
    for k in a:
        out[k] = a[k] + b[k]
    return out


def percentuais_energia_macros(carb_g, prot_g, lip_g):
    """% da energia estimada a partir de macros (4/4/9 kcal/g)."""
    k_cho = _f(carb_g) * 4
    k_prot = _f(prot_g) * 4
    k_lip = _f(lip_g) * 9
    total = k_cho + k_prot + k_lip
    if total <= 0:
        return None
    return {
        'carboidratos': round(100 * k_cho / total, 1),
        'proteinas': round(100 * k_prot / total, 1),
        'gorduras': round(100 * k_lip / total, 1),
    }


def totais_legado_refeicao(refeicao):
    """Quando não há itens de alimento, usa os inteiros legados da refeição."""
    cho = Decimal(str(refeicao.carboidratos or 0))
    prot = Decimal(str(refeicao.proteinas or 0))
    lip = Decimal(str(refeicao.gorduras or 0))
    kcal = cho * Decimal('4') + prot * Decimal('4') + lip * Decimal('9')
    return {
        'kcal': kcal,
        'carboidratos_g': cho,
        'proteinas_g': prot,
        'gorduras_g': lip,
        'fibra_g': Decimal('0'),
        'sodio_mg': Decimal('0'),
        'calcio_mg': Decimal('0'),
        'ferro_mg': Decimal('0'),
    }


def totais_refeicao_mostrados(refeicao, itens_list):
    if not itens_list:
        return totais_legado_refeicao(refeicao)
    return totais_por_itens(itens_list)


def sincronizar_macros_refeicao_legacy(refeicao):
    """Atualiza campos inteiros legados da Refeição com a soma dos alimentos (0 se não houver itens)."""
    from .models import ItemRefeicaoAlimento

    itens = ItemRefeicaoAlimento.objects.filter(refeicao=refeicao).select_related('alimento')
    if not itens.exists():
        refeicao.carboidratos = 0
        refeicao.proteinas = 0
        refeicao.gorduras = 0
        refeicao.save(update_fields=['carboidratos', 'proteinas', 'gorduras'])
        return
    t = totais_por_itens(itens)
    refeicao.carboidratos = int(round(_f(t['carboidratos_g'])))
    refeicao.proteinas = int(round(_f(t['proteinas_g'])))
    refeicao.gorduras = int(round(_f(t['gorduras_g'])))
    refeicao.save(update_fields=['carboidratos', 'proteinas', 'gorduras'])
