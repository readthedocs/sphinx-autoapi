{%- if obj.display %}

.. function:: {{ obj.name }}({{ obj.args|join(',') }})

   {% if obj.docstring %}
   {{ obj.docstring.strip()|indent(3) }}
   {% endif %}

{% endif %}