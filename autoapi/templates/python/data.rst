{% if obj.display %}
.. {{ obj.type }}:: {{ obj.name }}
   {%+ if obj.value is not none %}:annotation: = {{ obj.value }}{% endif %}


   {{ obj.docstring|prepare_docstring|indent(3) }}
{% endif %}
