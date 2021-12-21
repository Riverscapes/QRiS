<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" labelsEnabled="0" readOnly="0" styleCategories="AllStyleCategories" simplifyDrawingHints="1" simplifyLocal="1" minScale="100000000" maxScale="0" simplifyAlgorithm="0" simplifyMaxScale="1" version="3.16.5-Hannover" simplifyDrawingTol="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal mode="0" durationUnit="min" startField="" startExpression="" fixedDuration="0" endExpression="" accumulate="0" endField="" enabled="0" durationField="">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol type="fill" alpha="1" clip_to_extent="1" name="0" force_rhr="0">
        <layer pass="0" class="SimpleFill" locked="0" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="201,221,226,64"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="dash"/>
          <prop k="outline_width" v="0.56"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="parent_id" key="variableNames"/>
    <property value="" key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory opacity="1" maxScaleDenominator="1e+08" diagramOrientation="Up" labelPlacementMethod="XHeight" penColor="#000000" width="15" penWidth="0" scaleBasedVisibility="0" enabled="0" minScaleDenominator="0" sizeType="MM" scaleDependency="Area" spacingUnit="MM" lineSizeType="MM" penAlpha="255" backgroundColor="#ffffff" sizeScale="3x:0,0,0,0,0,0" barWidth="5" rotationOffset="270" spacingUnitScale="3x:0,0,0,0,0,0" backgroundAlpha="255" spacing="5" showAxis="1" direction="0" height="15" lineSizeScale="3x:0,0,0,0,0,0" minimumSize="0">
      <fontProperties style="" description=".AppleSystemUIFont,13,-1,5,50,0,0,0,0,0"/>
      <axisSymbol>
        <symbol type="line" alpha="1" clip_to_extent="1" name="" force_rhr="0">
          <layer pass="0" class="SimpleLine" locked="0" enabled="1">
            <prop k="align_dash_pattern" v="0"/>
            <prop k="capstyle" v="square"/>
            <prop k="customdash" v="5;2"/>
            <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="customdash_unit" v="MM"/>
            <prop k="dash_pattern_offset" v="0"/>
            <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="dash_pattern_offset_unit" v="MM"/>
            <prop k="draw_inside_polygon" v="0"/>
            <prop k="joinstyle" v="bevel"/>
            <prop k="line_color" v="35,35,35,255"/>
            <prop k="line_style" v="solid"/>
            <prop k="line_width" v="0.26"/>
            <prop k="line_width_unit" v="MM"/>
            <prop k="offset" v="0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="ring_filter" v="0"/>
            <prop k="tweak_dash_pattern_on_corners" v="0"/>
            <prop k="use_custom_dash" v="0"/>
            <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings dist="0" linePlacementFlags="18" showAll="1" zIndex="0" priority="0" placement="1" obstacle="0">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option type="Map" name="QgsGeometryGapCheck">
        <Option type="double" value="0" name="allowedGapsBuffer"/>
        <Option type="bool" value="false" name="allowedGapsEnabled"/>
        <Option type="QString" value="" name="allowedGapsLayer"/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <legend type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field name="fid" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="design_id" configurationFlags="None">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="AllowMulti"/>
            <Option type="bool" value="true" name="AllowNull"/>
            <Option type="QString" value="" name="Description"/>
            <Option type="QString" value="" name="FilterExpression"/>
            <Option type="QString" value="fid" name="Key"/>
            <Option type="QString" value="Designs_09657594_e60d_4dc1_908a_968ad7f207b3" name="Layer"/>
            <Option type="QString" value="Designs" name="LayerName"/>
            <Option type="QString" value="ogr" name="LayerProviderName"/>
            <Option type="QString" value="/Users/nick/Desktop/TuesdayTest/designs/designs.gpkg|layername=designs" name="LayerSource"/>
            <Option type="int" value="1" name="NofColumns"/>
            <Option type="bool" value="false" name="OrderByValue"/>
            <Option type="bool" value="false" name="UseCompleter"/>
            <Option type="QString" value="design_name" name="Value"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="zoi_name" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="zoi_type" configurationFlags="None">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option type="List" name="map">
              <Option type="Map">
                <Option type="QString" value="structure" name="Structure"/>
              </Option>
              <Option type="Map">
                <Option type="QString" value="complex" name="Complex"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="zoi_description" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="true" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="fid"/>
    <alias index="1" name="Design Name" field="design_id"/>
    <alias index="2" name="ZOI Name" field="zoi_name"/>
    <alias index="3" name="ZOI Type" field="zoi_type"/>
    <alias index="4" name="ZOI Description" field="zoi_description"/>
  </aliases>
  <defaults>
    <default expression="" field="fid" applyOnUpdate="0"/>
    <default expression="@parent_id" field="design_id" applyOnUpdate="0"/>
    <default expression="" field="zoi_name" applyOnUpdate="0"/>
    <default expression="" field="zoi_type" applyOnUpdate="0"/>
    <default expression="" field="zoi_description" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint notnull_strength="1" unique_strength="1" exp_strength="0" constraints="3" field="fid"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="design_id"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="zoi_name"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="zoi_type"/>
    <constraint notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0" field="zoi_description"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="fid"/>
    <constraint exp="" desc="" field="design_id"/>
    <constraint exp="" desc="" field="zoi_name"/>
    <constraint exp="" desc="" field="zoi_type"/>
    <constraint exp="" desc="" field="zoi_description"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="">
    <columns>
      <column type="field" hidden="0" width="-1" name="fid"/>
      <column type="field" hidden="0" width="-1" name="design_id"/>
      <column type="field" hidden="0" width="-1" name="zoi_name"/>
      <column type="field" hidden="0" width="-1" name="zoi_type"/>
      <column type="field" hidden="0" width="-1" name="zoi_description"/>
      <column type="actions" hidden="1" width="-1"/>
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
    <attributeEditorField index="1" showLabel="1" name="design_id"/>
    <attributeEditorField index="2" showLabel="1" name="zoi_name"/>
    <attributeEditorField index="3" showLabel="1" name="zoi_type"/>
    <attributeEditorField index="4" showLabel="1" name="zoi_description"/>
  </attributeEditorForm>
  <editable>
    <field editable="1" name="design_id"/>
    <field editable="1" name="fid"/>
    <field editable="1" name="zoi_description"/>
    <field editable="1" name="zoi_name"/>
    <field editable="1" name="zoi_type"/>
  </editable>
  <labelOnTop>
    <field name="design_id" labelOnTop="1"/>
    <field name="fid" labelOnTop="0"/>
    <field name="zoi_description" labelOnTop="1"/>
    <field name="zoi_name" labelOnTop="1"/>
    <field name="zoi_type" labelOnTop="1"/>
  </labelOnTop>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"zoi_name"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
