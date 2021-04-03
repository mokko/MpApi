#back to dsl again
#indent is important: \t or four spaces
HFObjekte:                  			# job label
	getObjects:             			# command with multiple lines
		exhibitId 20222 1   			# writes search1.xml, response1.xml
		groupId 26852 2      			# writes search2.xml, response2.xml
	getItem Object 2609893 objects2609893.xml # make sure is an object with an attachment
	join objects*.xml objects-join.zml	# writes objects*.xml to objects-join.xml
	getMultimedia objects-join.zml		# gets a lot of mm12345.xml files
	join *.xml mm-join.zml				# do we need everything in one file?
	clean mm-join.zml mm-clean.zml 		# in->out; includes validation
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
	multimedia response-clean.xml
Test:
	join
