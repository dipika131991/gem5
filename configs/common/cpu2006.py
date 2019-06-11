# Copyright (c) 2006-2008 The Regents of The University of Michigan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Nathan Binkert

import os
import sys
from os.path import basename, exists, join as joinpath, normpath
from os.path import isdir, isfile, islink

spec_dist = os.environ.get('M5_CPU2006', '/home/dipika/binaries/cpu2006')

def copyfiles(srcdir, dstdir):
    from filecmp import cmp as filecmp
    from shutil import copyfile

    srcdir = normpath(srcdir)
    dstdir = normpath(dstdir)

    if not isdir(dstdir):
        os.mkdir(dstdir)

    for root, dirs, files in os.walk(srcdir):
        root = normpath(root)
        prefix = os.path.commonprefix([root, srcdir])

        root = root[len(prefix):]
        if root.startswith('/'):
            root = root[1:]

        for entry in dirs:
            newdir = joinpath(dstdir, root, entry)
            if not isdir(newdir):
                os.mkdir(newdir)

        for entry in files:
            dest = normpath(joinpath(dstdir, root, entry))
            src = normpath(joinpath(srcdir, root, entry))
            if not isfile(dest) or not filecmp(src, dest):
                copyfile(src, dest)

    # some of the spec benchmarks expect to be run from one directory up.
    # just create some symlinks that solve the problem
    inlink = joinpath(dstdir, 'input')
    outlink = joinpath(dstdir, 'output')
    if not exists(inlink):
        os.symlink('.', inlink)
    if not exists(outlink):
        os.symlink('.', outlink)

class Benchmark(object):
    def __init__(self, isa, os, input_set):
        if not hasattr(self.__class__, 'name'):
            self.name = self.__class__.__name__

        if not hasattr(self.__class__, 'binary'):
            self.binary = self.name

        if not hasattr(self.__class__, 'args'):
            self.args = []

        if not hasattr(self.__class__, 'output'):
            self.output = '%s.out' % self.name

        if not hasattr(self.__class__, 'simpoint'):
            self.simpoint = None

        try:
            func = getattr(self.__class__, input_set)
        except AttributeError:
            raise AttributeError, \
                  'The benchmark %s does not have the %s input set' % \
                  (self.name, input_set)

        executable = joinpath(spec_dist, 'binaries', self.binary)
	print "executable= %s " % (executable)

        if not isfile(executable):
            raise AttributeError, '%s not found' % executable
        self.executable = executable
        # root of tree for input & output data files
        data_dir = joinpath(spec_dist, 'data',self.name)
        # optional subtree with files shared across input sets
        all_dir = joinpath(data_dir, 'all')
        # dirs for input & output files for this input set
        inputs_dir = joinpath(data_dir, input_set, 'input')
        #inputs_dir = joinpath(data_dir )
        outputs_dir = joinpath(data_dir, input_set, 'output')
        # keep around which input set was specified
        self.input_set = input_set
	print "inputs_dir = %s " % (inputs_dir)
	print "outputs_dir = %s " % (outputs_dir)
        if not isdir(inputs_dir):
            raise AttributeError, '%s not found' % inputs_dir

        self.inputs_dir = [ inputs_dir ]
        if isdir(all_dir):
            self.inputs_dir += [ joinpath(all_dir, 'input') ]
        if isdir(outputs_dir):
            self.outputs_dir = outputs_dir

        if not hasattr(self.__class__, 'stdin'):
            self.stdin = joinpath(inputs_dir, '%s.in' % self.name)
            if not isfile(self.stdin):
                self.stdin = None

        if not hasattr(self.__class__, 'stdout'):
            self.stdout = joinpath(outputs_dir, '%s.out' % self.name)
            if not isfile(self.stdout):
                self.stdout = None

        func(self, isa, os)

    def makeLiveProcessArgs(self, **kwargs):
        # set up default args for LiveProcess object
        process_args = {}
        process_args['cmd'] = [ self.name ] + self.args
        process_args['executable'] = self.executable
        if self.stdin:
            process_args['input'] = self.stdin
        if self.stdout:
            process_args['output'] = self.stdout
        if self.simpoint:
            process_args['simpoint'] = self.simpoint
        # explicit keywords override defaults
        process_args.update(kwargs)

        return process_args

    def makeLiveProcess(self, **kwargs):
        process_args = self.makeLiveProcessArgs(**kwargs)

        # figure out working directory: use m5's outdir unless
        # overridden by LiveProcess's cwd param
        cwd = process_args.get('cwd')
        if not cwd:
            from m5 import options
            cwd = options.outdir
            process_args['cwd'] = cwd
        if not isdir(cwd):
            os.makedirs(cwd)
        # copy input files to working directory
