## mzqc_heatmap_draft ipynb 
The notebook would be part of the supplementary material, I suppose.
It is of course difficult to write a Results and Discussion section with its sole focus on the QC as we (and everyone else) are used to only very brief descriptions of QC analyses if any in publications.
This notebook's purpose is to explore which results of a specific input data to highlight in the manuscript (which is a technical demonstration of the mzQC libraries, not a reanalysis study).

### Argument chain
1. Sanity check: no technical bias between group's measurements - PCA
2. One potential outlier: heatmap to show the QC metric values in relation to each other
3. We see some clustering (very vague), but if so, the 'outlier' clusters with the other group
4. We investigate further by adding context scaling to the metric values and find more outlier evidence in the identification. We also consider run order influences at first, too.
5. Identification related metric point further towards outlier
