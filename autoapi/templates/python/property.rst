{%- if obj.display %}
{% if is_own_page %}
{{ obj.name }}
{{ "=" * obj.name | length }}

{% endif %}
.. py:property:: {{ obj.short_name }}
   {% if obj.annotation %}
   :type: {{ obj.annotation }}
   {% endif %}
   {% if obj.properties %}
   {% for property in obj.properties %}
   :{{ property }}:
   {% endfor %}
   {% endif %}

   {% if obj.docstring %}
   {{ obj.docstring|indent(3) }}
   {% endif %}
{% endif %}