#	cwd = '/home/biswa/gem5-tournament'
    	#cwd = '/home/dipika/binaries/cpu2006/data/sphinx/all/input/'
        #cwd = '/home/biswa/m5-waysharing/input/'
	#print "cwd = %s " % (cwd)
        #for d in self.inputs_dir:
	#    copyfiles(d, cwd)
        # generate LiveProcess object
        from m5.objects import LiveProcess
        return LiveProcess(**process_args)

    def __str__(self):
        return self.name

class DefaultBenchmark(Benchmark):
    def ref(self, isa, os): pass
    def test(self, isa, os): pass
    def train(self, isa, os): pass
    def all(self, isa, os): pass

class MinneDefaultBenchmark(DefaultBenchmark):
    def smred(self, isa, os): pass
    def mdred(self, isa, os): pass
    def lgred(self, isa, os): pass

class namd(DefaultBenchmark):
    name = 'namd'
    lang = 'C++'

    def all(self, isa, os):
        #self.args = ['--input','working_dir/namd.input',
        self.args = ['--input','/home/dipika/binaries/cpu2006/data/namd/all/input/namd.input',
                     '--iterations', '38',
                     '--output','namd.out']
    def ref(self, isa, os):
        self.args = ['--input','/home/dipika/binaries/cpu2006/data/namd/all/input/namd.input',
                     '--iterations', '38',
                     '--output','namd.out']

class milc(DefaultBenchmark):
    name = 'milc'
    lang = 'C'
    def ref(self, isa, os):
        self.stdin = '/home/dipika/binaries/cpu2006/data/milc/ref/input/su3imp.in'
   

class omnetpp(DefaultBenchmark):
     name = 'omnetpp'
     lang = 'C++'
     def all(self, isa, os):
         self.args =  ['/home/dipika/binaries/cpu2006/data/omnetpp/ref/input/omnetpp.ini',
                     '/home/dipika/binaries/cpu2006/data/omnetpp/ref/output/omnetpp.log']

class cactusADM(DefaultBenchmark):
    name = 'cactusADM'
    number = 436 
    lang = 'C++'

    def ref(self, isa, os):
        self.args = ['/home/dipika/binaries/cpu2006/data/cactusADM/ref/input/benchADM.par']
	self.output = 'benchADM.out'


class soplex(DefaultBenchmark):
    name = 'soplex'
    lang = 'C++'

    def test(self, isa, os):
        self.args = ['-m10000','/home/dipika/binaries/cpu2006/data/soplex/test/input/test.mps']
        self.output = 'test.out'  

    def ref(self, isa, os):
        self.args = ['-m3500','/home/dipika/binaries/cpu2006/data/soplex/ref/input/ref.mps']
        self.output = 'ref.out'  

    def train(self, isa, os):
        self.args = ['-m1200','/home/dipika/binaries/cpu2006/data/soplex/train/input/train.mps']
        self.output = 'train.out'  

class gamess(DefaultBenchmark):
    name = 'gamess'
    number = 416 
    lang = 'F95'

    def ref(self, isa, os):
     	self.stdin = '/home/dipika/binaries/cpu2006/data/gamess/ref/input/cytosine.2.config'

