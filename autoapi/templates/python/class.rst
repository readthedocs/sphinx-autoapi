.. class:: {{ object.name }}({{ object.args|join(',') }})

   {% if object.docstring %}

   .. rubric:: Summary

   {{ object.docstring|indent(3) }}

   {% endif %}

   {% if methods %}
   
   {% for method in methods %}

   {% macro render() %}{{ method.render() }}{% endmacro %}
   {{ render()|indent(3) }}
   
   {%- endfor %}

   {% endif %}
