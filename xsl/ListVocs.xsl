<xsl:stylesheet version="2.0"
    xmlns:z="http://www.zetcom.com/ria/ws/module"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xs="http://www.w3.org/2001/XMLSchema"
	xmlns:func="http://func"
	exclude-result-prefixes="z">	

	<xsl:output method="xml" encoding="UTF-8" indent="yes" />
    <xsl:strip-space elements="*" />

	<!-- 
		Input: zml
		Output: a list of vocabularies used, preferrably with the fields in which they are used
		We want every instance only once. 
	-->
	
	<xsl:template match="/">
		<xsl:for-each-group select="//@instanceName" group-by=".">
			<xsl:sort select="."/>
			<xsl:message>
				<xsl:value-of select="name(current-group()[1]/../../..)"/>
				<xsl:text>.</xsl:text>
				<xsl:value-of select="current-group()[1]/../../../@name"/>
				<xsl:text>.</xsl:text>
				<xsl:value-of select="."/>
			</xsl:message>
		</xsl:for-each-group>
	</xsl:template>

</xsl:stylesheet>