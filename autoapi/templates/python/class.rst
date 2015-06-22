{{ obj.short_name }}
{{ "-" * obj.short_name|length }}

.. py:class:: {{ obj.short_name }}{% if obj.args %}({{ obj.args|join(',') }}){% endif %}

   {%- if obj.inheritance %}

   .. rubric:: Imports

   {% for import in obj.inheritance %}
   * {{ import }}
   {% endfor %}

   {% endif %}

   {%- if obj.docstring %}

   .. rubric:: Summary

   {{ obj.docstring|indent(3) }}

   {% endif %}

   {%- if obj.methods %}
   
   {%- for method in obj.methods %}

   {{ method.rendered|indent(3) }}
   
   {%- endfor %}

   {% endif %}

   {% block content %}
   {%- for obj_item in obj.children %}

   {{ obj_item.rendered|indent(3) }}

   {%- endfor %}
   {% endblock %}
