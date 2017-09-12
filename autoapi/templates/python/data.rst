.. {{ obj.type }}:: {{ obj.name }}
   {% if obj.value is not none %}:annotation: = {{ obj.value|pprint }} {% endif %}

   {{ obj.docstring|prepare_docstring|indent(3) }}

