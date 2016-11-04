{%- if obj.display %}

.. method:: {{ obj.name }}({{ obj.args[1:]|join(',') }})

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}

{% endif %}
