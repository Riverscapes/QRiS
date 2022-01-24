<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.18.2-Zürich" readOnly="0" hasScaleBasedVisibilityFlag="0" minScale="1e+08" maxScale="0" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal endExpression="" startField="" enabled="0" accumulate="0" mode="0" endField="" fixedDuration="0" startExpression="" durationField="" durationUnit="min">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <legend type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field name="fid" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="phase_name" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="phase_type" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="dominate_action" configurationFlags="None">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option name="map" type="List">
              <Option type="Map">
                <Option name="New Structure Additions" type="QString" value="New Structure Additions"/>
              </Option>
              <Option type="Map">
                <Option name="Existing Structure Enhancements" type="QString" value="Existing Structure Enhancements"/>
              </Option>
              <Option type="Map">
                <Option name="Other" type="QString" value="Other"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="implementation_date" configurationFlags="None">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option name="allow_null" type="bool" value="true"/>
            <Option name="calendar_popup" type="bool" value="true"/>
            <Option name="display_format" type="QString" value="yyyy-MM-dd"/>
            <Option name="field_format" type="QString" value="yyyy-MM-dd"/>
            <Option name="field_iso_format" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="phase_description" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="true"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="Phase ID" field="fid" index="0"/>
    <alias name="Phase Name" field="phase_name" index="1"/>
    <alias name="Phase Type" field="phase_type" index="2"/>
    <alias name="Dominate Action" field="dominate_action" index="3"/>
    <alias name="Implementation Date" field="implementation_date" index="4"/>
    <alias name="Phase Description" field="phase_description" index="5"/>
  </aliases>
  <defaults>
    <default field="fid" applyOnUpdate="0" expression=""/>
    <default field="phase_name" applyOnUpdate="0" expression=""/>
    <default field="phase_type" applyOnUpdate="0" expression=""/>
    <default field="dominate_action" applyOnUpdate="0" expression="'New Structure Additions'"/>
    <default field="implementation_date" applyOnUpdate="0" expression=""/>
    <default field="phase_description" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint unique_strength="1" notnull_strength="1" field="fid" exp_strength="0" constraints="3"/>
    <constraint unique_strength="0" notnull_strength="1" field="phase_name" exp_strength="0" constraints="1"/>
    <constraint unique_strength="0" notnull_strength="0" field="phase_type" exp_strength="0" constraints="0"/>
    <constraint unique_strength="0" notnull_strength="1" field="dominate_action" exp_strength="0" constraints="1"/>
    <constraint unique_strength="0" notnull_strength="1" field="implementation_date" exp_strength="0" constraints="1"/>
    <constraint unique_strength="0" notnull_strength="0" field="phase_description" exp_strength="0" constraints="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="fid" exp=""/>
    <constraint desc="" field="phase_name" exp=""/>
    <constraint desc="" field="phase_type" exp=""/>
    <constraint desc="" field="dominate_action" exp=""/>
    <constraint desc="" field="implementation_date" exp=""/>
    <constraint desc="" field="phase_description" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="">
    <columns>
      <column name="fid" type="field" width="-1" hidden="0"/>
      <column name="phase_name" type="field" width="-1" hidden="0"/>
      <column name="phase_type" type="field" width="-1" hidden="0"/>
      <column name="dominate_action" type="field" width="-1" hidden="0"/>
      <column name="implementation_date" type="field" width="-1" hidden="0"/>
      <column name="phase_description" type="field" width="-1" hidden="0"/>
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
    <attributeEditorField name="fid" showLabel="1" index="0"/>
    <attributeEditorField name="phase_name" showLabel="1" index="1"/>
    <attributeEditorField name="dominate_action" showLabel="1" index="3"/>
    <attributeEditorField name="implementation_date" showLabel="1" index="4"/>
    <attributeEditorField name="phase_description" showLabel="1" index="5"/>
  </attributeEditorForm>
  <editable>
    <field name="dominate_action" editable="1"/>
    <field name="fid" editable="1"/>
    <field name="implementation_date" editable="1"/>
    <field name="phase_description" editable="1"/>
    <field name="phase_name" editable="1"/>
    <field name="phase_type" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="dominate_action" labelOnTop="1"/>
    <field name="fid" labelOnTop="1"/>
    <field name="implementation_date" labelOnTop="1"/>
    <field name="phase_description" labelOnTop="1"/>
    <field name="phase_name" labelOnTop="1"/>
    <field name="phase_type" labelOnTop="1"/>
  </labelOnTop>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"phase_name"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
