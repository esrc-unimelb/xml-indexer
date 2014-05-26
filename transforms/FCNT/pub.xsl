<?xml version="1.0" encoding="UTF-8"?>
<!-- 
    EAC-CPF to Apache Solr Input Document Format Transform
    Copyright 2013 eScholarship Research Centre, University of Melbourne
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
        http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <xsl:import href="../lib/common.xsl" />

    <xsl:output method="text" indent="yes" encoding="UTF-8" omit-xml-declaration="yes" />
    <xsl:template match="/">
        <add>
            <doc>
                <field name="id"><xsl:value-of select="//meta[@name='DC.Identifier']/@content" /></field>
                <xsl:call-template name="pub_resource_type" />
                <field name="creator"><xsl:value-of select="//meta[@name='DC.Creator']/@content" /></field>
                <!-- <field name="name"><xsl:value-of select="//meta[@name='DC.Title']/@content" /></field> -->
                <field name="name">
                    <xsl:value-of select="//dl[@class='content-summary']/dd[@class='title']" />
                    <xsl:text>, </xsl:text>
                    <xsl:value-of select="//dl[@class='content-summary']/dd[@class='secondarytitle']" />
                </field>
                <field name="author"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='author']" /></field>
                <field name="editor"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='secondaryauthor']" /></field>
                <field name="imprint"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='imprint']" /></field>
                <field name="url"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='url']" /></field>
                <field name="abstract"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='abstract']" /></field>
                <field name="state_long">Northern Territory</field>
                <field name="state_short">NT</field>
            </doc>
        </add>
    </xsl:template>
</xsl:stylesheet>