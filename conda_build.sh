#!/bin/bash

# Determine the output filename
outfile=$(conda build conda.recipe/ --output)

# OK, now build (-b: don't upload or test)
conda build -b conda.recipe/

# Convert to other platforms
mkdir -p dist/conda/
conda convert --platform all $outfile -o dist/conda/


for i in $( ls dist/conda/ ); do
    echo item: $i
done
