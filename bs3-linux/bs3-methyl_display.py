import sys, gzip, pickle, scipy.stats, pdb
import numpy as np
from math import log
from scipy.cluster.hierarchy import dendrogram, linkage
import pdb
from optparse import OptionParser
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy
import subprocess

class Species:

        def __init__(self, mfile, gene_file, transposon, gene):

                self.raw = {}
		self.gene_map = {}
		self.transposon_map = {}
		self.gene = gene
		self.methyl_level = {}
		self.mlevel = {}
		self.nlevel = {}
		#self.label = label
		self.transposon = transposon
		#gene_file = True
                #read in CG file
		f = open(mfile)
                cg_raw = f.read().splitlines()
                f.close()
		


                for line in cg_raw:
			#print line
                        tmp = line.split()
                        chromosome = tmp[0]
			strand = tmp[1]
                        position = int(tmp[2])
                        mtype = tmp[3]
                        mlevel = float(tmp[5])

                        if chromosome not in self.raw:
                                self.raw[chromosome] = {}
                        self.raw[chromosome][position] = [strand, position, mtype, mlevel]
		
		
		#read in Gene file
		if gene_file == None:
			self.gene = False
			return

		f = open(gene_file)
		gene_raw = f.read().splitlines()
		f.close()
		

		for line in gene_raw:

			if len(line) == 0:
				continue

			if  line[0] == '#':
				continue

			elif line.split()[2] == 'gene' :
				self.parse_genome_info(line, self.gene_map)

			elif (line.split()[2] =='repeat_region') & (line.split()[1] == 'repeatmasker'):
				self.parse_genome_info(line, self.transposon_map)
		
			else:
				continue
	
	def parse_genome_info(self, line, region):

		tmp = line.split()
                gene_id = str(tmp[8].split('=')[1].split(';')[0])
                strand = str(tmp[6])
                start = int(tmp[3])
                stop = int(tmp[4])
                chromosome = str(tmp[0])
                region[gene_id] = [start, stop, strand, chromosome]
	
	#def parse_genome_info(self, line, region):
		
	#tmp = line.split()
		
	def region_interval(self, head, end, nbin):

		interval = [int(head + i * (end - head)/nbin) for i in range(nbin)]
		interval.append(end) 
		return interval

	def calculate_mlevel(self, nbin):
		
		mlevel = {}
		nlevel = {}
		for mtype in ['CG', 'CHH', 'CHG']:
			self.mlevel[mtype] = {}
			mlevel[mtype] = [0] * (nbin*4)
			nlevel[mtype] = [0] * (nbin*4)
	 
		
		if self.gene == True:
			self.tabulate_rate_gene_map(self.gene_map, mlevel, nlevel, nbin)
	
		if self.transposon == True:
			self.tabulate_rate_gene_map(self.transposon, mlevel, nlevel, nbin)

		if self.gene != True:
			
			for chromosome in self.raw:
				full_len = max(self.raw[chromosome].keys())
				interval = self.region_interval(0, full_len, 80)

				mlevel = {}
                		nlevel = {}

                		for mtype in ['CG', 'CHH', 'CHG']:
                        		mlevel[mtype] = [0] * (80)
                        		nlevel[mtype] = [0] * (80)
			
				self.tabulate_rate(interval, mlevel, nlevel, chromosome)	
				
				
				for mtype in self.mlevel.keys():
					#pdb.set_trace()
					if mtype not in self.methyl_level:
						self.methyl_level[mtype] = [ 0.0  if (nlevel[mtype][i] == 0) else mlevel[mtype][i] / nlevel[mtype][i] for i in range(len(mlevel[mtype]) - 1) ]
						continue
                        		self.methyl_level[mtype] += [ 0.0  if (nlevel[mtype][i] == 0) else mlevel[mtype][i] / nlevel[mtype][i] for i in range(len(mlevel[mtype]) - 1) ]
	        self.to_graph()	
		for mtype in self.methyl_level:			
			methyl = '\n'.join([str(i) for i in self.methyl_level[mtype]])
	        	with open(mtype + '_' + sys.argv[1], 'w') as file:
                                file.write(methyl)

                        file.close()

		return
		#for mtype in self.mlevel.keys():
		#	self.methyl_level[mtype] = [ 0.0  if (nlevel[mtype][i] == 0) else mlevel[mtype][i] / nlevel[mtype][i] for i in range(len(mlevel[mtype]) - 1) ]	
		self.raw = None
                self.gene_map = None
    		self.print_mlevel(mlevel, nlevel) 

	def to_graph(self):
	
                annot = ['c', 'r', 'b']
                fig, ax = plt.subplots()
		for i, mtype in enumerate(self.methyl_level):
                        ax.plot(numpy.array(self.methyl_level[mtype]), annot[i], label=mtype)
			
                plt.ylabel('CG Methylation Level', fontsize=14)
		plt.tick_params(
    			axis='x',          # changes apply to the x-axis
    			which='both',      # both major and minor ticks are affected
    			bottom='off',      # ticks along the bottom edge are off
    			top='off',         # ticks along the top edge are off
    			labelbottom='off')
                plt.axvline(20, color='k', linestyle='dashed', linewidth=2)
                plt.axvline(60, color='k', linestyle='dashed', linewidth=2)
		plt.xlabel('Upstream------------|-----------------Gene Body-------------------|--------Downstream')
		legend = ax.legend(loc='upper right', shadow=True, fontsize=14)
		fig.savefig('metaplot.png', dpi=600)
		
	def tabulate_rate_gene_map(self, region, mlevel, nlevel, nbin):

		for gene in region:

                   	chromosome = region[gene][3]
                        strand = region[gene][2]
                        gap = abs(region[gene][0] - region[gene][1]) * .5
                        head = int(region[gene][0] - gap)
                        end = int(region[gene][1] + gap)
                        upstream = self.region_interval(head, region[gene][0], nbin)
			upstream.pop(-1)
                        gene_body = self.region_interval(region[gene][0], region[gene][1],  2 * nbin)
                        downstream = self.region_interval(region[gene][1], end,  nbin)
			downstream.pop(0)

                        if strand == '+':
                 	       intervals = upstream + gene_body + downstream
                
		        else:
                        	intervals = downstream[::-1] + gene_body[::-1] + upstream[::-1]

                        self.tabulate_rate(intervals, mlevel, nlevel, chromosome)
			
		#	pdb.set_trace()

        	for mtype in self.mlevel.keys():
                	self.methyl_level[mtype] = [ 0.0  if (nlevel[mtype][i] == 0) else mlevel[mtype][i] / nlevel[mtype][i] for i in range(len(mlevel[mtype]) - 1) ]

	def tabulate_rate(self, intervals, mlevel, nlevel, chromosome):

		for k in range(len(intervals) - 1):

                	for i in range(min(intervals[k], intervals[k + 1]), max(intervals[k], intervals[k + 1])):

                        	if chromosome not in self.raw :
                                	continue
	
                                if (i in self.raw[chromosome] ) & (i > 0) :
                               		
					if self.raw[chromosome][i][2] in self.mlevel:
											
                                        	mlevel[self.raw[chromosome][i][2]][k] += self.raw[chromosome][i][3]
                                              	nlevel[self.raw[chromosome][i][2]][k] += 1
	
		


	
	def log_normalize(self):

		for mtype in self.mlevel.keys():
                        self.methyl_level[mtype] = [ log(self.methyl_level[mtype][i]) for i in range(len(self.methyl_level[mtype]) - 1) ]
	
	def normalize(self):

		max_all = max(self.methyl_level[mtype])

		for mtype in self.mlevel.keys():
			self.methyl_level[mtype] = [ self.methyl_level[mtype][i] / max_all for i in range(len(self.methyl_level[mtype]) - 1) ]	

	def mean_filter(self, step):

		step = step / 2

		for mtype in self.mlevel.keys():
			self.methyl_level[mtype] = [ self.methyl_level[mtype][i]  if (i < step) | (i >=  len(self.methyl_level[mtype] ) - step) else sum(self.methyl_level[mtype][i - step:i+step])/ (step * 2 + 1) for i in range(len(self.mlevel[mtype]) - 1) ]
							
	def print_mlevel(self, mlevel, nlevel):
	
		for mtype in mlevel:
			methyl = '\n'.join([ '0.0'  if (nlevel[mtype][i] == 0) else str(mlevel[mtype][i] / nlevel[mtype][i]) for i in range(len(mlevel[mtype]) - 1) ])
			
			with open(mtype + '_' + sys.argv[1], 'w') as file:
				file.write(methyl)		
			
			file.close()


