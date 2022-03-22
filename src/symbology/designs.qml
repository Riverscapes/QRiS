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
        <Option type="QString" value="concat(to_string(&quot;fid&quot;), '-', &quot;name&quot;)"/>
        <Option type="QString" value="&quot;design_name&quot;"/>
        <Option type="QString" value="concat(&quot;fid&quot;, &quot;-&quot;, &quot;design_name&quot;)"/>
        <Option type="QString" value="concat(to_string(&quot;fid&quot;), '-', &quot;name&quot;)"/>
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
    <field configurationFlags="None" name="structure_geometry">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option name="map" type="List">
              <Option type="Map">
                <Option name="Point" type="QString" value="Point"/>
              </Option>
              <Option type="Map">
                <Option name="Line" type="QString" value="Line"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="status_id">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" type="bool" value="false"/>
            <Option name="AllowNull" type="bool" value="false"/>
            <Option name="Description" type="QString" value="&quot;description&quot;"/>
            <Option name="FilterExpression" type="QString" value=""/>
            <Option name="Key" type="QString" value="fid"/>
            <Option name="Layer" type="QString" value="Design_Status_6012f983_2137_4176_abaa_675a5477cf9d"/>
            <Option name="LayerName" type="QString" value="Design Status"/>
            <Option name="LayerProviderName" type="QString" value="ogr"/>
            <Option name="LayerSource" type="QString" value="/Users/nick/Desktop/ztest/designs/designs.gpkg|layername=design_status"/>
            <Option name="NofColumns" type="int" value="1"/>
            <Option name="OrderByValue" type="bool" value="false"/>
            <Option name="UseCompleter" type="bool" value="false"/>
            <Option name="Value" type="QString" value="name"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="description">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="true"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="created">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option name="allow_null" type="bool" value="true"/>
            <Option name="calendar_popup" type="bool" value="true"/>
            <Option name="display_format" type="QString" value="M/d/yy HH:mm:ss"/>
            <Option name="field_format" type="QString" value="M/d/yy HH:mm:ss"/>
            <Option name="field_iso_format" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="Design ID" field="fid"/>
    <alias index="1" name="Design Name" field="name"/>
    <alias index="2" name="Structure Geometry" field="structure_geometry"/>
    <alias index="3" name="Design Status" field="status_id"/>
    <alias index="4" name="Design Description" field="description"/>
    <alias index="5" name="" field="created"/>
  </aliases>
  <defaults>
    <default applyOnUpdate="0" expression="" field="fid"/>
    <default applyOnUpdate="0" expression="" field="name"/>
    <default applyOnUpdate="0" expression="" field="structure_geometry"/>
    <default applyOnUpdate="0" expression="" field="status_id"/>
    <default applyOnUpdate="0" expression="" field="description"/>
    <default applyOnUpdate="0" expression="" field="created"/>
  </defaults>
  <constraints>
    <constraint constraints="3" notnull_strength="1" unique_strength="1" exp_strength="0" field="fid"/>
    <constraint constraints="3" notnull_strength="1" unique_strength="1" exp_strength="0" field="name"/>
    <constraint constraints="1" notnull_strength="1" unique_strength="0" exp_strength="0" field="structure_geometry"/>
    <constraint constraints="1" notnull_strength="1" unique_strength="0" exp_strength="0" field="status_id"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="description"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" exp_strength="0" field="created"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="fid"/>
    <constraint exp="" desc="" field="name"/>
    <constraint exp="" desc="" field="structure_geometry"/>
    <constraint exp="" desc="" field="status_id"/>
    <constraint exp="" desc="" field="description"/>
    <constraint exp="" desc="" field="created"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column name="fid" type="field" width="-1" hidden="0"/>
      <column name="name" type="field" width="170" hidden="0"/>
      <column name="structure_geometry" type="field" width="149" hidden="0"/>
      <column name="status_id" type="field" width="126" hidden="0"/>
      <column name="description" type="field" width="114" hidden="0"/>
      <column name="created" type="field" width="189" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
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
    <attributeEditorField showLabel="1" name="status_id" index="3"/>
    <attributeEditorField showLabel="1" name="structure_geometry" index="2"/>
    <attributeEditorField showLabel="1" name="description" index="4"/>
    <attributeEditorField showLabel="1" name="created" index="5"/>
  </attributeEditorForm>
  <editable>
    <field name="created" editable="1"/>
    <field name="description" editable="1"/>
    <field name="design_description" editable="1"/>
    <field name="design_geometry" editable="0"/>
    <field name="design_name" editable="1"/>
    <field name="design_status" editable="1"/>
    <field name="fid" editable="0"/>
    <field name="name" editable="1"/>
    <field name="status_id" editable="1"/>
    <field name="structure_geometry" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="created" labelOnTop="0"/>
    <field name="description" labelOnTop="1"/>
    <field name="design_description" labelOnTop="0"/>
    <field name="design_geometry" labelOnTop="0"/>
    <field name="design_name" labelOnTop="0"/>
    <field name="design_status" labelOnTop="0"/>
    <field name="fid" labelOnTop="0"/>
    <field name="name" labelOnTop="0"/>
    <field name="status_id" labelOnTop="0"/>
    <field name="structure_geometry" labelOnTop="0"/>
  </labelOnTop>
  <reuseLastValue>
    <field reuseLastValue="0" name="created"/>
    <field reuseLastValue="0" name="description"/>
    <field reuseLastValue="0" name="fid"/>
    <field reuseLastValue="0" name="name"/>
    <field reuseLastValue="0" name="status_id"/>
    <field reuseLastValue="0" name="structure_geometry"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>concat(to_string("fid"), '-', "name")</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
