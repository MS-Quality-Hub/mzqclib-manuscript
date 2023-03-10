## Build notes
Needs [ANN-SoLo](https://github.com/bittremieux/ANN-SoLo) checkout into ann-solo-git (worked at 71557eb)
to 'fix' pip requirements list in setup.py from "faiss" to "faiss-cpu" or "faiss-gpu" and then pip install from source (in the container build)
Otherwise pip will fail to recognise faiss has been installed or unable to install if missing, e.g.
```
ERROR: Could not find a version that satisfies the requirement faiss (from ann-solo) (from versions: none)
ERROR: No matching distribution found for faiss
FATAL:   While performing build: while running engine: exit status 1
```
This must be some changes in pip as it was working before.
