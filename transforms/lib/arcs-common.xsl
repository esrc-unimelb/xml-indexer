<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:n="urn:isbn:1-931666-33-4"
    xmlns:str="http://exslt.org/strings"
    extension-element-prefixes="str"
    exclude-result-prefixes="n str"
    version="1.0">

    <xsl:import href="common.xsl" />

    <!-- Extract the common data for archival resources -->
    <xsl:template name="archival-resource-common">
        <field name="id"><xsl:value-of select="//meta[@name='DC.Identifier']/@content" /></field>
        <xsl:call-template name="record_id" />
        <field name="name"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='title']" /></field>
        <field name="reference"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='arrepref']" /></field>
        <field name="reference_link">
            <xsl:call-template name="extract-link">
                <xsl:with-param name="link" select="//dl[@class='content-summary']/dd[@class='arrepref']/a/@href"></xsl:with-param>
            </xsl:call-template>
        </field>
        <field name="repository"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='arrepository']" /></field>
        <field name="repository_link">
            <xsl:call-template name="extract-link">
                <xsl:with-param name="link" select="//dl[@class='content-summary']/dd[@class='arrepository']/a/@href"></xsl:with-param>
            </xsl:call-template>
        </field>
        <field name="date_from"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='ardate']" /></field>
        <field name="creator"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='arcreator']" /></field>
        <field name="description"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='ardescription']" /></field>
        <field name="type">Archival Resource</field>
        <field name="main_type">Archival Resource</field>
    </xsl:template>

    <xsl:template name="extract-link">
        <xsl:param name="link"></xsl:param>
        <xsl:variable name="components" select="str:tokenize($link, '/')" />
        <xsl:choose>
            <!-- does the path begin with http or https? Use as is -->
            <xsl:when test="$components[1] = 'http:' or $components[1] = 'https:'">
                <xsl:value-of select="$link" />
            </xsl:when>

            <!-- does the path begin with ../? chomp up to objects/ and reconstruct with DC.Identifier -->
            <xsl:when test="$components[1] = '..'">
                <xsl:choose>
                    <xsl:when test="$components[2] = 'archives'">
                        <xsl:variable name="head" select="str:split(//meta[@name='DC.Identifier']/@content, '/archives')" />
                        <xsl:variable name="tail" select="str:split($link, 'archives')[2]" />
                        <xsl:value-of select="$head" />
                        <xsl:text>/archives</xsl:text>
                        <xsl:value-of select="$tail" />
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>