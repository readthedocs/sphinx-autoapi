{# Identention in this file is important #}

{% if is_method %}
{# Slice self off #}
.. method:: {{ object.name.split('.')[-1] }}({{ args[1:]|join(',') }})
{% else %}
.. function:: {{ object.name.split('.')[-1] }}({{ args|join(',') }})
{% endif %}

   {% if object.docstring %}
   {{ object.docstring|indent(3) }}
   {% endif %}