class bzip2(DefaultBenchmark):
    name = 'bzip2'
    number = 256
    lang = 'C'
    def all(self, isa, os):
        self.args = ['/home/dipika/binaries/cpu2006/data/bzip2/all/input/input.program', '1']

    def test(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/bzip2/test/input/dryer.jpg ','2']

    def train(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/bzip2/train/input/byoudoin.jpg','5' ]
    
    def ref(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/bzip2/ref/input/input.source','280' ]

class bzip2_source(bzip2):
    def ref(self, isa, os):
        self.simpoint = 977*100E6
        self.args = [ 'input.source', '58' ]

    def lgred(self, isa, os):
        self.args = [ 'input.source', '1' ]

class bzip2_graphic(bzip2):
    def ref(self, isa, os):
        self.simpoint = 718*100E6
        self.args = [ 'input.graphic', '58' ]

    def lgred(self, isa, os):
        self.args = [ 'input.graphic', '1' ]

class bzip2_program(bzip2):
    def ref(self, isa, os):
        self.simpoint = 458*100E6
        self.args = [ '/home/dipika/binaries/cpu2006/data/bzip2/all/input/input.program', '280' ]

    def lgred(self, isa, os):
        self.args = [ 'input.program', '1' ]

class gcc(DefaultBenchmark):
    name = 'gcc'
    number = 176
    lang = 'C'
    
    def ref(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/gcc/ref/input/scilab.i', '-o', '/home/dipika/binaries/cpu2006/data/gcc/test/input/scilab.s' ]

    def test(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/gcc/test/input/cccp.i', '-o', '/home/dipika/binaries/cpu2006/data/gcc/test/input/cccp.s' ]

    def train(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/gcc/train/input/integrate.i', '-o', '/home/dipika/binaries/cpu2006/data/gcc/train/input/integrate.s' ]

    def smred(self, isa, os):
        self.args = [ 'c-iterate.i', '-o', 'c-iterate.s' ]

    def mdred(self, isa, os):
        self.args = [ 'rdlanal.i', '-o', 'rdlanal.s' ]

    def lgred(self, isa, os):
        self.args = [ 'cp-decl.i', '-o', 'cp-decl.s' ]

class gcc_166(gcc):
    def ref(self, isa, os):
        self.simpoint = 389*100E6
        self.args = [ '166.i', '-o', '166.s' ]

class gcc_200(gcc):
    def ref(self, isa, os):
        self.simpoint = 736*100E6
        self.args = [ '200.i', '-o', '200.s' ]

class gcc_expr(gcc):
    def ref(self, isa, os):
        self.simpoint = 36*100E6
        self.args = [ 'expr.i', '-o', 'expr.s' ]

class gcc_integrate(gcc):
    def ref(self, isa, os):
        self.simpoint = 4*100E6
        self.args = [ 'integrate.i', '-o', 'integrate.s' ]

class gcc_scilab(gcc):
    def ref(self, isa, os):
        self.simpoint = 207*100E6
        self.args = [ 'scilab.i', '-o', 'scilab.s' ]

class zeusmp(DefaultBenchmark):
    name = 'zeusmp'
    number = 434
    lang = 'F'
    
    def ref(self, isa, os):
	#self.cwd = '/home/dipika/binaries/cpu2006/data/zeusmp/ref/input/'
    	self.args = [ '/home/dipika/binaries/cpu2006/data/zeusmp/ref/input/zmp_inp' ]

#class mcf(MinneDefaultBenchmark):
class mcf(DefaultBenchmark):
    name = 'mcf'
    number = 181
    lang = 'C'

    def test(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/mcf/test/input/inp.in' ]

    def ref(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/mcf/ref/input/inp.in' ]

    def train(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/mcf/train/input/inp.in' ]

class leslie3d(DefaultBenchmark):
    name = 'leslie3d'
    number = 437
    lang = 'F'
    def ref(self, isa, os):
        self.stdin = '/home/dipika/binaries/cpu2006/data/leslie3d/ref/input/leslie3d.in'

class hmmer(DefaultBenchmark):
    name = 'hmmer'
    lang = 'C'

    def test(self, isa, os):
	 self.args = ['--fixed', '0', 
		      '--mean', '325',
		      '--num', '5000',
		      '--sd', '200',
		      '--seed', '0',
		      '/home/dipika/binaries/cpu2006/data/hmmer/test/input/bombesin.hmm' ]
    	 self.output = 'bombesin.out'

    def ref(self, isa, os):
	 self.args = ['--fixed', '0', 
		      '--mean', '500',
		      '--num', '500000',
		      '--sd', '350',
		      '--seed', '0',
		      '/home/dipika/binaries/cpu2006/data/hmmer/ref/input/retro.hmm' ]
    	 self.output = 'retro.out'

    def train(self, isa, os):
	 self.args = ['--fixed', '0', 
		      '--mean', '425',
		      '--num', '85000',
		      '--sd', '300',
		      '--seed', '0',
		      '/home/dipika/binaries/cpu2006/data/hmmer/train/input/leng100.hmm' ]
    	 self.output = 'leng100.out'



class sjeng(DefaultBenchmark):
    name = 'sjeng'
    lang = 'C'
    
    def test(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/sjeng/test/input/test.txt']

    def train(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/sjeng/train/input/train.txt']

    def ref(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/sjeng/ref/input/ref.txt']

class GemsFDTD(DefaultBenchmark):
    name = 'GemsFDTD'
    number = '459'
    lang = 'F'

    def test(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/GemsFDTD/test/input/test.in']

    def ref(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/GemsFDTD/ref/input/ref.in']
    
    def train(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/GemsFDTD/train/input/train.in']

class h264ref(DefaultBenchmark):
    name = 'h264ref'
    number = '464'
    lang = 'C'

    def ref(self, isa, os):
        self.args = [ '-d','/home/dipika/binaries/cpu2006/data/h264ref/ref/input/foreman_ref_encoder_baseline.cfg']
        h264ref.output = 'foreman_test_encoder_baseline.out'
    
    def test(self, isa, os):
        self.args = [ '-d','/home/dipika/binaries/cpu2006/data/h264ref/test/input/foreman_test_encoder_baseline.cfg']
        h264ref.output = 'foreman_test_encoder_baseline.out'

class xalancbmk(DefaultBenchmark):
    name = 'xalancbmk'
    number = 181
    lang = 'C'

    def test(self, isa, os):
    	self.args = [ '/home/dipika/binaries/cpu2006/data/xalancbmk/test/input/test.xml' ]
    def ref(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/xalancbmk/ref/input/t5.xml','/home/dipika/binaries/cpu2006/data/xalancbmk/ref/input/xalanc.xsl']

class bwaves(DefaultBenchmark):
    name = 'bwaves'
    number = 410
    lang = 'C'

    def ref(self, isa, os):
        self.args = [ '/home/dipika/binaries/cpu2006/data/bwaves/ref/input/bwaves.in' ]



class libquantum(DefaultBenchmark):
    name = 'libquantum'
    lang = 'C'

    def test(self, isa, os):
	 self.args = ['33','5']

    def train(self, isa, os):
	 self.args = ['143','25']
    
    def ref(self, isa, os):
	 self.args = ['1397','8']

class lbm(DefaultBenchmark):
    name  = 'lbm'
    lang = 'C'
    
    def test(self, isa, os):
         self.args = ['20', 'reference.dat', '0', '1' , '/home/dipika/binaries/cpu2006/data/lbm/test/input/100_100_130_cf_a.of']

    def train(self, isa, os):
         self.args = ['300', 'reference.dat', '0', '1' , '/home/dipika/binaries/cpu2006/data/lbm/train/input/100_100_130_cf_b.of']

    def ref(self, isa, os):
         self.args = ['3000', 'reference.dat', '0', '0' , '/home/dipika/binaries/cpu2006/data/lbm/ref/input/100_100_130_ldc.of']

class calculix(DefaultBenchmark):
    name = 'calculix'
    lang = 'C'

    def test(self, isa, os):
         self.args =  ['-i','/home/dipika/binaries/cpu2006/data/calculix/test/input/beampic']
    def train(self, isa, os):
         self.args =  ['-i','/home/dipika/binaries/cpu2006/data/calculix/train/input/stairs']
    def ref(self, isa, os):
         self.args =  ['-i','/home/dipika/binaries/cpu2006/data/calculix/ref/input/hyperviscoplastic']

class gromacs(DefaultBenchmark):
    name = 'gromacs'
    number = '435'
    lang = 'C'

    def test(self, isa, os):
        self.args = [ '-silent','-deffnm','/home/dipika/binaries/cpu2006/data/gromacs/test/input/gromacs.tpr','-nice','2']
    def train(self, isa, os):
        self.args = [ '-silent','-deffnm','/home/dipika/binaries/cpu2006/data/gromacs/train/input/gromacs.tpr','-nice','0']
    def ref(self, isa, os):
        self.args = [ '-silent','-deffnm','/home/dipika/binaries/cpu2006/data/gromacs/ref/input/gromacs.tpr','-nice','0']

class gobmk(DefaultBenchmark):
    name = 'gobmk'
    number = '445'
    lang = 'C'

    def ref(self, isa, os):
    	self.args = ['--quiet','--mode','gtp']
        self.stdin = '/home/dipika/binaries/cpu2006/data/gobmk/ref/input/13x13.tst'
    #input = '/home/dipika/binaries/cpu2006_exe/445.gobmk/data/test/input/capture.tst'
    #output = '/home/dipika/binaries/cpu2006_exe/445.gobmk/data/test/output/capture.out' 
#sphinx3=LiveProcess()
#sphinx3.executable =  binary_dir+'482.sphinx_livepretend_base.alpha-gcc'
#sphinx3.cmd = [sphinx3.executable]+['ctlfile', '.', 'args.an4']
#sphinx3.output = 'an4.out'

class sphinx(DefaultBenchmark):
    name = 'sphinx'
    number = '482'
    lang = 'C'

    def ref(self, isa, os):
        self.args = ['/home/dipika/binaries/cpu2006/data/sphinx/all/input/model/lm/an4/an4.ctl', '/home/dipika/binaries/cpu2006/data/sphinx/all/input/model/lm/an4', '/home/dipika/binaries/cpu2006/data/sphinx/ref/input/args.an4']
        self.output = 'an4.out'
       # self.args = [input1, input_dir, input2]       

class dealII(DefaultBenchmark):
     name = 'dealII'
     number = '447'
     lang = 'C++'
     def ref(self, isa, os):
         self.args=['23']

class perlbench(DefaultBenchmark):
     name = 'perlbench' 
     number = '400' 
     lang = 'C'
     
     def ref(self, isa, os):
	 self.args=['-I','/home/dipika/binaries/cpu2006/data/perlbench/all/input/lib','/home/dipika/binaries/cpu2006/data/perlbench/ref/input/checkspam.pl','2500','5','25','11','150','1','1' ,'1' ,'1']

class povray(DefaultBenchmark):
     name = 'povray'
     number = '453'
     lang = 'C++'
     def ref(self, isa, os):
	 self.args=['/home/dipika/binaries/cpu2006/data/povray/ref/input/SPEC-benchmark-ref.ini']

class astar(DefaultBenchmark):
     name = 'astar'
     number = '473'
     lang = 'C++'
   
     def ref(self, isa, os):
	  self.args=['/home/dipika/binaries/cpu2006/data/astar/ref/input/BigLakes2048.cfg']

class specrand(DefaultBenchmark):
      name = 'specrand'
      number = '999'
      lang = 'C'
     
      def ref(self, isa, os):
            self.args=['1255432124','234923']
  
all = [ bzip2,bzip2_source, bzip2_graphic, bzip2_program, gcc_166, gcc_200,povray,specrand, 
	gcc_expr, gcc_integrate, gcc_scilab, namd, soplex, mcf ,leslie3d, hmmer, sjeng,perlbench,astar,
	dealII,gromacs,zeusmp,cactusADM,GemsFDTD, libquantum, milc, lbm, bwaves, h264ref,calculix ,gobmk, gamess,sphinx,xalancbmk,omnetpp]

__all__ = [ x.__name__ for x in all ]

if __name__ == '__main__':
    from pprint import pprint
    for bench in all:
        for input_set in 'ref', 'test', 'train':
            print 'class: %s' % bench.__name__
            x = bench('x86', 'tru64', input_set)
            print '%s: %s' % (x, input_set)
            pprint(x.makeLiveProcessArgs())
            print
