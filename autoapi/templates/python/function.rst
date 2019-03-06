{% if obj.display %}
.. function:: {{ obj.short_name }}({{ obj.args }})

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}
{% endif %}
