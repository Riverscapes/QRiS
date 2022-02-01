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
    <property value="&quot;construction_description&quot;" key="dualview/previewExpressions"/>
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
    <field configurationFlags="None" name="structure_type_name">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="structure_mimics">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option type="List" name="map">
              <Option type="Map">
                <Option value="Beaver Dam" type="QString" name="Beaver Dam"/>
              </Option>
              <Option type="Map">
                <Option value="Wood Jam" type="QString" name="Wood Jam"/>
              </Option>
              <Option type="Map">
                <Option value="Other Structure" type="QString" name="Other Structure"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="construction_description">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="true" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="function_description">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="true" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_posts">
      <editWidget type="Range">
        <config>
          <Option type="Map">
            <Option value="true" type="bool" name="AllowNull"/>
            <Option value="500" type="int" name="Max"/>
            <Option value="0" type="int" name="Min"/>
            <Option value="0" type="int" name="Precision"/>
            <Option value="1" type="int" name="Step"/>
            <Option value="SpinBox" type="QString" name="Style"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_length">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_width">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="typical_height">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="fid" index="0" name="Structure Type ID"/>
    <alias field="structure_type_name" index="1" name="Type Name"/>
    <alias field="structure_mimics" index="2" name="Mimics"/>
    <alias field="construction_description" index="3" name="Construction Description"/>
    <alias field="function_description" index="4" name="Function Description"/>
    <alias field="typical_posts" index="5" name="Typical Posts"/>
    <alias field="typical_length" index="6" name="Typical Length"/>
    <alias field="typical_width" index="7" name="Typical Width"/>
    <alias field="typical_height" index="8" name="Typical Height"/>
  </aliases>
  <defaults>
    <default expression="" applyOnUpdate="0" field="fid"/>
    <default expression="" applyOnUpdate="0" field="structure_type_name"/>
    <default expression="'Beaver Dam'" applyOnUpdate="0" field="structure_mimics"/>
    <default expression="" applyOnUpdate="0" field="construction_description"/>
    <default expression="" applyOnUpdate="0" field="function_description"/>
    <default expression="" applyOnUpdate="0" field="typical_posts"/>
    <default expression="" applyOnUpdate="0" field="typical_length"/>
    <default expression="" applyOnUpdate="0" field="typical_width"/>
    <default expression="" applyOnUpdate="0" field="typical_height"/>
  </defaults>
  <constraints>
    <constraint unique_strength="1" exp_strength="0" constraints="3" notnull_strength="1" field="fid"/>
    <constraint unique_strength="0" exp_strength="0" constraints="1" notnull_strength="1" field="structure_type_name"/>
    <constraint unique_strength="0" exp_strength="0" constraints="1" notnull_strength="1" field="structure_mimics"/>
    <constraint unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0" field="construction_description"/>
    <constraint unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0" field="function_description"/>
    <constraint unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0" field="typical_posts"/>
    <constraint unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0" field="typical_length"/>
    <constraint unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0" field="typical_width"/>
    <constraint unique_strength="0" exp_strength="0" constraints="0" notnull_strength="0" field="typical_height"/>
  </constraints>
  <constraintExpressions>
    <constraint field="fid" exp="" desc=""/>
    <constraint field="structure_type_name" exp="" desc=""/>
    <constraint field="structure_mimics" exp="" desc=""/>
    <constraint field="construction_description" exp="" desc=""/>
    <constraint field="function_description" exp="" desc=""/>
    <constraint field="typical_posts" exp="" desc=""/>
    <constraint field="typical_length" exp="" desc=""/>
    <constraint field="typical_width" exp="" desc=""/>
    <constraint field="typical_height" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns>
      <column width="-1" type="field" hidden="0" name="fid"/>
      <column width="-1" type="field" hidden="0" name="structure_type_name"/>
      <column width="-1" type="field" hidden="0" name="structure_mimics"/>
      <column width="-1" type="field" hidden="0" name="construction_description"/>
      <column width="-1" type="field" hidden="0" name="function_description"/>
      <column width="-1" type="field" hidden="0" name="typical_length"/>
      <column width="-1" type="field" hidden="0" name="typical_width"/>
      <column width="-1" type="field" hidden="0" name="typical_height"/>
      <column width="-1" type="actions" hidden="1"/>
      <column width="-1" type="field" hidden="0" name="typical_posts"/>
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
    <attributeEditorField showLabel="1" index="1" name="structure_type_name"/>
    <attributeEditorField showLabel="1" index="2" name="structure_mimics"/>
    <attributeEditorField showLabel="1" index="3" name="construction_description"/>
    <attributeEditorField showLabel="1" index="4" name="function_description"/>
    <attributeEditorField showLabel="1" index="5" name="typical_posts"/>
    <attributeEditorField showLabel="1" index="6" name="typical_length"/>
    <attributeEditorField showLabel="1" index="7" name="typical_width"/>
    <attributeEditorField showLabel="1" index="8" name="typical_height"/>
  </attributeEditorForm>
  <editable>
    <field editable="1" name="construction_description"/>
    <field editable="1" name="estimated_posts"/>
    <field editable="0" name="fid"/>
    <field editable="1" name="function_description"/>
    <field editable="1" name="structure_mimics"/>
    <field editable="1" name="structure_type_name"/>
    <field editable="1" name="typical_height"/>
    <field editable="1" name="typical_length"/>
    <field editable="1" name="typical_posts"/>
    <field editable="1" name="typical_width"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="construction_description"/>
    <field labelOnTop="0" name="estimated_posts"/>
    <field labelOnTop="0" name="fid"/>
    <field labelOnTop="0" name="function_description"/>
    <field labelOnTop="0" name="structure_mimics"/>
    <field labelOnTop="0" name="structure_type_name"/>
    <field labelOnTop="0" name="typical_height"/>
    <field labelOnTop="0" name="typical_length"/>
    <field labelOnTop="0" name="typical_posts"/>
    <field labelOnTop="0" name="typical_width"/>
  </labelOnTop>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"construction_description"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
