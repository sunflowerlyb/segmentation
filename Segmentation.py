#-*- coding:utf-8 -*-

import sys
import clean
import re
import os
import time
import recall_accuracy

#难点：处理歧义，未登录词的处理  
#基本算法为基于最大概率切分算法，要做到2－gram，3－gram均可，综合考虑召回率和准确率，取F值大的那个交叉验证 ,3-gram用删除插值算法解决概率为0的情况 
#本算法采取前向后向分别扫描，最大长度为5的，切词方式，这样会出现多种合理的组合，取所有组合中概率最大的那个， 
#其实可以用动态规划穷举法，也许正确率可以达到100%，but，效率太低了，时间复杂度指数增长 
#另一种方法，利用机器学习的方法，将分词转化为分类问题，将词分为，B,E,M,S四类，这种方法对未登录词和消岐效果不错，但是也是运算时间长

#对于未登录词 作为单独的词来处理， 采用 拉普拉斯加一平滑
#歧义消解：双向匹配最大概率 

def isWord(word):
	#return len(re.compile(u'[\u4E00-\u9FA5\uff21-\uff3a\uff41-\uff5a\uff10-\uff190-9a-zA-Z]').findall(word))
	return len(re.compile(u'[\u4E00-\u9FA5\uff21-\uff3a\uff41-\uff5aa-zA-Z]').findall(word))
	#所有的汉字和英文字母
def isDig(word):
 	#数字单独处理，比如1234，这样的数字，那么训练数据中也许没有，但是却应该按一个词算
 	return len(re.compile(u'[\uff10-\uff190-9]').findall(word))

class Segmentation(object):
	"""Chinese Segmentation"""

	def __init__(self):
		self.words = set()  #把每个词存入set
		self.sentence = str 
		self.count = 0#一共多少词，不可重复
		self.n_gram = 2 #ngram
		self.max_len = 5 #最大匹配的个数
		self.length = 0 #一共多少词，可重复

	def train(self, train_file, n, m):
		'''构造词典'''
		file_name = 'dealed_' + train_file

		try:
			file_open = open(file_name, 'r')
		except:
			file_name = clean.clean(train_file)
			file_open = open(file_name, 'r')

		file_read = file_open.read().decode('utf-8')
		self.sentence = file_read

		file_read = file_read.replace('\r\n',' ')
		file_read = file_read.replace('\n',' ')
		file_read = file_read.replace('#', '')
		file_read = file_read.replace('$', '')
		self.words = set(file_read.split(" "))
		
		self.n_gram = int(n)
		self.length = len(file_read.split(" "))
		self.count = len(self.words)
		self.max_len = int(m)

		file_open.close()

	def exists_words(self, words):
		'''查看某个词是否在词典中'''
		if words in self.words:
			return 1
		else:
			return 0

	def Probablity(self, list_seg, sentence):
	#计算某种切分的概率 , 

		list_seg.append(len(sentence) + 1)
		length = len(list_seg)
		sentence += u'$'
		str_temp = u'# '
		probablity = 1
		i = 0
		if self.n_gram > 1:
			while i < length - 1:
				probablity *= float(self.sentence.count(str_temp + sentence[list_seg[i]:list_seg[i + 1]] + ' ') + 1) / float(self.sentence.count(str_temp) + self.count)
				if i < self.n_gram - 2:
					str_temp += sentence[list_seg[i]:list_seg[i + 1]] + ' '
				else:
					str_temp = str_temp[1:len(str_temp)]
					str_temp = str_temp[str_temp.index(' '): len(str_temp)] + sentence[list_seg[i]:list_seg[i + 1]] + ' '
				i += 1		
		else:
			while i < length - 1:
				probablity *= float(self.sentence.count(sentence[list_seg[i]:list_seg[i + 1]] + ' ') + 1) / float(self.length + self.count)
				i += 1	
		return probablity

	def select_seq(self, list_coll, sentence):
		'''从各种切分方式中 找出切分句子概率最大的那个 序列'''

		probablity = -1
		list_temp = []
		for list_num in list_coll:
			p = self.Probablity(list_num, sentence)
			if probablity < p:
				list_temp = list_num
				probablity = p

		return list_temp

	def seg_result(self, list_r, sentence):
		'''根据最终的序列， 整理sentence的分词结果'''
		result = ''
		for i in range(0, len(list_r) - 1):
			result += sentence[list_r[i]:list_r[i + 1]] + ' '

		return result

	def tag(self, sentence):
		'''某句话分别用前向和后向切分方法，形成序列，若两个序列相同，则视为切分无歧义，直接返回该序列结果，若切分有歧义则计算概率'''
		seg_collect = []
		collect = []
		lenth = len(sentence)
		loc = 0

		while loc < lenth:#正向最大匹配
			collect.append(loc)
			j = self.max_len
			while j > 0:
				if loc + j <= lenth:
					if self.exists_words(sentence[loc:loc + j]):
						loc += j
						j = 0
				if j == 1:#单个词 
					loc += 1
				j -= 1

		collect.append(lenth)
		seg_collect.append(collect)
		collect = []
		loc = lenth

		while loc > 0:#逆向最大匹配
			collect.append(loc)
			j = self.max_len
			while j > 0:
				if loc - j >= 0:
					if self.exists_words(sentence[loc - j:loc]):
						loc -= j
						j = 0
				if j == 1:
					loc -= 1
				j -= 1

		collect.append(0)
		collect.sort()
		if collect not in seg_collect:
			seg_collect.append(collect)

		if len(seg_collect) == 1:
			return self.seg_result(seg_collect[0], sentence) #无歧义
		else:
			return self.seg_result(self.select_seq(seg_collect, sentence), sentence)

	def deal(self, sentences):
		sentence = '' #将每句分割成n个以标点符号为分割的小句子 
		count = 0
		sentence_tag = ''

		while sentences[count] != '$':

			while isWord(sentences[count]):
				sentence += sentences[count]
				count += 1

			sentence_tag += self.tag(sentence) #给某句话标注 
			sentence = ''
			
			tag = 1
			temp_word = sentences[count]
			while isDig(temp_word):
				#可以处理类似 12.6% 这样数字但是无法处理  一千二百元整  这样的情况
				if tag == 1 and len(sentence_tag) > 0 and sentence_tag[-1] != ' ':
					if(not re.compile(u'[' + sentence_tag[-1] +'\d' + ']').findall(self.sentence)):
						sentence_tag += ' '
				elif tag == 1 and len(sentence_tag) > 1 and sentence_tag[-2] != ' ' and sentence_tag[-1] == ' ':
					if(re.compile(u'[' + sentence_tag[-2] +'\d' + ']').findall(self.sentence)):
						sentence_tag = sentence_tag[:-1]

				sentence_tag += temp_word
				count += 1
				temp_word = sentences[count]
				if tag == 1:
					tag = 0

				if not isDig(temp_word):
					if len(re.compile(u'[' + '\d' + temp_word + ']').findall(self.sentence)):
						sentence_tag += temp_word #然而并不能处理双字单位的情况 
						tag = 1
					else:
						break
					count += 1
					temp_word = sentences[count]
				sentence_tag = sentence_tag.replace('  ',' ')

			if len(sentence_tag) > 0 and sentence_tag[-1] != ' ':
				sentence_tag += ' '

			if temp_word=='$':
				break
			elif not isWord(temp_word):#默认当作标点
				sentence_tag += temp_word + ' '
				count += 1
			sentence_tag = sentence_tag.replace('  ',' ')
		sentence_tag = sentence_tag.replace('  ',' ')
		return sentence_tag + '\n'

