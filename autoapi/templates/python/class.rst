.. class:: {{ fullname }}({{ args|join(',') }})

   {% if docstring %}

   .. rubric:: Summary

   {{ docstring|indent(3) }}

   {% endif %}

   {% if methods %}
   
   {% for class in classes %}
   {% macro render() %}{{ class.render() }}{% endmacro %}
   {{ render()|indent(3) }}
   {%- endfor %}
   
   {% endif %}

   {% if methods %}
   
   {% for method in methods %}

   {% macro render() %}{{ method.render() }}{% endmacro %}
   {{ render()|indent(3) }}
   
   {%- endfor %}

   {% endif %}
