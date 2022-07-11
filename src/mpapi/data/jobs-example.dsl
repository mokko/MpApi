#back to dsl again
#indent is important: \t or four spaces
#disadvantage of this method is that we have to write every step to disk
HFObjekte: # job label
	getPack exhibit 20222 M39
	getPack exhibit 20219 SM-Afrika
	getPack exhibit 20220 SM-Amerika
	getPack exhibit 20223 SM-Südsee
	getPack exhibit 21822 Amerika-Ausstellung
	getPack exhibit 20215 Südsee-Ausstellung
	getPack exhibit 20226 Afrika-Ausstellung	

Test:
	getItem Object 2609893 objects2609893.xml # make sure is an object with an attachment
