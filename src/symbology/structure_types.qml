<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" version="3.22.3-Białowieża" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" minScale="1e+08" maxScale="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal durationField="fid" startExpression="" fixedDuration="0" mode="0" accumulate="0" endExpression="" enabled="0" limitMode="0" endField="" durationUnit="min" startField="created">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <Option type="Map">
      <Option name="dualview/previewExpressions" type="List">
        <Option type="QString" value="&quot;name&quot;"/>
      </Option>
      <Option name="embeddedWidgets/count" type="QString" value="0"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <legend type="default-vector" showLabelLegend="0"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field configurationFlags="None" name="fid">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="name">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="mimics_id">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" type="bool" value="false"/>
            <Option name="AllowNull" type="bool" value="false"/>
            <Option name="Description" type="QString" value="&quot;description&quot;"/>
            <Option name="FilterExpression" type="QString" value=""/>
            <Option name="Key" type="QString" value="fid"/>
            <Option name="Layer" type="QString" value="Structure_Mimics_93e82b1d_40a9_45c3_a7ac_80f62015377d"/>
            <Option name="LayerName" type="QString" value="Structure Mimics"/>
            <Option name="LayerProviderName" type="QString" value="ogr"/>
            <Option name="LayerSource" type="QString" value="/Users/nick/Desktop/ztest/designs/designs.gpkg|layername=structure_mimics"/>
            <Option name="NofColumns" type="int" value="1"/>
            <Option name="OrderByValue" type="bool" value="false"/>
            <Option name="UseCompleter" type="bool" value="false"/>
            <Option name="Value" type="QString" value="name"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="construction_description">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="true"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="function_description">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="true"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_posts">
      <editWidget type="Range">
        <config>
          <Option type="Map">
            <Option name="AllowNull" type="bool" value="true"/>
            <Option name="Max" type="double" value="500"/>
            <Option name="Min" type="double" value="0"/>
            <Option name="Precision" type="int" value="0"/>
            <Option name="Step" type="double" value="1"/>
            <Option name="Style" type="QString" value="SpinBox"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_length">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_width">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_height">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="created">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="Structure Type ID" field="fid"/>
    <alias index="1" name="Structure Type Name" field="name"/>
    <alias index="2" name="Structure Mimics" field="mimics_id"/>
    <alias index="3" name="Construction Description" field="construction_description"/>
    <alias index="4" name="Function Description" field="function_description"/>
    <alias index="5" name="Typical Posts" field="typical_posts"/>
    <alias index="6" name="Typical Length" field="typical_length"/>
    <alias index="7" name="Typical Width" field="typical_width"/>
    <alias index="8" name="Typical Height" field="typical_height"/>
    <alias index="9" name="" field="created"/>
  </aliases>
  <defaults>
    <default applyOnUpdate="0" expression="" field="fid"/>
    <default applyOnUpdate="0" expression="" field="name"/>
    <default applyOnUpdate="0" expression="" field="mimics_id"/>
    <default applyOnUpdate="0" expression="" field="construction_description"/>
    <default applyOnUpdate="0" expression="" field="function_description"/>
    <default applyOnUpdate="0" expression="" field="typical_posts"/>
    <default applyOnUpdate="0" expression="" field="typical_length"/>
    <default applyOnUpdate="0" expression="" field="typical_width"/>
    <default applyOnUpdate="0" expression="" field="typical_height"/>
    <default applyOnUpdate="0" expression="" field="created"/>
  </defaults>
  <constraints>
    <constraint constraints="3" notnull_strength="1" unique_strength="1" exp_strength="0" field="fid"/>
    <constraint constraints="3" notnull_strength="1" unique_strength="1" exp_strength="0" field="name"/>
    <constraint constraints="1" notnull_strength="2" unique_strength="0" exp_strength="0" field="mimics_id"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="construction_description"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="function_description"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="typical_posts"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="typical_length"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="typical_width"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="typical_height"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="created"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="fid"/>
    <constraint exp="" desc="" field="name"/>
    <constraint exp="" desc="" field="mimics_id"/>
    <constraint exp="" desc="" field="construction_description"/>
    <constraint exp="" desc="" field="function_description"/>
    <constraint exp="" desc="" field="typical_posts"/>
    <constraint exp="" desc="" field="typical_length"/>
    <constraint exp="" desc="" field="typical_width"/>
    <constraint exp="" desc="" field="typical_height"/>
    <constraint exp="" desc="" field="created"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column name="fid" type="field" width="-1" hidden="0"/>
      <column name="name" type="field" width="137" hidden="0"/>
      <column name="mimics_id" type="field" width="100" hidden="0"/>
      <column name="construction_description" type="field" width="169" hidden="0"/>
      <column name="function_description" type="field" width="120" hidden="0"/>
      <column name="typical_posts" type="field" width="100" hidden="0"/>
      <column name="typical_length" type="field" width="87" hidden="0"/>
      <column name="typical_width" type="field" width="81" hidden="0"/>
      <column name="typical_height" type="field" width="85" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
      <column name="created" type="field" width="136" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>tablayout</editorlayout>
  <attributeEditorForm>
    <attributeEditorField showLabel="1" name="fid" index="0"/>
    <attributeEditorField showLabel="1" name="name" index="1"/>
    <attributeEditorField showLabel="1" name="mimics_id" index="2"/>
    <attributeEditorField showLabel="1" name="construction_description" index="3"/>
    <attributeEditorField showLabel="1" name="function_description" index="4"/>
    <attributeEditorField showLabel="1" name="typical_posts" index="5"/>
    <attributeEditorField showLabel="1" name="typical_length" index="6"/>
    <attributeEditorField showLabel="1" name="typical_width" index="7"/>
    <attributeEditorField showLabel="1" name="typical_height" index="8"/>
  </attributeEditorForm>
  <editable>
    <field name="construction_description" editable="1"/>
    <field name="created" editable="1"/>
    <field name="estimated_posts" editable="1"/>
    <field name="fid" editable="0"/>
    <field name="function_description" editable="1"/>
    <field name="mimics_id" editable="1"/>
    <field name="name" editable="1"/>
    <field name="structure_mimics" editable="1"/>
    <field name="structure_type_name" editable="1"/>
    <field name="typical_height" editable="1"/>
    <field name="typical_length" editable="1"/>
    <field name="typical_posts" editable="1"/>
    <field name="typical_width" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="construction_description" labelOnTop="1"/>
    <field name="created" labelOnTop="0"/>
    <field name="estimated_posts" labelOnTop="0"/>
    <field name="fid" labelOnTop="0"/>
    <field name="function_description" labelOnTop="1"/>
    <field name="mimics_id" labelOnTop="0"/>
    <field name="name" labelOnTop="0"/>
    <field name="structure_mimics" labelOnTop="0"/>
    <field name="structure_type_name" labelOnTop="0"/>
    <field name="typical_height" labelOnTop="0"/>
    <field name="typical_length" labelOnTop="0"/>
    <field name="typical_posts" labelOnTop="0"/>
    <field name="typical_width" labelOnTop="0"/>
  </labelOnTop>
  <reuseLastValue>
    <field reuseLastValue="0" name="construction_description"/>
    <field reuseLastValue="0" name="created"/>
    <field reuseLastValue="0" name="fid"/>
    <field reuseLastValue="0" name="function_description"/>
    <field reuseLastValue="0" name="mimics_id"/>
    <field reuseLastValue="0" name="name"/>
    <field reuseLastValue="0" name="typical_height"/>
    <field reuseLastValue="0" name="typical_length"/>
    <field reuseLastValue="0" name="typical_posts"/>
    <field reuseLastValue="0" name="typical_width"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"name"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
