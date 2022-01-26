<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" version="3.18.2-Zürich" maxScale="0" readOnly="0" styleCategories="AllStyleCategories" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal endField="" startExpression="" startField="" durationField="" enabled="0" mode="0" endExpression="" durationUnit="min" accumulate="0" fixedDuration="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
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
    <field configurationFlags="None" name="fid">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="design_name">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="design_geometry">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option type="List" name="map">
              <Option type="Map">
                <Option value="Point" type="QString" name="Point"/>
              </Option>
              <Option type="Map">
                <Option value="Line" type="QString" name="Line"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="design_status">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option type="List" name="map">
              <Option type="Map">
                <Option value="Specification" type="QString" name="Specification"/>
              </Option>
              <Option type="Map">
                <Option value="As-Built" type="QString" name="As-Built"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="design_description">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="true" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="fid" index="0" name="Design ID"/>
    <alias field="design_name" index="1" name="Name"/>
    <alias field="design_geometry" index="2" name="Structure Geometry"/>
    <alias field="design_status" index="3" name="Status"/>
    <alias field="design_description" index="4" name="Description"/>
  </aliases>
  <defaults>
    <default expression="" applyOnUpdate="0" field="fid"/>
    <default expression="" applyOnUpdate="0" field="design_name"/>
    <default expression="" applyOnUpdate="0" field="design_geometry"/>
    <default expression="" applyOnUpdate="0" field="design_status"/>
    <default expression="" applyOnUpdate="0" field="design_description"/>
  </defaults>
  <constraints>
    <constraint unique_strength="1" exp_strength="0" constraints="3" notnull_strength="1" field="fid"/>
    <constraint unique_strength="0" exp_strength="0" constraints="1" notnull_strength="1" field="design_name"/>
    <constraint unique_strength="0" exp_strength="0" constraints="1" notnull_strength="1" field="design_geometry"/>
    <constraint unique_strength="0" exp_strength="0" constraints="1" notnull_strength="1" field="design_status"/>
    <constraint unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0" field="design_description"/>
  </constraints>
  <constraintExpressions>
    <constraint field="fid" exp="" desc=""/>
    <constraint field="design_name" exp="" desc=""/>
    <constraint field="design_geometry" exp="" desc=""/>
    <constraint field="design_status" exp="" desc=""/>
    <constraint field="design_description" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns>
      <column width="-1" type="field" hidden="0" name="fid"/>
      <column width="-1" type="field" hidden="0" name="design_name"/>
      <column width="-1" type="field" hidden="0" name="design_geometry"/>
      <column width="-1" type="field" hidden="0" name="design_status"/>
      <column width="-1" type="field" hidden="0" name="design_description"/>
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
    <attributeEditorField showLabel="1" index="1" name="design_name"/>
    <attributeEditorField showLabel="1" index="2" name="design_geometry"/>
    <attributeEditorField showLabel="1" index="3" name="design_status"/>
    <attributeEditorField showLabel="1" index="4" name="design_description"/>
  </attributeEditorForm>
  <editable>
    <field editable="1" name="design_description"/>
    <field editable="0" name="design_geometry"/>
    <field editable="1" name="design_name"/>
    <field editable="1" name="design_status"/>
    <field editable="0" name="fid"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="design_description"/>
    <field labelOnTop="0" name="design_geometry"/>
    <field labelOnTop="0" name="design_name"/>
    <field labelOnTop="0" name="design_status"/>
    <field labelOnTop="0" name="fid"/>
  </labelOnTop>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"design_name"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
