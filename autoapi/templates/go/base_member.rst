.. go:{{ obj.ref_type }}:: {{ obj.name }}
{%- if obj.type == 'func' -%}
    {%- set argjoin = joiner(', ') -%}
    ({%- for param in obj.parameters -%}
        {{ argjoin() }}{{ param.name }} {{ param.type }}
    {%- endfor -%})
{%- endif %}

    {% macro render() %}{{ obj.docstring }}{% endmacro %}
    {{ render()|indent(4) }}

    {# Don't define parameter description here, that can be done in the block
    above #}
    {% for param in obj.parameters %}
    :type {{ param.name }}: {{ param.type }}
    {%- endfor %}
    {%- if obj.returns %}
    :rtype: {{ obj.returns.type }}
    {%- endif %}

    {% if obj.children -%}
        {%- for child in obj.children|sort %}
    {% macro render_child() %}{{ child.render() }}{% endmacro %}
    {{ render_child()|indent(4) }}
        {%- endfor %}
    {%- endif %}
