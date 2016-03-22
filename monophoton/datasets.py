import re
import os
import math

class SampleDef(object):
    def __init__(self, name, title = '', book = '', directory = '', crosssection = 0., scale = 1., nevents = 0, sumw = 0., lumi = 0., data = False, signal = False, comments = '', custom = {}):
        self.name = name
        self.title = title
        self.book = book
        self.directory = directory
        self.crosssection = crosssection
        self.scale = scale
        self.nevents = nevents
        if sumw == 0.:
            self.sumw = float(nevents)
        else:
            self.sumw = sumw
        self.lumi = lumi
        self.data = data
        self.signal = signal
        self.comments = comments
        self.custom = custom

    def clone(self):
        return SampleDef(self.name, title = self.title, book = self.book, directory = self.directory, crosssection = self.crosssection, scale = self.scale, nevents = self.nevents, sumw = self.sumw, lumi = self.lumi, data = self.data, signal = self.signal, comments = self.comments, custom = dict(self.custom.items()))

    def dump(self):
        print 'name =', self.name
        print 'title =', self.title
        print 'book =', self.book
        print 'directory =', self.directory
        print 'crosssection =', self.crosssection
        print 'scale =', self.scale
        print 'nevents =', self.nevents
        print 'sumw =', self.sumw
        print 'lumi =', self.lumi
        print 'data =', self.data
        print 'comments = "' + self.comments + '"'
        print 'signal =', self.signal

    def linedump(self):
        title = '"%s"' % self.title

        if self.data:
            xsec = self.lumi
            ndec = 1
            sumwstr = '-'
        else:
            xsec = self.crosssection
            ndec = 0
            while xsec < math.pow(10., 3 - ndec):
                ndec += 1

            if int(self.sumw) == self.nevents:
                sumwstr = '%.1f' % self.sumw
            else:
                sumwstr = '%.11e' % self.sumw

        if self.signal:
            xsec *= -1.

        if ndec >= 6:
            xsecstr = '%.{ndec}e'.format(ndec = 3) % xsec
        else:
            xsecstr = '%.{ndec}f'.format(ndec = ndec) % xsec

        if self.scale != 1.:
            xsecstr += 'x%.1e' % self.scale

        if self.comments != '':
            self.comments = "# "+self.comments
            
        print '%-16s %-35s %-20s %-10d %-20s %-10s %s %s' % (self.name, title, xsecstr, self.nevents, sumwstr, self.book, self.directory, self.comments)


class SampleDefList(object):
    def __init__(self, samples = []):
        self.samples = samples

    def __iter__(self):
        return iter(self.samples)

    def __reversed__(self):
        return reversed(self.samples)

    def __getitem__(self, key):
        try:
            return self.get(key)
        except RuntimeError:
            raise KeyError(key + ' not defined')

    def names(self):
        return [s.name for s in self.samples]

    def get(self, name):
        try:
            return next(s for s in self.samples if s.name == name)
        except StopIteration:
            raise RuntimeError('Sample ' + name + ' not found')

allsamples = SampleDefList()

with open(os.path.dirname(os.path.realpath(__file__)) + '/data/datasets.csv') as dsSource:
    for line in dsSource:
        line = line.strip()

        if line.startswith('#'):
            continue

        matches = re.match('([^ ]+)\s+"(.*)"\s+([0-9e.x+-]+)\s+([0-9]+)\s+([0-9e.+-]+)\s+([^ ]+)\s+([^ ]+)(| +#.*)', line.strip())
        if not matches:
            print 'Ill-formed line in datasets.csv'
            print line
            continue

        name, title, xsec, nevents, sumw, book, directory, comments = [matches.group(i) for i in range(1, 9)]

        if sumw == '-':
            sdef = SampleDef(name, title = title, book = book, directory = directory, lumi = float(xsec), nevents = int(nevents), data = True, comments = comments.lstrip(' #'))
        else:
            if 'x' in xsec:
                (xsec, scale) = xsec.split('x')
                xsec = float(xsec) # * float(scale)
                scale = float(scale)
            else:
                xsec = float(xsec)
                scale = 1.

            if xsec < 0.:
                signal = True
                xsec = -xsec
            else:
                signal = False

            # print signal, xsec, scale

            sdef = SampleDef(name, title = title, book = book, directory = directory, crosssection = xsec, scale = scale, nevents = int(nevents), sumw = float(sumw), signal = signal, comments = comments.lstrip(' #'))

        allsamples.samples.append(sdef)

if __name__ == '__main__':
    import sys
    import os
    from argparse import ArgumentParser

    argParser = ArgumentParser(description = 'Dataset information management')
    argParser.add_argument('--list', '-L', action = 'store_true', dest = 'list', help = 'List datasets with nevents > 0')
    argParser.add_argument('--all', '-A', action = 'store_true', dest = 'all', help = '(With --list) Show all datasets.')
    argParser.add_argument('--print', '-p', metavar = 'DATASET', dest = 'showInfo', help = 'Print information of DATASET.')
    argParser.add_argument('--recalculate', '-r', metavar = 'DATASET', dest = 'recalculate', help = 'Recalculate nentries and sumw for DATASET.')
    argParser.add_argument('--source-dir', '-d', metavar = 'DIR', dest = 'sourceDir', help = 'Source directory where simpletree files are.')

    args = argParser.parse_args()
    sys.argv = []

    if args.list:
        if args.all:
            print ' '.join([sample.name for sample in allsamples])
        else:
            print ' '.join([sample.name for sample in allsamples if sample.nevents > 0.])

        sys.exit(0)

    if args.showInfo:
        try:
            allsamples[args.showInfo].dump()
        except:
            print 'No sample', args.showInfo
        
        sys.exit(0)

    if args.recalculate:
        name = args.recalculate

        import ROOT
        if args.sourceDir:
            sourceDir = args.sourceDir
        else:
            print 'Source dir?'
            sourceDir = sys.stdin.readline().strip()

        try:
            sample = allsamples[name]
            fNames = [f for f in os.listdir(sourceDir + '/' + sample.book + '/' + sample.directory) if f.startswith('simpletree_')]

            counter = None
            for fName in fNames:
                source = ROOT.TFile.Open(sourceDir + '/' + sample.book + '/' + sample.directory + '/' + fName)
                if counter is None:
                    counter = source.Get('counter')
                    counter.SetDirectory(ROOT.gROOT)
                else:
                    counter.Add(source.Get('counter'))
                source.Close()

            sample.nevents = int(counter.GetBinContent(1))
            if not sample.data:
                sample.sumw = counter.GetBinContent(2)

            sample.linedump()
    
        except:
            sys.stderr.write(name + '  NAN\n')

        sys.exit(0)
