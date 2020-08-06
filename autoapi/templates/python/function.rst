{% if obj.display %}
{% for (args, return_annotation) in obj.signatures %}
{% if loop.index0 == 0 %}
.. function:: {{ obj.short_name }}({{ args }}){% if return_annotation is not none %} -> {{ return_annotation }}{% endif %}

{% else %}
              {{ obj.short_name }}({{ args }}){% if return_annotation is not none %} -> {{ return_annotation }}{% endif %}

{% endif %}
{% endfor %}
   {% if sphinx_version >= (2, 1) %}
   {% for property in obj.properties %}
   :{{ property }}:
   {% endfor %}
   {% endif %}

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% else %}
   {% endif %}
{% endif %}
