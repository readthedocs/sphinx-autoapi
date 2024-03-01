{% if obj.display %}
{% if is_own_page %}
{{ obj.name }}
{{ "=" * obj.name | length }}
{% endif %}

.. py:{{ obj.type }}:: {{ obj.short_name }}{% if obj.args %}({{ obj.args }}){% endif %}

{% for (args, return_annotation) in obj.overloads %}
      {{ " " * (obj.type | length) }}   {{ obj.short_name }}{% if args %}({{ args }}){% endif %}

{% endfor %}


   {% if obj.bases %}
   {% if "show-inheritance" in autoapi_options %}
   Bases: {% for base in obj.bases %}{{ base|link_objs }}{% if not loop.last %}, {% endif %}{% endfor %}
   {% endif %}


   {% if "show-inheritance-diagram" in autoapi_options and obj.bases != ["object"] %}
   .. autoapi-inheritance-diagram:: {{ obj.obj["full_name"] }}
      :parts: 1
      {% if "private-members" in autoapi_options %}
      :private-bases:
      {% endif %}

   {% endif %}
   {% endif %}
   {% if obj.docstring %}
   {{ obj.docstring|indent(3) }}
   {% endif %}
   {# TODO: Rendering of all children below this line must be conditional on own_page_types #}
   {% if "inherited-members" in autoapi_options %}
   {% set visible_classes = obj.classes|selectattr("display")|list %}
   {% else %}
   {% set visible_classes = obj.classes|rejectattr("inherited")|selectattr("display")|list %}
   {% endif %}
   {% for klass in visible_classes %}
   {{ klass.render(own_page_types=[])|indent(3) }}
   {% endfor %}
   {% if "inherited-members" in autoapi_options %}
   {% set visible_properties = obj.properties|selectattr("display")|list %}
   {% else %}
   {% set visible_properties = obj.properties|rejectattr("inherited")|selectattr("display")|list %}
   {% endif %}
   {% if "property" in own_page_types and visible_properties %}

   Properties
   ----------

   .. toctree::
      :hidden:

      {% for property in visible_properties %}
      {{ property.name }}
      {% endfor %}
   {% else %}
   {% for property in visible_properties %}
   {{ property.render()|indent(3) }}
   {% endfor %}
   {% endif %}
   {% if "inherited-members" in autoapi_options %}
   {% set visible_attributes = obj.attributes|selectattr("display")|list %}
   {% else %}
   {% set visible_attributes = obj.attributes|rejectattr("inherited")|selectattr("display")|list %}
   {% endif %}
   {% if "attribute" in own_page_types and visible_attributes %}

   Attributes
   ----------

   .. toctree::
      :hidden:

      {% for attribute in visible_attributes %}
      {{ attribute.name }}
      {% endfor %}
   {% else %}
   {% for attribute in visible_attributes %}
   {{ attribute.render()|indent(3) }}
   {% endfor %}
   {% endif %}
   {% if "inherited-members" in autoapi_options %}
   {% set visible_methods = obj.methods|selectattr("display")|list %}
   {% else %}
   {% set visible_methods = obj.methods|rejectattr("inherited")|selectattr("display")|list %}
   {% endif %}
   {% if "method" in own_page_types and visible_methods %}

   Methods
   -------

   .. toctree::
      :hidden:

      {% for method in visible_methods %}
      {{ method.name }}
      {% endfor %}
   {% else %}
   {% for method in visible_methods %}
   {{ method.render()|indent(3) }}
   {% endfor %}
   {% endif %}
{% endif %}
