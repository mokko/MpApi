"""
Since we have record.py now, I think we abandon this attempt


I am considering making a new class for moduleItems. These would represent
a single moduleItem.

I think we would could inherit from Module. Use the same data structure, just
additionally check that there is only one record. We could also have methods
that act on the items properties.

Alternatively, we make a new class that deals with fragments.

    i = Item (id=1234, attachment=True) #

    xml = "<systemField name="__orgUnit"><value>EMMusikethnologie</value></systemField>"
    fieldET = etree.fromstring(xml)

    i.append(fieldET)
    i.append2(type="dataField", value="value")
    i.append2(type="systemField", value="value")

  <moduleItem hasAttachments="true" id="503707">
    <systemField dataType="Long" name="__id">
      <value>503707</value>
    </systemField>
  ...
  </moduleItem>

inherit from Module,
but additionally make sure 
(a) make sure we have only one
"""
