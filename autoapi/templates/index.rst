Sphinx AutoAPI Index
####################

This page is the top-level of your generated API documentation.
Below is a list of all items that are documented here.

.. toctree::
   :includehidden:
   :glob:
   :maxdepth: 1

   {%- for page in pages|sort %}
   {% if page.top_level_object %}
   /autoapi/{{ page.id.split('.')|join('/') }}/index
   {% endif %}
   {%- endfor %}
