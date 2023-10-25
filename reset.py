import evadb

cursor = evadb.connect().cursor()

cursor.query("DROP INDEX OMSCSDocPDFIndex").df()
cursor.query("DROP TABLE OMSCSDocPDF").df()