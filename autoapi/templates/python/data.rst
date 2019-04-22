{% if obj.display %}
.. {{ obj.type }}:: {{ obj.name }}
   {%+ if obj.value is not none or obj.annotation is not none %}:annotation:{% if obj.annotation %} :{{ obj.annotation }}{% endif %}{% if obj.value is not none %} = {{ obj.value }}{% endif %}{% endif %}


   {{ obj.docstring|prepare_docstring|indent(3) }}
{% endif %}
