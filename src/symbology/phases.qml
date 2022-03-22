<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="1e+08" readOnly="0" styleCategories="AllStyleCategories" version="3.22.3-Białowieża" hasScaleBasedVisibilityFlag="0" maxScale="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal startField="implementation_date" endField="" fixedDuration="0" mode="0" startExpression="" durationField="fid" accumulate="0" durationUnit="min" endExpression="" enabled="0" limitMode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <Option type="Map">
      <Option type="List" name="dualview/previewExpressions">
        <Option type="QString" value="&quot;name&quot;"/>
      </Option>
      <Option type="QString" name="embeddedWidgets/count" value="0"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <legend showLabelLegend="0" type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field configurationFlags="None" name="fid">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" name="IsMultiline" value="false"/>
            <Option type="bool" name="UseHtml" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="name">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" name="IsMultiline" value="false"/>
            <Option type="bool" name="UseHtml" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="primary_action_id">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option type="bool" name="AllowMulti" value="false"/>
            <Option type="bool" name="AllowNull" value="false"/>
            <Option type="QString" name="Description" value="&quot;description&quot;"/>
            <Option type="QString" name="FilterExpression" value=""/>
            <Option type="QString" name="Key" value="fid"/>
            <Option type="QString" name="Layer" value="Phase_Action_c4fd53b8_7d0f_41d0_b5a9_1c1dbfbf57ad"/>
            <Option type="QString" name="LayerName" value="Phase Action"/>
            <Option type="QString" name="LayerProviderName" value="ogr"/>
            <Option type="QString" name="LayerSource" value="/Users/nick/Desktop/ztest/designs/designs.gpkg|layername=phase_action"/>
            <Option type="int" name="NofColumns" value="1"/>
            <Option type="bool" name="OrderByValue" value="false"/>
            <Option type="bool" name="UseCompleter" value="false"/>
            <Option type="QString" name="Value" value="name"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="implementation_date">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option type="bool" name="allow_null" value="true"/>
            <Option type="bool" name="calendar_popup" value="true"/>
            <Option type="QString" name="display_format" value="yyyy-MM-dd"/>
            <Option type="QString" name="field_format" value="yyyy-MM-dd"/>
            <Option type="bool" name="field_iso_format" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="description">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" name="IsMultiline" value="true"/>
            <Option type="bool" name="UseHtml" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="created">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option type="bool" name="allow_null" value="true"/>
            <Option type="bool" name="calendar_popup" value="true"/>
            <Option type="QString" name="display_format" value="M/d/yy HH:mm:ss"/>
            <Option type="QString" name="field_format" value="M/d/yy HH:mm:ss"/>
            <Option type="bool" name="field_iso_format" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="fid" name="Phase ID"/>
    <alias index="1" field="name" name="Phase Name"/>
    <alias index="2" field="primary_action_id" name="Primary Action"/>
    <alias index="3" field="implementation_date" name="Implementation Date"/>
    <alias index="4" field="description" name="Phase Description"/>
    <alias index="5" field="created" name=""/>
  </aliases>
  <defaults>
    <default field="fid" expression="" applyOnUpdate="0"/>
    <default field="name" expression="" applyOnUpdate="0"/>
    <default field="primary_action_id" expression="" applyOnUpdate="0"/>
    <default field="implementation_date" expression="" applyOnUpdate="0"/>
    <default field="description" expression="" applyOnUpdate="0"/>
    <default field="created" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" notnull_strength="1" constraints="3" field="fid" unique_strength="1"/>
    <constraint exp_strength="0" notnull_strength="1" constraints="3" field="name" unique_strength="1"/>
    <constraint exp_strength="0" notnull_strength="1" constraints="1" field="primary_action_id" unique_strength="0"/>
    <constraint exp_strength="0" notnull_strength="1" constraints="1" field="implementation_date" unique_strength="0"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" field="description" unique_strength="0"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" field="created" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="fid" exp=""/>
    <constraint desc="" field="name" exp=""/>
    <constraint desc="" field="primary_action_id" exp=""/>
    <constraint desc="" field="implementation_date" exp=""/>
    <constraint desc="" field="description" exp=""/>
    <constraint desc="" field="created" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortExpression="" actionWidgetStyle="dropDown" sortOrder="0">
    <columns>
      <column width="-1" type="field" hidden="0" name="fid"/>
      <column width="-1" type="field" hidden="0" name="implementation_date"/>
      <column width="-1" type="field" hidden="0" name="name"/>
      <column width="-1" type="field" hidden="0" name="primary_action_id"/>
      <column width="-1" type="field" hidden="0" name="description"/>
      <column width="-1" type="field" hidden="0" name="created"/>
      <column width="-1" type="actions" hidden="1"/>
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
    <attributeEditorField showLabel="1" index="0" name="fid"/>
    <attributeEditorField showLabel="1" index="1" name="name"/>
    <attributeEditorField showLabel="1" index="2" name="primary_action_id"/>
    <attributeEditorField showLabel="1" index="3" name="implementation_date"/>
    <attributeEditorField showLabel="1" index="4" name="description"/>
    <attributeEditorField showLabel="1" index="5" name="created"/>
  </attributeEditorForm>
  <editable>
    <field editable="0" name="created"/>
    <field editable="1" name="description"/>
    <field editable="1" name="dominate_action"/>
    <field editable="0" name="fid"/>
    <field editable="1" name="implementation_date"/>
    <field editable="1" name="name"/>
    <field editable="1" name="phase_description"/>
    <field editable="1" name="phase_name"/>
    <field editable="1" name="phase_type"/>
    <field editable="1" name="primary_action_id"/>
  </editable>
  <labelOnTop>
    <field name="created" labelOnTop="0"/>
    <field name="description" labelOnTop="1"/>
    <field name="dominate_action" labelOnTop="1"/>
    <field name="fid" labelOnTop="0"/>
    <field name="implementation_date" labelOnTop="0"/>
    <field name="name" labelOnTop="0"/>
    <field name="phase_description" labelOnTop="1"/>
    <field name="phase_name" labelOnTop="1"/>
    <field name="phase_type" labelOnTop="1"/>
    <field name="primary_action_id" labelOnTop="0"/>
  </labelOnTop>
  <reuseLastValue>
    <field reuseLastValue="0" name="created"/>
    <field reuseLastValue="0" name="description"/>
    <field reuseLastValue="0" name="fid"/>
    <field reuseLastValue="0" name="implementation_date"/>
    <field reuseLastValue="0" name="name"/>
    <field reuseLastValue="0" name="primary_action_id"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"name"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
