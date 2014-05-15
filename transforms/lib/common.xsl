<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:n="urn:isbn:1-931666-33-4"
    xmlns:str="http://exslt.org/strings"
    extension-element-prefixes="str"
    exclude-result-prefixes="n str"
    version="1.0">

    <!-- Extract the dobject type -->
    <xsl:template name="dobject_type">
        <xsl:variable name="type" select="str:split(//meta[@name='DC.Title']/@content, ' - ')" />
        <field name="type">
            <xsl:value-of select="$type" />
        </field>
        <field name="main_type">Digital Object</field>
    </xsl:template>

    <!-- Extract the arc resource type -->
    <xsl:template name="arc_resource_type">
        <field name="type">Archival Resource</field>
        <field name="main_type">Archival Resource</field>
    </xsl:template>

    <!-- Extract the pub resource type -->
    <xsl:template name="pub_resource_type">
        <xsl:variable name="type" select="str:split(//meta[@name='DC.Title']/@content, ' - ')" />
        <field name="type">
            <xsl:value-of select="$type" />
        </field>
        <field name="main_type">Publication</field>
    </xsl:template>

    <!-- Extract the dobject thumbnail -->
    <xsl:template name="thumbnail">
        <xsl:variable name="docpath" select="str:split(//meta[@name='DC.Identifier']/@content, '/objects')" />
        <xsl:variable name="thumbpath" select="str:split(//img[@id='dothumb']/@src, '../objects')" />
        <xsl:value-of select="$docpath" />
        <xsl:text>/objects</xsl:text>
        <xsl:value-of select="$thumbpath" />
    </xsl:template>

    <!-- Extract the dobject large image -->
    <xsl:template name="large_image">
        <xsl:variable name="docpath" select="str:split(//meta[@name='DC.Identifier']/@content, '/objects')" />
        <xsl:variable name="im" select="str:split(//div[@class='entity-image']/a/@href, '../image_viewer.htm?objects')" />
        <xsl:variable name="largepath" select="str:split($im, ',')" />
        <xsl:value-of select="$docpath" />
        <xsl:text>/objects</xsl:text>
        <xsl:value-of select="$largepath" />
    </xsl:template>

    <!-- Extract the entity functions -->
    <xsl:template match="/n:eac-cpf/n:cpfDescription/n:description/n:functions/n:function/n:term">
        <field name="function"><xsl:value-of select="." /></field>
    </xsl:template>

    <!-- Extract locality definitions -->
    <xsl:template match="/n:eac-cpf/n:cpfDescription/n:description/n:biogHist/n:chronList/n:chronItem/n:event">
        <field name="locality"><xsl:value-of select="." /></field>
    </xsl:template>

    <!-- Extract the name of the entity -->
    <xsl:template name="name">
        <xsl:variable name="type" select="/n:eac-cpf/n:control/n:localControl[@localType='typeOfEntity']/n:term" />
        <xsl:choose>
            <xsl:when test="$type = 'Person'">
                <field name="name">
                    <xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry/n:part[@localType='familyname']" />
                    <xsl:text>, </xsl:text>
                    <xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry/n:part[@localType='givenname']" />
                </field>
            </xsl:when>
            <xsl:otherwise>
                <field name="name"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry/n:part" /></field>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Extract the alternate name of the entity -->
    <xsl:template match="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry[position()>1]/n:part">
        <field name="altname"><xsl:value-of select="." /></field>
    </xsl:template>

    <!-- Extract the binomial name of the entity -->
    <xsl:template name="binomial_name">
        <xsl:variable name="type" select="/n:eac-cpf/n:control/n:localControl[@localType='typeOfEntity']/n:term" />
        <xsl:choose>
            <xsl:when test="$type != 'Person'">
                <field name="binomial_name"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry/n:part[position() = 2]" /></field>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>