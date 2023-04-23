{% if obj.display %}
{{ md_fence + "{py:" + obj.type + "} " + obj.name }}
   {%- if obj.annotation is not none %}

   :type: {%- if obj.annotation %} {{ obj.annotation }}{%- endif %}

   {%- endif %}

   {%- if obj.value is not none %}

   :value: {% if obj.value is string and obj.value.splitlines()|count > 1 -%}
                Multiline-String

   {{ md_fence }}{raw} html

       <details><summary>Show Value</summary>
   {{ md_fence }}

   ```python
   """{{ obj.value|indent(width=8,blank=true) }}"""
   ```

   {{ md_fence }}{raw} html

       </details>
   {{ md_fence }}
           {%- else -%}
             {{ "%r" % obj.value|string|truncate(100) }}
           {%- endif %}
   {%- endif %}


   {{ obj.docstring|indent(3) }}
{{ md_fence }}
{% endif %}
