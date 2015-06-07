{# Identention in this file is important #}

{% if is_method %}
{# Slice self off #}
.. method:: {{ obj.name.split('.')[-1] }}({{ args[1:]|join(',') }})
{% else %}
.. function:: {{ obj.name.split('.')[-1] }}({{ args|join(',') }})
{% endif %}

   {% if obj.docstring %}
   {{ obj.docstring|indent(3) }}
   {% endif %}


