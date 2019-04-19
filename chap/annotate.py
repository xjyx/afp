#! /home/a_filipchyk/soft/home/a_filipchyk/anaconda3/bin/python
'''Annotates the discovered peaks'''

import argparse
import sys
import os
from collections import defaultdict
from bisect import bisect_right, bisect_left


import pandas as pd;
import numpy as np;
import matplotlib.pyplot as plt;
from pybedtools import BedTool

from afbio.pybedtools_af import construct_gff_interval

parser = argparse.ArgumentParser(description='Annotates the discovered peaks');
parser.add_argument('path', metavar = 'N', nargs = '?', type = str, help = "Path to the detected peaks");
parser.add_argument('--genes', nargs = '?', required=True, type = str, help = "Path to the gene annotation file");
parser.add_argument('--coverage', nargs = '?', type = str, help = "Path to the coverage track, bed format");
parser.add_argument('--overlap', nargs = '?', default=0.01, type = float, help = "Min overlap required overlap between a peak and genomic feature (as fraction of peak length)");
parser.add_argument('--maxshift', nargs = '?', default=50, type = int, help = "Max allowed shift (in nucleotides) of the peak top position downstream to start of the gene, to be still counted as peak upstream the gene");
parser.add_argument('--flen', nargs = '?', default=50, type = int, help = "Length of the peak\'s flanks to be included into analyses");
args = parser.parse_args();

#################################################################################################################################################################
### Read the input

genes = BedTool(args.genes);
peaks = BedTool(args.path);
offset = len(peaks[0].fields)
genes2annotation = dict([ (x.name, (x.attrs['annotation'], x.attrs['function']) ) for x in genes])
                        

#################################################################################################################################################################
### Get names of the overlapping genes

  
def get_gene_name(intersection, offset):
    attrs = dict( [x.strip().split('=') for x in intersection[offset+8].split(";")])
    return attrs['Name']

peak2genenames = defaultdict(list);
for el in peaks.intersect(genes, wo = True, f = args.overlap):
    peak2genenames[el.name].append(get_gene_name(el, offset))
    
    
if(peaks.file_type == 'gff'):
    for interval in peaks:
        interval.attrs['genes'] = ",".join(peak2genenames.get(interval.name, ['None']))
else:
    temp_peaks = []
    for interval in peaks:
        top = int(interval.name)
        start = max((top-args.flen,0))
        end = top+args.flen +1
        anint = construct_gff_interval(interval.chrom, start, end, 'peak', score=interval.score, strand=interval.strand, source='af_peak_detection', frame='.', attrs=[ ('Name', interval.name), ('genes', ",".join(peak2genenames.get(interval.name, ['None'])))])
        temp_peaks.append(anint)
    peaks = temp_peaks;
        
    
    

    
#################################################################################################################################################################
### Get coverage annotation
def annotate_coverage(interval, coverage, flen):
    top = int(interval.name)
    topcoverage = coverage[top]
    
    return topcoverage, start, end
 
if(args.coverage):
    coverage = pd.read_csv(args.coverage, sep="\t" , names = ["chr", "postion", "coverage"]).coverage.values

    for interval in peaks:
        topcoverage, start, end = annotate_coverage(interval, coverage, args.flen)
        interval.attrs['topcoverage'] =  "%1.3f" % topcoverage


   
#sys.exit()
    

  
#################################################################################################################################################################    
###Get closest genomic starts upstream to the dected peaks
#plusstarts = [x.start for x in genes if gene.strand == '+']
#minusstarts = [x.end-1 for x in genes if gene.strand == '-']

genestarts = [ (x.start, x.strand, x.name) if x.strand == '+' else (x.end-1, x.strand, x.name) for x in genes]


def findclosest(interval, genestarts, maxshift):
    pos = int(interval.name)
    raw_distances = [x[0]-pos if x[1] == '+' else pos-x[0] for x in genestarts];
    distances = [abs(x) if x > -maxshift else 10**8 for x in raw_distances]
    minindex = np.argmin(distances);
    start, strand, name = genestarts[minindex];
    return distances[minindex], name, strand
    

            
    
peak2genestarts = {}
for interval in peaks:
    ss_distance, ss_genename, ss_strand = findclosest(interval, genestarts, args.maxshift)
    interval.attrs['start_gene'] = ss_genename
    interval.attrs['start_gene_distance'] =  "%d" % ss_distance
    interval.attrs['start_gene_strand'] = ss_strand
    interval.attrs['start_annotation'], interval.attrs['start_function'] = genes2annotation[ss_genename]
    sys.stdout.write(str(interval))






