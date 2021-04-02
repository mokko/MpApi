#back to dsl again
#indent is important; \t or four space
HFObjekte:                  			# job label
	getObjects:             			# command with multiple lines
		exhibitId 20222 1   			# writes search1.xml, response1.xml
		groupId 30639 2      			# writes search2.xml, response2.xml
	join response-join.xml  			# joins response*.xml
	clean response-join.xml response-clean.xml # in out
	validate response-clean.xml 		# in
	digitalAssets response-clean.xml	# in
OtherJob:
	getObjects:         
		exhibitId 20222 
		groupId 1234
	getObjectsExhibit 20222 response0.xml
	getObjectsGroup 1234 response1.xml
	join response1.xml response2.xml > response-join.xml
	getObjects arg1 arg2
	clean response-clean.xml
	validate 
	digitalAssets response-clean.xml

#getObjects(exhibitId="20222")
#getObjects(groupId="1234")
#clean("response-clean.xml")
#validate()
#digitalAssets("response-clean.xml")	 