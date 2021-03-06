#!/usr/bin/python3

#By Grigorii Pechkovskii
'''

'''
print('start')

import re
import os
import sys
import argparse

import numpy as np
import pandas as pd

import pipeline_base

parser = argparse.ArgumentParser()
parser.add_argument('-x', '--xmfa',action='store', help='File xmfa')
parser.add_argument('-r', '--ref',action='store', help='Reference fasta')
parser.add_argument('-d', '--dir',action='store', help='Work directory')
parser.add_argument('-o', '--out-dir',action='store',default=os.getcwd(), help='Out directory')
parser.add_argument('-i', '--index-type',action='store',default='mauve', help="Index type 'mauve' or 'parsnp'")
parser.add_argument('-g', '--gbk-file',action='store',default='mauve', help='File gbk')
parser.add_argument('-n', '--name-vcf',action='store',default='test_mini.vcf', help='File gbk')

REF = parser.parse_args().ref
directory_file_xmfa = parser.parse_args().xmfa
directory  = parser.parse_args().dir
directory_out  = parser.parse_args().out_dir
file_gbk = parser.parse_args().gbk_file
index_type = parser.parse_args().index_type
name_vcf = parser.parse_args().name_vcf

if not os.access(directory_out,os.F_OK):
    os.mkdir(directory_out)

if True:
    directory = os.getcwd()
    #directory_file_xmfa = '/home/strain4/Desktop/xmfa_to_vcf/test_mini.xmfa'

    #directory_file_xmfa = directory + '/' + 'test_mini.xmfa'
    directory_file_xmfa = '/home/strain4/Desktop/fin_script/xmfa_to_vcf/exp_A2_group_0'

    REF = 'AmesAncestor_GCF_000008445.1'#test_mini
    #REF ='AmesAncestor_GCF_0000084451'
    REF = 'GCF_000008445.1_ASM844v1_genomic'#GI_AAJ_out1
    #REF = 'Ames_Ancestor_ref_GCF_000008445.1_ASM844v1_genomic.fna'#parsnp.xmfa
    directory_out = directory
    index_type = 'mauve'
    #name_vcf_simple = 'test_sim.vcf'
    file_gbk = '/home/strain4/Desktop/piplines/genomics_pipline_supply/' + 'AmesAncestor_GCF_000008445.1.gbk'
    file_gbk = os.path.join(os.path.split(directory)[0],'genomics_pipline_supply','AmesAncestor_GCF_000008445.1.gbk')
    name_vcf = 'test_exp_1_group_1.vcf'

    directory_exp_main = 'C:\\Users\\Grin\\Desktop\\remote_work\\exp_super2_4\\'
    directory_exp_files = [directory_exp_main + file_name +'/' + file_name for file_name in os.listdir(directory_exp_main) if 'group' in file_name]

    #file_vcf_for_check_un = '/home/strain4/Desktop/fin_script/GI_AAK_2/merged_final_exp_super2_4.vcf'

#some important options
sort = True
delete_ref = True
NORM = True

if index_type == 'parsnp':    
    pos_vcf = 1
    pos_minus = 1
elif index_type == 'mauve':
    pos_vcf = 0
    pos_minus = 2

def get_index(directory_file_xmfa,index_type):
    '''Iter on xmfa header(mauve format) with #
        and return dict with id(key) and name genome(values)
    '''
    file_xmfa = open(directory_file_xmfa)
    id_nameseq_dict = dict()

    if index_type == 'mauve':
        for file_line in file_xmfa:
            if '#' in file_line:
                find = re.search(r'Sequence(\d*)File\t(.*)\.',file_line)
            else:
                break
            if find != None:
                id_nameseq_dict[find.group(1)] = os.path.basename(find.group(2))

    if index_type == 'parsnp':
        find_id_lst = []
        find_genome_lst = []
        for file_line in file_xmfa:
            if '#' in file_line:
                #print(id_nameseq_dict)
                find_id = re.search(r'SequenceIndex\s(\d*)',file_line)
                find_genome = re.search(r'SequenceFile\s(.*)\.',file_line)#!\w replace .
            else:                
                id_nameseq_dict = dict(zip(find_id_lst,find_genome_lst))
                break

            if find_id != None:
                find_id_lst.append(find_id.group(1))
            if find_genome != None:
                find_genome_lst.append(find_genome.group(1))

            #if '>' in file_line:

                    
    file_xmfa.close()
    return id_nameseq_dict

#id_nameseq_dict = get_index(directory_file_xmfa,index_type)
#id_nameseq_dict_val = list(id_nameseq_dict.values())

def single_aln_generator(directory_file_xmfa):
    '''Generator for xmfa,
       get a directory_file_xmfa
       yield separate with = aln '''
    title_seq = []
    seq_seq = []
    single_aln = ''
    notfirst = False
    tmp = ''
    file_xmfa = open(directory_file_xmfa)    
    for line in file_xmfa:
        if '#' not in line and '=' not in line: #dont want make check for all string
            single_aln += line                
            if '>' in line:
                title_seq.append(line.strip())
                if notfirst:
                    seq_seq.append(tmp)
                    tmp = ''                
            else:
                notfirst = True
                tmp += line.strip().upper() #!up register 

        if '=' in line:
            seq_seq.append(tmp)
            tmp = ''
            notfirst = False
            yield title_seq , seq_seq
            title_seq = []
            seq_seq = []

    file_xmfa.close()


