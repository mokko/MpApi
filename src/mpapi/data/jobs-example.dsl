#back to dsl again
#indent is important: \t or four spaces
#disadvantage of this method is that we have to write every step to disk
HFObjekte: # job label
	getPackage exhibit 20222 M39
	getPackage exhibit 20219 SM-Afrika
	getPackage exhibit 20220 SM-Amerika
	getPackage exhibit 20223 SM-Südsee
	getPackage exhibit 21822 Amerika-Ausstellung
	getPackage exhibit 20215 Südsee-Ausstellung
	getPackage exhibit 20226 Afrika-Ausstellung	

Test:
	getItem Object 2609893 objects2609893.xml # make sure is an object with an attachment
