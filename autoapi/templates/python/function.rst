{# Identention in this file is important #}

{% if is_method %}
{# Slice self off #}
.. method:: {{ fullname.split('.')[-1] }}({{ args[1:]|join(',') }})
{% else %}
.. function:: {{ fullname.split('.')[-1] }}({{ args|join(',') }})
{% endif %}

   {% if docstring %}
   {{ docstring|indent(3) }}
   {% endif %}


