{%- if obj.display %}

.. method:: {{ obj.name.split('.')[-1] }}({{ obj.args[1:]|join(',') }})

   {% if obj.docstring %}
   {{ obj.docstring.strip()|indent(3) }}
   {% endif %}

{% endif %}