def parser_title(title_seq:list,directory_file_xmfa):
    '''Parsing > line
       get title_seq(> line)
       return positioin start - end sequence
       and name_idseq - name sequece from header name and id in > line
    '''

    id_nameseq_dict = get_index(directory_file_xmfa,index_type)
    id_nameseq_dict_val = list(id_nameseq_dict.values())

    position_every = []
    position_every_dict = dict()
    position_every_num_dict = dict()
    name_every = []
    id_strand = dict()
    name_strand = dict()
    for title in title_seq:

        id_search = re.search(r'(\d*):',title)
        id_seq = id_search.group(1)

        #!!!MAUVE
        #name_search = re.search(r'(/.*)\.',title)
        #name = name_search.group(1)
        #name = os.path.basename(name)
        #name_every.append(name)

        position_search = re.search(r'\d*:(\d*)-(\d*)\b',title)
        position = [position_search.group(1),position_search.group(2)]
        position_every += [position]

        #position_every_dict[name] = position

        position_every_num_dict[id_seq] = position

        strand_search = re.search(r'\s([\+-])\s',title_seq[0]).group(1)
        id_strand[id_seq] = strand_search


    #print(id_strand)
    name_seq_title = dict()
    #for sorting maybe!!
    for key,val in position_every_num_dict.items() :
        #print(id_nameseq_dict[key])
        name_seq_title[id_nameseq_dict[key]] = val#!id_nameseq_dict frome up namespace
        

    for key,val in id_strand.items():
        name_strand[id_nameseq_dict[key]] = val

    pos = list(name_seq_title.values())
    name_idseq = list(name_seq_title)
    strand = list(name_strand.values())
    #print(name_strand)
    #return name_every,position_every,position_every_dict,position_every_num_dict,pos,name_idseq
    return pos,name_idseq,strand



find_locus, find_source ,find_source_real = pipeline_base.contig_finder_gbk(file_gbk)


def aln_getter(query_pos,directory_file_xmfa,start_inter=100,end_inter=100,without_ref=False): 
    contig,position_real = pipeline_base.contig_definder(query_pos,find_locus,find_source)
    position_real = query_pos

    query_pos_init = query_pos
    start_inter_init = start_inter
    end_inter_init = end_inter

    for title_seq, seq_seq in single_aln_generator(directory_file_xmfa):
        #print(title_seq)

        pos_set = parser_title(title_seq,directory_file_xmfa)
        
        #print(pos_set[1])
        #print()
        #print(pos_set[1][1])

        if pos_set[1][0]!= REF or int(pos_set[0][0][1]) == 0 or len(pos_set[1]) == 1:
            print('WARNING pass aln',pos_set[1][0],pos_set[0][0][1])
            continue
        #if vcf_slice.loc[pos_set[1][1]] == '.':
        #    continue

        #if pos_set[1][0]== REF:
        else:
            #print(int(pos_set[0][0][0]), query_pos,int(pos_set[0][0][1]))
            if int(pos_set[0][0][0]) <= position_real <= int(pos_set[0][0][1]):
                pos = position_real - int(pos_set[0][0][0])
                pos_gapless = 0
                pos_full = 0

                if pos_set[2][0] == '-':
                    seq_seq = pipeline_base.seq_reverse(seq_seq)
                    #pos_set = list(pos_set)
                    #pos_set[0] = [ i[::-1] for i in pos_set[0]]
                    #pos_set = tuple(pos_set)
                    print('Warning reverse strand')

                for i in seq_seq[0]:#range(len(seq_seq[0])):
                    if i != '-':
                        pos_gapless += 1
                    if pos_gapless == pos or pos==0:#0
                        break
                    pos_full += 1 
                start_inter = pos_full - start_inter
                end_inter = pos_full + end_inter
                #print('pos_full=',pos_full,'pos_gapless=',pos_gapless)
                if start_inter<0:
                    start_inter = 0
                if end_inter > len(seq_seq[0])-1:
                    end_inter = len(seq_seq[0])-1
                fast_opened = open(contig + '_' +str(position_real) + '_variance' + '.fna','a')

                for n_seq in range(len(seq_seq)):
                    if without_ref and n_seq==0:
                        continue
                    else:
                        head = ' '.join(['>' + pos_set[1][n_seq],str(position_real),str(query_pos_init),str(start_inter_init),str(end_inter_init),'start_inter=' + str(start_inter),'end_inter=' + str(end_inter),title_seq[n_seq].replace('>','').replace(' ','_'),'\n'])
                        #head = ' '.join(['>',str(position_real),'start_inter=',str(start_inter),'end_inter',str(end_inter),'\n'])

                        fast_opened.write(head)
                        fast_opened.write(seq_seq[n_seq][start_inter:end_inter] + '\n')
                        #print('position_real=',position_real,'query_pos=',query_pos,
                        #    'start_inter=',start_inter,'end_inter=',end_inter,'len(seq_seq[0])-1',len(seq_seq[0])-1,
                        #    pos_set[1][n_seq])
                fast_opened.close()
                return

#vcf = pd.read_table(file_vcf_for_check_un)
#vcf.index = vcf['#CHROM'].astype(str) + '_' + vcf['POS'].astype(str) + '_' + vcf.index.astype(str)
#vcf_slice = vcf.loc['NC_007530_1334174_6691']

for directory_exp_file in directory_exp_files:    
    aln_getter(746456,directory_exp_file,start_inter=500,end_inter=2000,without_ref=True)

#1395979
#2534098
#4352218

print('end')
