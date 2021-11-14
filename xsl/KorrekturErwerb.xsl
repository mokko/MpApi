<xsl:stylesheet version="2.0"
    xmlns:z="http://www.zetcom.com/ria/ws/module"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:func="http://func"
	exclude-result-prefixes="z">	

	<xsl:output method="html" encoding="UTF-8" indent="yes" />
    <xsl:strip-space elements="*" />
	
	<!-- 
		Erstellt eine HTML Liste zum Korreturlesen des Erwerbszusammenhangs
	-->

	<xsl:template match="/">
		<html>
			<head>
				<meta charset="utf-8"/>
				<title>Korrekturbogen Erwerbszusammenhang</title>
				<style>
				table, th, td{
					border-collapse: collapse;
				}
				td {
					padding-left:12px;
					padding-right:12px;
				}
				</style>
			</head>
			<body>
				<h1>Korrekturbogen Erwerbszusammenhang</h1>
				Input: 4-eröffnet.npx.xml<br/>
				<table border="1">
					<tr>
						<th>Identifikation</th>
						<th>Vorhandene Felder</th>
						<th>Satz</th>
						<th>Final</th>
					</tr>
					<xsl:apply-templates select="/z:application/z:modules/z:module[@name = 'Object']/z:moduleItem"/>
				</table>
			</body>
		</html>
	</xsl:template>

	<xsl:template match="/z:application/z:modules/z:module[@name = 'Object']/z:moduleItem">
		<tr>
			<td>
				<xsl:value-of select="z:dataField[@name = 'ObjObjectNumberTxt']"/>
				<xsl:text> / </xsl:text>
				<xsl:value-of select="@id"/>
			</td>
			<td><xsl:call-template name="Vorhandene"/></td>
			<td><xsl:call-template name="Satz"/></td>
			<td><xsl:call-template name="Ergebnis"/></td>
		</tr>
	</xsl:template>

	<xsl:template name="Vorhandene">
		<xsl:apply-templates select="z:repeatableGroup[@name = 'ObjAcquisitionDateGrp']"/>
		<xsl:apply-templates select="z:repeatableGroup[@name = 'ObjAcquisitionMethodGrp']"/>
		<xsl:apply-templates select="z:repeatableGroup[@name = 'ObjOwnerMethodGrp']"/>
		<xsl:apply-templates select="z:moduleReference[@name = 'ObjPerAssociationRef']/z:moduleReferenceItem[z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Veräußerer']"/>
		<xsl:apply-templates select="z:moduleReference[@name = 'ObjPerAssociationRef']/z:moduleReferenceItem[z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Verbesitzer']"/>
		<xsl:apply-templates select="z:repeatableGroup[@name = 'ObjAcquisitionSourcePerRef']"/>
		<xsl:apply-templates select="z:repeatableGroup[@name = 'ObjAcquisitionSourceGrp']"/>
		<xsl:apply-templates select="z:repeatableGroup[@name = 'ObjAcquisitionNotesGrp']"/>
	</xsl:template>
	
	<xsl:template name="Ergebnis">
		<xsl:choose>
			<xsl:when test="z:repeatableGroup[
				@name = 'ObjAcquisitionNotesGrp']/z:repeatableGroupItem[
				z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Ausgabe']">
				<xsl:value-of select="z:repeatableGroup[
					@name = 'ObjAcquisitionNotesGrp']/z:repeatableGroupItem[
					z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Ausgabe']/z:dataField"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="func:satz(.)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name="Satz">
		<xsl:value-of select="func:satz(.)"/>
	</xsl:template>

	<!-- Vorhandene -->
	<xsl:template match="z:repeatableGroup[@name = 'ObjAcquisitionDateGrp']">
		<xsl:text>Erwerb. Datum: </xsl:text>
		<br/>
		<xsl:for-each select="z:repeatableGroupItem">
			<xsl:text>-DateFromText:</xsl:text>
			<xsl:value-of select="z:dataField[@name = 'DateFromTxt']"/>
			<br/>
			<xsl:text>-DateTxt: </xsl:text>
			<xsl:value-of select="z:dataField[@name = 'DateTxt']"/>
			<br/>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="z:repeatableGroup[@name = 'ObjAcquisitionMethodGrp']">
		<xsl:text>Erwerbungsart: </xsl:text>
		<xsl:for-each select="z:repeatableGroupItem">
			<xsl:value-of select="z:vocabularyReference"/>
		</xsl:for-each>
		<br/>
	</xsl:template>

	<xsl:template match="z:repeatableGroup[@name = 'ObjOwnerMethodGrp']">
		<xsl:text>Besitzart: </xsl:text>
		<xsl:for-each select="z:repeatableGroupItem">
			<xsl:value-of select="z:vocabularyReference"/>
		</xsl:for-each>
		<br/>
	</xsl:template>

	<xsl:template match="z:repeatableGroup[@name = 'ObjAcquisitionNotesGrp']">
		<xsl:text>ErwerbNotiz</xsl:text>
		<br/>
		<xsl:for-each select="z:repeatableGroupItem">
			<xsl:text>-</xsl:text>
			<xsl:value-of select="z:vocabularyReference"/>
			<xsl:text>: </xsl:text>
			<xsl:value-of select="z:dataField"/>
			<br/>
		</xsl:for-each>
		<br/>
	</xsl:template>

	<xsl:template match="z:moduleReference[@name = 'ObjPerAssociationRef']/z:moduleReferenceItem[
		z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Veräußerer']">
		<xsl:text>PKVeräußerer: </xsl:text>
		<xsl:value-of select="z:formattedValue"/>
		<xsl:text> [kueId:</xsl:text>
		<xsl:value-of select="@moduleItemId"/>
		<xsl:text>]</xsl:text>
		<br/>
	</xsl:template>

	<xsl:template match="z:moduleReference[@name = 'ObjPerAssociationRef']/z:moduleReferenceItem[
		z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Vorbesitzer']">
		<xsl:text>PKVerbesitzer: </xsl:text>
		<xsl:value-of select="z:formattedValue"/>
		<xsl:text> [kueId:</xsl:text>
		<xsl:value-of select="@moduleItemId"/>
		<xsl:text>]</xsl:text>
		<br/>
	</xsl:template>

	<!--field "Erwerb. von" in register 4, untested b/c no data-->
	<xsl:template match="z:repeatableGroup[@name = 'ObjAcquisitionSourceGrp']">
		<xsl:text>Erwerb. von  (r4): </xsl:text>
		<xsl:for-each select="z:repeatableGroupItem">
			<xsl:value-of select="z:vocabularyReference"/>
		</xsl:for-each>
		<br/>
	</xsl:template>

	<!--field Veräußerer in register 4, untested b/c no data-->
	<xsl:template match="z:repeatableGroup[@name = 'ObjAcquisitionSourcePerRef']">
		<xsl:text>Veräußerer (r4): </xsl:text>
		<xsl:for-each select="z:repeatableGroupItem">
			<xsl:value-of select="z:vocabularyReference"/>
		</xsl:for-each>
		<br/>
	</xsl:template>


	<xsl:function name="func:satz">
		<xsl:param name="context"/>
		<xsl:for-each select="$context">	

			<!--ART-->
			<xsl:variable name="art2" select="normalize-space(z:repeatableGroup[
				@name = 'ObjAcquisitionMethodGrp']/z:repeatableGroupItem/z:vocabularyReference)"/>

			<xsl:variable name="art"> 
				<xsl:choose>
					<xsl:when test="$art2 eq 'Zugang ungeklärt (Expedition)'">
						<xsl:text>unbekannten Zugang (Expedition)</xsl:text>
					</xsl:when>
					<xsl:when test="$art2 eq 'Unbekannt'">
						<xsl:text>unbekannte Erwerbungsart</xsl:text>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="$art2"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>


			<!--DATUM-->

			<xsl:variable name="DateFromTxt" select="normalize-space(z:repeatableGroup[
				@name = 'ObjAcquisitionDateGrp']/z:repeatableGroupItem/z:dataField[
				@name = 'DateFromTxt']/z:value)"/>
			<xsl:variable name="DateTxt" select="normalize-space(z:repeatableGroup[
				@name = 'ObjAcquisitionDateGrp']/z:repeatableGroupItem/z:dataField[
				@name = 'DateTxt']/z:value)"/>

			<xsl:variable name="datum">
				<xsl:choose>
					<xsl:when test="$DateTxt ne ''">
						<xsl:value-of select="$DateTxt"/>
					</xsl:when>
					<xsl:when test="$DateFromTxt ne ''"> 
						<xsl:value-of select="$DateFromTxt"/>
					</xsl:when>
				</xsl:choose>
			</xsl:variable>

			<xsl:variable name="datum2">
				<xsl:choose>
					<xsl:when test="matches($datum, '^(\d+)\.(\d+)\.\d\d\d\d')">
						<xsl:text>am </xsl:text>
						<xsl:value-of select="$datum"/>
					</xsl:when>
					<xsl:when test="matches($datum, ' \(um\)')">
						<xsl:text>um </xsl:text>
						<xsl:value-of select="substring-before($datum, ' (um)')"/>
					</xsl:when>
					<xsl:when test="matches($datum, ' \(\?\)')">
						<xsl:value-of select="substring-before($datum, ' (?)')"/>
						<xsl:text> (Datum fraglich)</xsl:text>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="$datum"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<xsl:message>
				<xsl:value-of select="$datum"/>
				<xsl:text>::</xsl:text>
				<xsl:value-of select="$datum2"/>
			</xsl:message>

			<!--VON-->

			<xsl:variable name="ErwerbNotizErwerbungVon" select="z:repeatableGroup[
				@name = 'ObjAcquisitionNotesGrp']/z:repeatableGroupItem[
				z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Erwerbung von']/z:dataField"/>
			<xsl:variable name="PKVeräußerer">
				<xsl:for-each select="z:moduleReference[
					@name = 'ObjPerAssociationRef']/z:moduleReferenceItem[
					z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Veräußerer']/z:formattedValue">
					<xsl:value-of select="substring-before(., ' (')"/>
				</xsl:for-each>
			</xsl:variable>
			<xsl:variable name="PKVerbesitzer">
				<xsl:for-each select="z:moduleReference[
					@name = 'ObjPerAssociationRef']/z:moduleReferenceItem[
					z:vocabularyReference/z:vocabularyReferenceItem/z:formattedValue = 'Vorbesitzer']/z:formattedValue">
					<xsl:value-of select="substring-before(., ' (')"/>
				</xsl:for-each>
			</xsl:variable> 
			<!--xsl:if test="$PKVeräußerer ne ''">
				<xsl:message>
					<xsl:text>PKVeräußerer: </xsl:text>
					<xsl:value-of select="$PKVeräußerer"/>
				</xsl:message>
			</xsl:if-->

			<xsl:variable name="von">
				<xsl:choose>
					<xsl:when test="normalize-space($PKVeräußerer) ne ''">
						<xsl:value-of select="normalize-space($PKVeräußerer)"/>	
					</xsl:when>
					<xsl:when test="normalize-space($PKVerbesitzer) ne ''">
						<xsl:value-of select="normalize-space($PKVerbesitzer)"/>	
					</xsl:when>
					<xsl:when test="normalize-space($ErwerbNotizErwerbungVon) ne ''">
						<xsl:value-of select="normalize-space($ErwerbNotizErwerbungVon)"/>	
					</xsl:when>
				</xsl:choose>
			</xsl:variable>

			<!--Return Satz-->
			<xsl:if test="$art ne '' or $von ne '' or $datum2 ne ''">
				<xsl:choose>
					<xsl:when test="$art eq 'Leihe' or $art eq 'Dauerleihgabe'">
						<xsl:value-of select="$art"/>
					</xsl:when>
					<xsl:when test="$art ne ''">
						<xsl:text>erworben durch </xsl:text>
						<xsl:value-of select="$art"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:text>erworben </xsl:text>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:if test="$von ne ''">
					<xsl:text> von </xsl:text>
					<xsl:value-of select="$von"/>
				</xsl:if>
				<xsl:if test="$datum2 ne ''">
					<xsl:text> </xsl:text>
					<xsl:value-of select="$datum2"/>
				</xsl:if>
			</xsl:if>
		</xsl:for-each>
	</xsl:function>		
</xsl:stylesheet>