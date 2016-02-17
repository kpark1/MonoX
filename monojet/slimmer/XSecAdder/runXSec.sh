#! /bin/bash

folder=/afs/cern.ch/work/d/dabercro/public/Winter15/Correct_w_MJ/merged/

root -q -l -b xsecWeights.cc+\(\"$folder\"\)                      # This is to just make sure the macro is compiled

cat xsecArgs.txt | xargs -n2 -P6 ./xsecRunner.sh $folder
