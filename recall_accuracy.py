#-*- coding:utf-8 -*-

import sys

def recall_accuracy(gold_file, test_file):
	file_open_gold = open(gold_file)
	file_open_test = open(test_file)

	gold_file_read = file_open_gold.readline().decode('gbk')
	test_file_read = file_open_test.readline().decode('utf-8')
	total_gold = 0
	total_test = 0
	accuray = 0

	while test_file_read and gold_file_read:
		test_read = test_file_read.strip()
		gold_read = gold_file_read.strip()

		test_split = test_read.split(' ')
		gold_split = gold_read.split(' ')
		if cmp(test_read, gold_read) == 0:
			accuray += len(test_split)
		else:
			accuray += len(test_split) - len([word for word in test_split if word not in gold_split])

		total_test += len(test_split)
		total_gold += len(gold_split)
		gold_file_read = file_open_gold.readline().decode('gbk')
		test_file_read = file_open_test.readline().decode('utf-8')

	c_prec = (float)(accuray) / (float)(total_test)
	c_rec = (float)(accuray) / (float)(total_gold)
	fscore = (float)(2 * c_prec * c_rec)/(float)(c_prec + c_rec)

	print "\t precision \trecall \t\tF1-Score"
	print "evalute: %f\t%f\t%f" % (c_prec, c_rec, fscore)

if __name__ == '__main__':
	
	if len(sys.argv) != 3:
		sys.exit(2)

	try:
		gold_file_name = sys.argv[1]
		test_file_name = sys.argv[2]
	except IOError:
		sys.stderr.write("ERROR: Cannot read inputfile %s.\n" % arg)
		sys.exit(1)

	recall_accuracy(gold_file_name, test_file_name)