def read_species_list():
	
	f = open(sys.argv[4])
        Species  = f.read().splitlines()
        f.close()
	Mlevel = []

	nSpecies = 0
	for species in Species:
		organism = species.split()
		if len(organism) < 2:
			Mlevel.append(Species(organism[0], None))
		else:
			Mlevel.append(Species(organism[0], organism[1]))
		Mlevel[nSpecies].calculate_mlevel(nbin)
		
		nSpecies += 1

	return Mlevel
		
def unconversion(file):
        
	unconverted = []
	for line in open(file):
		tmp = line.split()
                unconverted.append(float(tmp[6]) / (tmp[6] + tmp[7]))
        
	unconverted = np.array(unconverted)	
	print unconverted
	plt.hist(unconverted, bins=[float(i) * .01 for i in xrange(0, 105, 5)])
        print np.average(unconverted) 
	plt.title("Unconversion Rate by Phage Control: " + str(round(np.average(unconverted) * 100, 2)) + '%', fontsize=14)
	plt.xlabel("mCH/CH", fontsize=14)
	plt.ylabel("Frequency ", fontsize=14)
	plt.savefig('Unconversion_Rate.png')

def qc(file):

	qc_p = open(file)
	all_mapped_passed = int(qc_p.readline().strip()) 
        qc = []

        while True:
		tmp = qc_p.readline()
                if len(tmp) == 0:
			break
                qc.append(float(tmp.strip()) / all_mapped_passed)

        qc = np.array(qc)
        plt.plot(qc)
        plt.title("Mismatches Distribution per Read", fontsize=14)
        plt.xlabel("Single BP Position", fontsize=14)
        plt.ylabel("Average Freuency per Read ", fontsize=14)
        plt.savefig('QC_Plot')


