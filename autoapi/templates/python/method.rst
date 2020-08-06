{%- if obj.display %}
{% if sphinx_version >= (2, 1) %}
{% for (args, return_annotation) in obj.signatures %}
{% if loop.index0 == 0 %}
.. method:: {{ obj.short_name }}({{ args }}){% if return_annotation is not none %} -> {{ return_annotation }}{% endif %}

{% else %}
            {{ obj.short_name }}({{ args }}){% if return_annotation is not none %} -> {{ return_annotation }}{% endif %}

{% endif %}
{% endfor %}
   {% if obj.properties %}
   {% for property in obj.properties %}
   :{{ property }}:
   {% endfor %}

   {% else %}

   {% endif %}
{% else %}
{% for (args, return_annotation) in obj.signatures %}
{% if loop.index0 == 0 %}
.. {{ obj.method_type }}:: {{ obj.short_name }}({{ args }})

{% else %}
                        :: {{ obj.short_name }}({{ args }})

{% endif %}
{% endfor %}
{% endif %}
   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}
{% endif %}
