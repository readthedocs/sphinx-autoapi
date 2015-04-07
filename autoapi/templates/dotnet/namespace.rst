{{ name }}
{{ underline }}

Modules
-------

.. toctree::
   {% for obj in objs %} 
   {{ name }}/{{ obj.name.CSharp }} {% endfor %}

