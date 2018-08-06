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

spec_dist = os.environ.get('M5_CPU2006', '/home/abhijit/Research/gem5/binaries/cpu2006')

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
        self.args = ['--input','/home/abhijit/Research/gem5/binaries/cpu2006/data/namd/all/input/namd.input',
                     '--iterations', '38',
                     '--output','namd.out']
    def ref(self, isa, os):
        self.args = ['--input','/home/abhijit/Research/gem5/binaries/cpu2006/data/namd/all/input/namd.input',
                     '--iterations', '38',
                     '--output','namd.out']


class leslie3d(DefaultBenchmark):
    name = 'leslie3d'
    number = 437
    lang = 'F'
    def ref(self, isa, os):
        self.stdin = '/home/abhijit/Research/gem5/binaries/cpu2006/data/leslie3d/ref/input/leslie3d.in'


class bzip2(DefaultBenchmark):
    name = 'bzip2'
    number = 256
    lang = 'C'
    def all(self, isa, os):
        self.args = ['/home/abhijit/Research/gem5/binaries/cpu2006/data/bzip2/all/input/input.program', '1']

    def test(self, isa, os):
        self.args = [ '/home/abhijit/Research/gem5/binaries/cpu2006/data/bzip2/test/input/dryer.jpg ','2']

    def train(self, isa, os):
        self.args = [ '/home/abhijit/Research/gem5/binaries/cpu2006/data/bzip2/train/input/byoudoin.jpg','5' ]
    
    def ref(self, isa, os):
        self.args = [ '/home/abhijit/Research/gem5/binaries/cpu2006/data/bzip2/ref/input/input.source','280' ]


class lbm(DefaultBenchmark):
    name  = 'lbm'
    lang = 'C'
    
    def test(self, isa, os):
         self.args = ['20', 'reference.dat', '0', '1' , '/home/abhijit/Research/gem5/binaries/cpu2006/data/lbm/test/input/100_100_130_cf_a.of']

    def train(self, isa, os):
         self.args = ['300', 'reference.dat', '0', '1' , '/home/abhijit/Research/gem5/binaries/cpu2006/data/lbm/train/input/100_100_130_cf_b.of']

    def ref(self, isa, os):
         self.args = ['3000', 'reference.dat', '0', '0' , '/home/abhijit/Research/gem5/binaries/cpu2006/data/lbm/ref/input/100_100_130_ldc.of']

  
all = [namd, leslie3d, bzip2, lbm]

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