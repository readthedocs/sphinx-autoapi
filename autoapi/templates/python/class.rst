{% if obj.display %}
.. py:{{ obj.type }}:: {{ obj.short_name }}{% if obj.args %}({{ obj.args }}){% endif %}


   {% if obj.bases %}
   Bases: {% for base in obj.bases %}:class:`{{ base }}`{% if not loop.last %}, {% endif %}{% endfor %}


   {% if include_inheritance_graphs and obj.bases != ["object"] %}
   .. autoapi-inheritance-diagram:: {{ obj.obj["full_name"] }}
      :parts: 1
      {% if include_private_inheritance %}:private-bases:{% endif %}

   {% endif %}
   {% endif %}
   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}
   {% set visible_classes = obj.classes|selectattr("display")|list %}
   {% for klass in visible_classes %}
   {{ klass.rendered|indent(3) }}
   {% endfor %}
   {% set visible_attributes = obj.attributes|selectattr("display")|list %}
   {% for attribute in visible_attributes %}
   {{ attribute.rendered|indent(3) }}
   {% endfor %}
   {% set visible_methods = obj.methods|selectattr("display")|list %}
   {% for method in visible_methods %}
   {{ method.rendered|indent(3) }}
   {% endfor %}
{% endif %}
