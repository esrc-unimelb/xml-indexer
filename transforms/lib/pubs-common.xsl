<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:n="urn:isbn:1-931666-33-4"
    xmlns:str="http://exslt.org/strings"
    extension-element-prefixes="str"
    exclude-result-prefixes="n str"
    version="1.0">

    <!-- Extract the pub resource type -->
    <xsl:template name="publication-common">
        <field name="id"><xsl:value-of select="//meta[@name='DC.Identifier']/@content" /></field>

        <field name="name"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='title']" /></field>
        <field name="in"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='secondarytitle']" /></field>
        <field name="author"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='author']" /></field>
        <field name="editor"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='secondaryauthor']" /></field>
        <field name="imprint"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='imprint']" /></field>
        <field name="abstract"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='abstract']" /></field>
        <field name="typeofwork"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='typeofwork']" /></field>
        <field name="url">
            <xsl:call-template name="extract-link">
                <xsl:with-param name="link" select="//dl[@class='content-summary']/dd[@class='url']/a/@href"></xsl:with-param>
            </xsl:call-template>
        </field>


        <xsl:variable name="type" select="str:split(//meta[@name='DC.Title']/@content, ' - ')" />
        <field name="type"><xsl:value-of select="$type" /></field>
        <field name="pub_type"><xsl:value-of select="$type" /></field>
        <field name="main_type">Publication</field>
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