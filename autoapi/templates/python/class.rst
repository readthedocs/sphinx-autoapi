{%- if obj.display %}

.. py:{{ obj.type }}:: {{ obj.short_name }}{% if obj.args %}({{ obj.args }}){% endif %}

   {%- if obj.bases %}

   Bases: {%- for base in obj.bases %}:class:`{{ base }}`{%- if not loop.last %}, {% endif %}{% endfor %}

   {% endif %}

   {%- if obj.docstring %}

   {{ obj.docstring|prepare_docstring|indent(3) }}

   {% endif %}

   {%- for attribute in obj.attributes %}

   {{ attribute.rendered|indent(3) }}

   {% endfor %}

   {%- for method in obj.methods %}

   {{ method.rendered|indent(3) }}

   {%- endfor %}

{% endif %}
