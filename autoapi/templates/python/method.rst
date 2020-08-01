{%- if obj.display %}
{% if sphinx_version >= (2, 1) %}
.. method:: {{ obj.short_name }}({{ obj.args }}){% if obj.return_annotation is not none %} -> {{ obj.return_annotation }}{% endif %}
   {% if obj.properties %}

   {% for property in obj.properties %}
   :{{ property }}:
   {% endfor %}
   {% else %}

   {% endif %}
{% else %}
.. {{ obj.method_type }}:: {{ obj.short_name }}({{ obj.args }})

{% endif %}

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}
{% endif %}
