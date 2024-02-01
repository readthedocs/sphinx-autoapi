{% if obj.display %}
   {% if is_own_page %}
:py:mod:`{{ obj.name }}`
=========={{ "=" * obj.name|length }}

   {% endif %}
.. py:module:: {{ obj.name }}

   {% if obj.docstring %}
.. autoapi-nested-parse::

   {{ obj.docstring|indent(3) }}

   {% endif %}

   {% block subpackages %}
      {% set visible_subpackages = obj.subpackages|selectattr("display")|list %}
      {% if visible_subpackages %}
Subpackages
-----------
.. toctree::
   :hidden:

         {% for subpackage in visible_subpackages %}
   {{ subpackage.short_name }}/index.rst
         {% endfor %}

.. autoapisummary::

         {% for subpackage in visible_subpackages %}
   {{ subpackage.id }}
         {% endfor %}


      {% endif %}
   {% endblock %}
   {% block submodules %}
      {% set visible_submodules = obj.submodules|selectattr("display")|list %}
      {% if visible_submodules %}
         {% if "module" in own_page_types %}
Submodules
----------
.. toctree::
   :hidden:

            {% for submodule in visible_submodules %}
   {{ submodule.short_name }}/index.rst
            {% endfor %}

.. autoapisummary::

            {% for submodule in visible_submodules %}
   {{ submodule.id }}
            {% endfor %}
         {% else %}
            {% for submodule in visible_submodules %}
   {{ submodule.render() }}
            {% endfor %}
         {% endif %}


      {% endif %}
   {% endblock %}
   {% block content %}
      {% if obj.all is not none %}
         {% set visible_children = obj.children|selectattr("short_name", "in", obj.all)|list %}
      {% elif obj.type is equalto("package") %}
         {% set visible_children = obj.children|selectattr("display")|list %}
      {% else %}
         {% set visible_children = obj.children|selectattr("display")|rejectattr("imported")|list %}
      {% endif %}
      {% if visible_children %}
         {% if is_own_page %}
            {% set visible_attributes = visible_children|selectattr("type", "equalto", "data")|list %}
            {% if visible_attributes %}
               {% if "attribute" in own_page_types or "show-module-summary" in autoapi_options %}
Attributes
----------
                  {% if "attribute" in own_page_types %}
.. toctree::
   :hidden:

                     {% for attribute in visible_attributes %}
   {{ attribute.short_name }}
                     {% endfor %}

                  {% endif%}
.. autoapisummary::

                  {% for attribute in visible_attributes %}
   {{ attribute.id }}
                  {% endfor %}
               {% endif %}


            {% endif %}
            {% set visible_exceptions = visible_children|selectattr("type", "equalto", "exception")|list %}
            {% if visible_exceptions %}
               {% if "exception" in own_page_types or "show-module-summary" in autoapi_options %}
Exceptions
----------
                  {% if "exception" in own_page_types %}
.. toctree::
   :hidden:

                     {% for exception in visible_exceptions %}
   {# 
       The set own_page_types sometimes is not ordered! This changes the value of
       its last element. Thus, the best way to check is to verify if 'function'
       lies within the list
       Do -> if 'function' not in own_page_types
       Instead of -> if "class" == (own_page_types | list | last)
   #}
   {% if "method" not in own_page_types %}
   {{ exception.short_name }}.rst
   {% else %}
   {{ exception.short_name }}/index.rst
   {% endif %}
                     {% endfor %}

                  {% endif %}
.. autoapisummary::

                  {% for exception in visible_exceptions %}
   {{ exception.id }}
                  {% endfor %}
               {% endif %}


            {% endif %}
            {% set visible_classes = visible_children|selectattr("type", "equalto", "class")|list %}
            {% if visible_classes %}
               {% if "class" in own_page_types or "show-module-summary" in autoapi_options %}
Classes
-------
                  {% if "class" in own_page_types %}
.. toctree::
   :hidden:

                     {% for klass in visible_classes %}
   {# 
       The set own_page_types sometimes is not ordered! This changes the value of
       its last element. Thus, the best way to check is to verify if 'function'
       lies within the list
       Do -> if 'function' not in own_page_types
       Instead of -> if "class" == (own_page_types | list | last)
   #}
   {% if "method" not in own_page_types %}
   {{ klass.short_name }}.rst
   {% else %}
   {{ klass.short_name }}/index.rst
   {% endif %}
                     {% endfor %}

                  {% endif %}
.. autoapisummary::

                  {% for klass in visible_classes %}
   {{ klass.id }}
                  {% endfor %}
               {% endif %}


            {% endif %}
            {% set visible_functions = visible_children|selectattr("type", "equalto", "function")|list %}
            {% if visible_functions %}
               {% if "function" in own_page_types or "show-module-summary" in autoapi_options %}
Functions
---------
                  {% if "function" in own_page_types %}
.. toctree::
   :hidden:

                     {% for function in visible_functions %}
   {{ function.short_name }}.rst
                     {% endfor %}

                  {% endif %}
.. autoapisummary::

                  {% for function in visible_functions %}
   {{ function.id }}
                  {% endfor %}
               {% endif %}


            {% endif %}
{{ obj.type|title }} Contents
{{ "-" * obj.type|length }}---------

            {% for obj_item in visible_children %}
               {% if obj_item.type not in own_page_types %}
{{ obj_item.render()|indent(0) }}
               {% endif %}
            {% endfor %}
         {% else %}
            {# If this is not its own page, the children won't have their own page either. #}
            {# So render them as normal, without needing to check if they have their own page. #}
            {% for obj_item in visible_children %}
   {{ obj_item.render()|indent(3) }}
            {% endfor %}
         {% endif %}
      {% endif %}
   {% endblock %}
{% endif %}
