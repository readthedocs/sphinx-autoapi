{{ name.CSharp }}
{{ underline }}

{#
.. currentmodule:: {{ module }}
#}

Summary
-------

{{ summary }}

Inheritance Hierarchy
---------------------

{% for item in inheritance %}
* {{ item.id }}
{% endfor %}

Syntax

.. code-block:: csharp

   {{ syntax.content.CSharp }}

Class Information
-----------------

.. dn:class:: {{ qualifiedName.CSharp }}


   {% if ctors %}
   
   {% for ctor in ctors %}

   {% macro render() %}{{ ctor.render() }}{% endmacro %}
   {{ render()|indent(3) }}
   
   {%- endfor %}

   {% endif %}


   {% if methods %}
   
   {% for method in methods %}

   {% macro render() %}{{ method.render() }}{% endmacro %}
   {{ render()|indent(3) }}
   
   {%- endfor %}

   {% endif %}



   {% if methods %}
   
   {% for method in attributes %}

   {% macro render() %}{{ method.render() }}{% endmacro %}
   {{ render()|indent(3) }}
   
   {%- endfor %}

   {% endif %}

