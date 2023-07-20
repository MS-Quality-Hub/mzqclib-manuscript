## Build notes
Needs [ANN-SoLo](https://github.com/bittremieux/ANN-SoLo) submodule checkout into ann-solo-git before container build. Repo at commit 71557eb worked. The setup.py needs to be patched to 'fix' pip requirements list in setup.py from "faiss" to "faiss-cpu" or "faiss-gpu" and then pip install from source (in the container build)
Otherwise pip will fail to recognise faiss has been installed or unable to install if missing, e.g.
```
ERROR: Could not find a version that satisfies the requirement faiss (from ann-solo) (from versions: none)
ERROR: No matching distribution found for faiss
FATAL:   While performing build: while running engine: exit status 1
```
This must be due to some changes in pip as it was working before.
A 'patched' `setup.py` can be found in `container/pymzqc-usecase/local-ann-patch/setup.py`. Check out a local ANN-solo from _main_ into `ann-solo-git` and copy that `setup.py` to `ann-solo-git/src/setup.py` befor `singularity build`.
