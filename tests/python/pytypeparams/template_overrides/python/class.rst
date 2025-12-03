.. py:class:: {{ obj.short_name }}[{{obj.type_params}}]
              
    {% if obj.bases %}
    Bases: {% for base in obj.bases %}{{ base|link_objs }}{% if not loop.last %}, {% endif %}{% endfor %}
    {% endif %}

{% set visible_attrs = obj.children|selectattr("display")|selectattr("type", "equalto", "attribute")|list %}
   {% for obj_item in visible_attrs %}

   {{ obj_item.render()|indent(3) }}
   {% endfor %}
    
{% set visible_methods = obj.children|selectattr("display")|selectattr("type", "equalto", "method")|list %}

   {% for obj_item in visible_methods %}

   {{ obj_item.render()|indent(3) }}
   {% endfor %}

   
