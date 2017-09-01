.. py:class:: {{ obj.short_name }}{% if obj.args %}({{ obj.args[1:]|join(',') }}){% endif %}

   {%- if obj.docstring %}

   {{ obj.docstring|prepare_docstring|indent(3) }}

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
