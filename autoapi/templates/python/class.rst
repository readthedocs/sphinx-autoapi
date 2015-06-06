.. py:class:: {{ obj.name }}{% if obj.args %}({{ obj.args|join(',') }}){% endif %}

   {% if obj.docstring %}

   .. rubric:: Summary

   {{ obj.docstring|indent(3) }}

   {% endif %}

   {% if obj.methods %}
   
   {% for method in obj.methods %}

   {% macro render() %}{{ method.render() }}{% endmacro %}
   {{ render()|indent(3) }}
   
   {%- endfor %}

   {% endif %}
   

   {% block content %}
   {%- for obj_item in obj.children|sort %}

   {% macro render() %}{{ obj_item.render() }}{% endmacro %}
   {{ render()|indent(0) }}

   {%- endfor %}
   {% endblock %}

