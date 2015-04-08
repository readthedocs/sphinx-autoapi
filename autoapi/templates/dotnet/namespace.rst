{{ name.CSharp }}
{{ underline }}

Modules
```````

.. toctree::
   {% for obj in items %} 
   {% set ns = id.split('.')[0] %}
   /autoapi/{{ obj.type }}/{{ obj.id.split('.')[-1] }} {% endfor %}

