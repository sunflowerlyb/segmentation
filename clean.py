#-*- coding: utf-8 -*-
import re
import sys

def isWord(word):
	return len(re.compile(u'[\u4E00-\u9FA5\uff21-\uff3a\uff41-\uff5a\uff10-\uff19a-zA-Z0-9]').findall(word))

def clean(file_name):
	file_open = open(file_name, 'r')
	file_o = open('dealed_' + file_name, 'w')
	read_line = file_open.readline()

	while read_line:
		read_line = read_line.decode('gbk')
		#read_line = read_line.replace('\r\n','')
		#read_line = read_line.replace('\n','')
		readline = read_line.strip()

		length = len(readline)
		i = 0
		sentence = ''
		flag = 0
		while i < length:
			if isWord(readline[i]) or readline[i] == ' ':
				sentence += readline[i]
				flag = 1
			else:
				if flag == 1:
					sentence = sentence.strip()
					if len(sentence) != 0:
						sentence = '# ' + sentence + ' $\n'
						file_o.write(sentence.encode('utf-8'))
						flag = 0
				sentence = ''
			i += 1
		read_line = file_open.readline()
	file_open.close()
	file_o.close()
	return 'dealed_' + file_name

if __name__ == '__main__':
	file_result = clean('corpus_for_ass2train.txt')