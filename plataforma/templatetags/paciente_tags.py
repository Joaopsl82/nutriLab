from django import template

register = template.Library()


@register.inclusion_tag('plataforma/tags/paciente_avatar.html')
def paciente_avatar(paciente, size=120, extra_class=''):
    try:
        s = int(size)
    except (TypeError, ValueError):
        s = 120
    return {'paciente': paciente, 'size': s, 'extra_class': extra_class}