def main():

	parser = OptionParser()
    	parser.add_option('-n', action="store", dest="nbin", type="int", help="Bin size for metagene plot", default = 80)
    	parser.add_option('-m', action="store", dest ='met', help="Single-based-resolution methylation level file (CG format)")
        parser.add_option('-a', action="store", dest ='annotation', help ="Gene annotation file", default="None")
    	parser.add_option('-r', action="store", dest ="genome_region", help="Genomeic region to be plotted", choices=['transposon', 'gene',], default="gene")
        parser.add_option('-u', action="store", dest ="isunconversion", help="Plot Unconverstion Graph", choices=['y', 'n'], default="n")
        parser.add_option('-q', action="store", dest ="qc_f", help="Plot Quality Control Graph, supply qc file", default= '')
	parser.add_option('--meta', action="store", dest ="meta", help="Plot metagene file",choices=['y', ''],default= '')
	options, args = parser.parse_args()	

	

	if options.isunconversion == 'y':
                if 'gz' == options.met[len(options.met) - 2 : len(options.met)]:
			subprocess.call('gunzip -k ' + options.met, shell=True)
		unconversion(options.met[0:len(options.met) -3])
    
        if options.qc_f != '':
                qc(options.qc_f)

        if options.meta != '':
            
		if 'gz' == options.met[len(options.met) - 2 : len(options.met)]:
                        subprocess.call('gunzip -k ' + options.met, shell=True)
                options.met = options.met[0:len(options.met) -3]
                
	        if options.annotation == 'None':
        	        test = Species(options.met, None, False, False)
	        else:
		        if options.genome_region == 'gene':
		                test = Species(options.met, options.annotation, False, True)
	        test.calculate_mlevel(options.nbin)
		
if __name__ == '__main__':
	main()



