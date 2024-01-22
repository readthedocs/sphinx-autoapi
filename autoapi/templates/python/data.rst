{% if obj.display %}
   {% if is_own_page %}
:py:{{ obj.type|truncate(4, True, "", 0) }}:`{{ obj.id }}`
==========={{ "=" * obj.id | length }}

   {% endif %}
.. py:{{ obj.type }}:: {% if is_own_page %}{{ obj.id }}{% else %}{{ obj.name }}{% endif %}
   {% if obj.annotation is not none %}

   :type: {% if obj.annotation %} {{ obj.annotation }}{% endif %}
   {% endif %}
   {% if obj.value is not none %}

      {% if obj.value is string and obj.value.splitlines()|count > 1 %}
   :value: Multiline-String

   .. raw:: html

      <details><summary>Show Value</summary>

   .. code-block:: python

      """{{ obj.value|indent(width=6,blank=true) }}"""

   .. raw:: html

      </details>

      {% else %}
         {% if obj.value is string %}
   :value: {{ "%r" % obj.value|string|truncate(100) }}
         {% else %}
   :value: {{ obj.value|string|truncate(100) }}
         {% endif %}
      {% endif %}
   {% endif %}

   {% if obj.docstring %}

   {{ obj.docstring|indent(3) }}
   {% endif %}
{% endif %}
