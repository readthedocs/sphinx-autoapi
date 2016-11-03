{%- if obj.display %}

.. method:: {{ obj.name }}({{ obj.args[1:]|join(',') }})

   {% if obj.docstring %}
   {{ obj.docstring|indent(3) }}
   {% endif %}

{% endif %}
