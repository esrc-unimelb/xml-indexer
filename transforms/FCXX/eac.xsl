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
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:n="urn:isbn:1-931666-33-4"
    version="1.0">

    <xsl:import href="../lib/common.xsl" />

    <xsl:output method="text" indent="yes" encoding="UTF-8" omit-xml-declaration="yes" />
    <xsl:template match="/">
        <add>
            <doc>
                <field name="id"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:entityId" /></field>
                <xsl:call-template name="display_url" />
                <field name="type"><xsl:value-of select="/n:eac-cpf/n:control/n:localControl[@localType='typeOfEntity']/n:term" /></field>
                <field name="record_id"><xsl:value-of select="/n:eac-cpf/n:control/n:recordId" /></field>
                <field name="creator"><xsl:value-of select="/nothere"/></field>
                <xsl:call-template name="name" />
                <xsl:apply-templates select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry[position()>1]/n:part" />
                <xsl:call-template name="binomial_name" />
                <field name="date_from"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:description/n:existDates/n:dateRange/n:fromDate/@standardDate" /></field>
                <field name="date_to"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:description/n:existDates/n:dateRange/n:toDate/@standardDate" /></field>
                <xsl:apply-templates select="/n:eac-cpf/n:cpfDescription/n:description/n:functions/n:function/n:term" />
                <field name="abstract"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:description/n:biogHist/n:abstract" /></field>
                <field name="text">
                    <xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:description/n:biogHist/n:abstract" />
                    <xsl:apply-templates select="/n:eac-cpf/n:cpfDescription/n:description/n:biogHist/n:p" />
                </field>
                <xsl:apply-templates select="/n:eac-cpf/n:cpfDescription/n:description/n:biogHist/n:chronList/n:chronItem/n:event" />
                <xsl:for-each select="/n:eac-cpf/n:cpfDescription/n:description/n:functions/n:function/n:term">
                    <xsl:variable name="org" select="." />
                    <xsl:if test="$org = 'Home'">
                        <field name="resource_type">Homes</field>
                    </xsl:if>
                </xsl:for-each>
		<field name="state_long"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:description/n:places/n:place/n:placeEntry" /></field>
                <xsl:for-each select="/n:eac-cpf/n:control/n:localControl[@localType='typeOfEntity']/n:term">
                    <xsl:variable name="res" select="." />
                    <xsl:if test="$res= 'Archival Item'">
                        <field name="resource_type">Records information</field>
                    </xsl:if>
                    <xsl:if test="$res= 'Archival Series'">
                        <field name="resource_type">Records information</field>
                    </xsl:if>
                    <xsl:if test="$res= 'Archival Collection'">
                        <field name="resource_type">Records information</field>
                    </xsl:if>
                </xsl:for-each>
            </doc>
        </add>
    </xsl:template>
</xsl:stylesheet>
