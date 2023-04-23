{%- if obj.display %}
{{ md_fence }}{py:property} {{ obj.short_name }}
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
{{ md_fence }}
{% endif %}
