import sys
import os
import dominate
import argparse
from collections import defaultdict
from dominate.tags import *
from dominate.util import raw


from afbio.html.methods import add_ucsc
from math import log

parser = argparse.ArgumentParser(description='Generates html report of CHAP analyses by chipchap.py');
parser.add_argument('path', metavar = 'N', nargs = '?', type = str, help = "Path to the log folder");
#parser.add_argument('--genome', nargs = '?', required=True, type = str, help = "Path to the genome, fasta format");
#parser.add_argument('--js', nargs = '?', required=True, type = str, help = "Path to javascript functions");
parser.add_argument('--css', nargs = '?', required=True, type = str, help = "Path to css style sheet");
#parser.add_argument('--ucsc', nargs = '?', required=True, type = str, help = "Name of the UCSC session");
#parser.add_argument('--flank', nargs = '?', default=60, type = int, help = "Peak plank length");
args = parser.parse_args();

#name = args.path.split("/")[-2]
name = os.path.realpath(args.path).split("/")[-1]
log_file = os.path.join(args.path, "log.txt")
#sys.stderr.write("%s\n" % name)


#print(args.css)
#sys.exit()


section2text = {} #defaultdict(list);
section = ""
with open(log_file) as f:
    for l in f:
        if(l.startswith("###")):
            section = l.strip()[3:];
            section2text[section] = [];
        elif(section):
            section2text[section].append(l.strip())
            
            
### BOWTIE2 processing ###
bowtie_labels = ["Total reads", "Mapped uniquely", "Mapped non-uniquely", "Unmapped reads", "Mapped Discordantly"]

def get_bowtie(name):
    bowtie_list = [];
    
    ltemp = section2text[name][1:8]
    for l in (ltemp[:4] + ltemp[6:]):
        bowtie_list.append(int(l.split(" ")[0]))
        
    bowtie_list[1] -= bowtie_list[4]
    bowtie_list[1], bowtie_list[2], bowtie_list[3] = bowtie_list[2], bowtie_list[3], bowtie_list[1]
    return bowtie_list, bowtie_list[0]

bowtie_list, bowtie_total = get_bowtie('bowtie')
if('bowtie_control' in section2text):
    bowtie_control_list, bowtie_control_total = get_bowtie('bowtie_control')
else:
    bowtie_control_list = [];





### Detect peaks processing
#coverage_list = [];
detection_list = [];
detection_labels = ["Median Coverage", "Mean Coverage", "STD Coverage", "Maximum Coverage", "Strong Peaks Detected", "Strong Peaks Bandwidth", "Total Peaks Detected"]
for l in (section2text['detect_peaks']):
    if(l):
        a = l.split("\t")
        #print(a)
        if(not a[0].startswith("WARNING") and len(a)>1):
            detection_list.append(float(a[1]))
detection_list = detection_list[:6] + detection_list[7:]
detection_list[4], detection_list[5] = detection_list[5], detection_list[4]
detection_units = ['', ' nt', '']


### Filter peaks processing
#coverage_list = [];
filter_list = [];
filter_labels = ["Initial Median Score", "Fitted Mean Score", "Fitted STD Score", "Score Threshold", "Mean Coverage", "Coverage Threshold", "Total Peaks", "Filtered by Score", "Filtered by Coverage", "num of re-centered peaks"]
for l in (section2text['filter_peaks']):
    if(l):
        filter_list.append(float(l.split("\t")[1]))
        
filter_list = [filter_list[0], filter_list[3], filter_list[4], filter_list[5], detection_list[1], filter_list[10], filter_list[6], filter_list[7], filter_list[12], filter_list[13] ]
filter_total = filter_list[6]



        






########### HTML SECTION ###########
doc = dominate.document(title="CHAP analyses overview for the sample \"%s\"" % name)
with open(args.css) as f:
    _style = f.read()
with doc.head:
    style(_style)
    
