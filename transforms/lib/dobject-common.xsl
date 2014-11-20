<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:n="urn:isbn:1-931666-33-4"
    xmlns:str="http://exslt.org/strings"
    extension-element-prefixes="str"
    exclude-result-prefixes="n str"
    version="1.0">

    <xsl:import href="common.xsl" />

    <!-- Extract the dobject type -->
    <xsl:template name="dobject-common">
        <field name="id"><xsl:value-of select="//meta[@name='DC.Identifier']/@content" /></field>
        <xsl:call-template name="record_id" />
        <field name="title"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='title']" /></field>
        <field name="description"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='dodescription']" /></field>
        <field name="source"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='doreference']" /></field>
        <field name="source_link"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='doexternalurl']/a/@href" /></field>
        <field name="rights"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='dorights']" /></field>
        <xsl:for-each select="str:split(//dl[@class='content-summary']/dd[@class='dointepretation']/p, '; ')">
            <field name="tag"><xsl:value-of select="." /></field>
        </xsl:for-each>
        <field name="date_from">
            <xsl:value-of select="//dl[@class='content-summary']/dd[@class='dodate']/@standardfromdate" />
        </field>
        <field name="date_to">
            <xsl:value-of select="//dl[@class='content-summary']/dd[@class='dodate']/@standardtodate" />
        </field>
        <field name="date"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='dodate']" /></field>
        <field name="creator"><xsl:value-of select="//dl[@class='content-summary']/dd[@class='docreator']" /></field>
        <xsl:variable name="type" select="str:split(//meta[@name='DC.Title']/@content, ' - ')" />
        <field name="type"><xsl:value-of select="$type" /></field>
        <field name="dobject_type"><xsl:value-of select="$type" /></field>
        <field name="main_type">Digital Object</field>

        <field name="thumbnail">
            <xsl:call-template name="extract-link">
                <xsl:with-param name="link" select="//img[@id='dothumb']/@src"></xsl:with-param>
            </xsl:call-template>
        </field>
        <field name="fullsize">
            <xsl:call-template name="extract-link">
                <xsl:with-param name="link" select="//img[@id='dothumb']/../../a/@href"></xsl:with-param>
            </xsl:call-template>
        </field>
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
                    <xsl:when test="$components[2] = 'objects'">
                        <xsl:variable name="head" select="str:split(//meta[@name='DC.Identifier']/@content, '/objects')" />
                        <xsl:variable name="tail" select="str:split($link, 'objects')[2]" />
                        <xsl:value-of select="$head" />
                        <xsl:text>/objects</xsl:text>
                        <xsl:value-of select="$tail" />
                    </xsl:when>
                    <xsl:when test="$components[2] = 'assets'">
                        <xsl:variable name="head" select="str:split(//meta[@name='DC.Identifier']/@content, '/assets')" />
                        <xsl:variable name="tail" select="str:split($link, 'assets')[2]" />
                        <xsl:value-of select="$head" />
                        <xsl:text>/assets</xsl:text>
                        <xsl:value-of select="$tail" />
                    </xsl:when>
                    <xsl:when test="$components[2] = 'site'">
                        <xsl:variable name="head" select="str:split(//meta[@name='DC.Identifier']/@content, '/site')" />
                        <xsl:variable name="tail" select="str:split($link, 'site')[2]" />
                        <xsl:value-of select="$head" />
                        <xsl:text>/site</xsl:text>
                        <xsl:value-of select="$tail" />
                    </xsl:when>
                    <xsl:when test="$components[2] = 'image_viewer.htm?objects'">
                        <xsl:variable name="head" select="str:split(//meta[@name='DC.Identifier']/@content, '/objects')" />
                        <xsl:variable name="tail" select="str:split($link, 'objects')[2]" />
                        <xsl:value-of select="$head" />
                        <xsl:text>/objects</xsl:text>
                        <xsl:value-of select="str:split($tail, ',')[1]" />
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>