if __name__ == "__main__":

	if len(sys.argv) != 5:
		usage()
		sys.exit(2)

	try:
		file_train = sys.argv[1]
		file_tag = sys.argv[2]
		n_gram = sys.argv[3]
		if n_gram < 1:
			sys.stderr.write("please input  n_gram (>0) correctly ......")
			sys.exit(0)
		max_len = sys.argv[4]
		if max_len < 1:
			sys.stderr.write("please input  max_len (>0) correctly ......")
			sys.exit(0)
	except IOError:
		sys.stderr.write("ERROR: Cannot read inputfile %s.\n" % arg)
		sys.exit(1)

	#print 'begin time :', (time.strftime('%H:%M:%S'))

	train_file = Segmentation()
	print "collectting train data info ......"
	train_file.train(file_train, n_gram, max_len)
	print 'taging test data ......'

	result = open("result_n" + n_gram + 'ml' + max_len + '_' + file_tag, 'w')# 将结果写入文件
	test = open(file_tag, 'r')
	line = test.readline().decode('gbk')

	while line:
		sentences = line.replace("\r\n", '')
		sentences = sentences.replace('\n', '')
		sentences = sentences.replace(' ', '')
		sentences = sentences.strip()
		sentences = sentences + '$'
		
		text = train_file.deal(sentences)
		result.write(text.encode('utf-8'))
		line = test.readline().decode('gbk')

	print '------------------------------------------'
	print 'the result is saved in '+ "result_n" + n_gram + 'ml' + max_len + '_' + file_tag
	result.close()
	test.close()
	print 'comparing tag result with gold tag ......'
	print 'the result is below (recall_accuracy):'
	recall_accuracy.recall_accuracy('corpus_for_ass2GS.txt',"result_n" + n_gram + 'ml' + max_len + '_' + file_tag)

	#print 'end time :', (time.strftime('%H:%M:%S'))
