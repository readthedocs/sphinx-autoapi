{%- if obj.display %}
{% if sphinx_version >= (2, 1) %}
.. method:: {{ obj.short_name }}({{ obj.args }})
   {% for property in obj.properties %}
   :{{ property }}:
   {% endfor %}

{% else %}
.. {{ obj.method_type }}:: {{ obj.short_name }}({{ obj.args }})
{% endif %}

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}
{% endif %}
