{%- if obj.display %}

.. function:: {{ obj.short_name }}({{ obj.args|join(',') }})

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}

{% endif %}