with doc:
    p(strong("Mapping Results", style= 'font-size: 16pt'))
    with table(style= 'font-size: 14pt') as _table:
        for label, value in zip(bowtie_labels, bowtie_list):
            with tr():
                td(label)
                td('{:,}'.format(value))
                td("%1.2f%%" % (value/bowtie_total*100))
                
    with div(cls="row", style="display: flex"):
        with div(cls="column", style="padding: 5px; flex:50%"):
            img(src= '%s.scores.png' % name, alt="Snow", style="width:100%")
        with div(cls="column", style="padding: 5px; flex:50%"):
            img(src='%s.fragment_lengthes.png' % name, alt="Snow", style="width:100%")
    br()
    br()
    if(bowtie_control_list):
        p(strong("Genomic Control", style= 'font-size: 16pt'))
        with table(style= 'font-size: 14pt') as _table:
            for label, value in zip(bowtie_labels, bowtie_control_list):
                with tr():
                    td(label)
                    td('{:,}'.format(value))
                    td("%1.2f%%" % (value/bowtie_control_total*100))
        
        with div(cls="row", style="display: flex"):
            img(src='control_coverage.png', alt="Snow", style="width:75%")

        br()
        br()        
    
    p(strong("Genomic Coverage", style= 'font-size: 16pt'))
    with table(style= 'font-size: 14pt') as _table:
        for label, value in zip(detection_labels[:4], detection_list[:4]):
            with tr():
                td(label)
                td("%d" % (value))
                
    br()
    br()
    p(strong("Peak detection", style= 'font-size: 16pt'))
    with table(style= 'font-size: 14pt') as _table:
        for label, value, unit in zip(detection_labels[4:], detection_list[4:], detection_units):
            with tr():
                td(label)
                td("%s%s" % ('{:,}'.format(int(value)), unit))
                
    br()
    br()
    p(strong("Peak Filtering Analyses", style= 'font-size: 16pt'))
    with table(style= 'font-size: 14pt') as _table:
        for label, value in zip(filter_labels[:6], filter_list[:6]):
            with tr():
                td(label)
                td("%d" % value)
    with div(cls="row", style="display: flex"):
        with div(cls="column", style="padding: 5px; flex:50%"):
            img(src='convolution.png', alt="Snow", style="width:100%")
        with div(cls="column", style="padding: 5px; flex:50%"):
            img(src='filtering.png', alt="Snow", style="width:100%")
    br()
    br()
    p(strong("Peak Filtering Results", style= 'font-size: 16pt'))
    with table(style= 'font-size: 14pt') as _table:
        for label, value in zip(filter_labels[6:], filter_list[6:]):
            with tr():
                td(label)
                td('{:,}'.format(int(value)))
                td("%1.2f%%" % (value/filter_total*100))
    br()
    br()
    p(strong("Peaks Annotation", style= 'font-size: 16pt'))
    with div(cls="row", style="display: flex"):
        with div(cls="column", style="padding: 5px; flex:50%"):
            img(src='peak_genomic_types.svg', alt="Snow", style="width:100%")
        with div(cls="column", style="padding: 5px; flex:50%"):
            img(src='peak_coverage_scores.svg', alt="Snow", style="width:100%")
    br()
    br()
    p(strong("Peaks Top Coverage", style= 'font-size: 16pt'))
    with div(cls="row", style="display: flex"):
        img(src='topcoverage_hist.svg', alt="Snow", style="width:100%")    
    br()
    br()
    p(strong("Peaks TSS distance", style= 'font-size: 16pt'))
    with div(cls="row", style="display: flex"):
        img(src='tss_hist.svg', alt="Snow", style="width:100%")



print(doc.render());










'''357955 reads; of these:
  357955 (100.00%) were paired; of these:
    31369 (8.76%) aligned concordantly 0 times
    321179 (89.73%) aligned concordantly exactly 1 time
    5407 (1.51%) aligned concordantly >1 times
    ----
    31369 pairs aligned concordantly 0 times; of these:
      1049 (3.34%) aligned discordantly 1 time
91.53% overall alignment rate
'''
