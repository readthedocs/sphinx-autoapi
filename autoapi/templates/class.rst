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

.. class:: {{ name.CSharp }}

   {% if ctors %}
   
   .. rubric:: Constructors

   {% for item in ctors %}
      {% include "member.rst" %}
   {%- endfor %}
   {% endif %}


   {% block methods %}

   {% if methods %}
   
   .. rubric:: Methods

   {% for item in methods %}
      {% include "member.rst" %}
   {%- endfor %}
   {% endif %}
   {% endblock %}



   {% block attributes %}
   {% if attributes %}

   .. rubric:: Attributes

   {% for item in attributes %}
      {% include "member.rst" %}
   {%- endfor %}
   {% endif %}
   {% endblock %}
