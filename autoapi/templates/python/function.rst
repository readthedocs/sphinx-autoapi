{% if obj.display %}
.. function:: {{ obj.short_name }}({{ obj.args }}){% if obj.return_annotation is not none %} -> {{ obj.return_annotation }}{% endif %}

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}
{% endif %}
