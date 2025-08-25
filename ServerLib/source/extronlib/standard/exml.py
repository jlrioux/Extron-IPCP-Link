import xml as exml
"""
    This is a restricted version of standard Python xml modules. It provides the same classes and functions.

    ---

    Adapting the example from [docs.python.org](docs.python.org):

    ```

    import extronlib.standard.exml.etree.ElementTree as ET

    country_data_as_string = \"\"\"
    <?xml version="1.0"?>
    <data>
        <country name="Liechtenstein">
            -    <rank>1</rank>
            -    <year>2008</year>
            -    <gdppc>141100</gdppc>
            -    <neighbor name="Austria" direction="E"/>
            -    <neighbor name="Switzerland" direction="W"/>
        </country>
        <country name="Singapore">
            -    <rank>4</rank>
            -    <year>2011</year>
            -    <gdppc>59900</gdppc>
            -    <neighbor name="Malaysia" direction="N"/>
        </country>
        <country name="Panama">
            -    <rank>68</rank>
            -    <year>2011</year>
            -    <gdppc>13600</gdppc>
            -    <neighbor name="Costa Rica" direction="W"/>
            -    <neighbor name="Colombia" direction="E"/>
        </country>
    </data>
    \"\"\"

    root = ET.fromstring(country_data_as_string)
    print(root.tag)
    ```
"""
