## Create a workflowchart from nextflow
To produce a mermaid file for 'pretty' workflow visualisation from the workflow, use
```
nextflow run 'mzqc-usecases.nf'  -with-dag flowchart.mmd --run test.raw -stub
```
## Current capability:
```mermaid
flowchart TD
    p0([Channel.fromPath])
    p1[rawfileconversion]
    p2[jmzqc]
    p3[rmzqc]
    p4[pymzqc]
    p5[Report or Archival]
    p0 -->|run_channel| p1
    p1 -->|mzml_channel| p2
    p1 -->|mzml_channel| p3
    p2 -->|mzqc_channel| p4
    p3 -->|mzqc_channel| p4
    p4 -->|mzqc_channel| p5    
```

## Originally planned:
```mermaid
flowchart TD
    p0([Channel.fromPath])
    p1[rawfileconversion]
    p2[jmzqc]
    p3[rmzqc]
    p4[pymzqc]
    p5[Report or Archival]
    p0 -->|run_channel| p1
    p1 -->|mzml_channel| p2
    p1 -->|mzml_channel| p3
    p1 -->|mzml_channel| p4
    p2 -->|mzqc_channel| p5
    p3 -->|mzqc_channel| p5
    p4 -->|mzqc_channel| p5    
```
